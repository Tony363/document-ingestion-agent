"""
Worker signals for task recovery and monitoring
"""

import redis
import json
import logging
from datetime import datetime, timedelta
from celery import signals
from celery.result import AsyncResult
from .celery_app import celery_app

logger = logging.getLogger(__name__)

@signals.worker_ready.connect
def recover_pending_tasks(sender, **kwargs):
    """
    Recover PENDING tasks when worker starts.
    This handles cases where tasks were queued but never processed.
    """
    logger.info("Worker starting - checking for stuck tasks...")
    
    try:
        # Import settings to get Redis configuration
        from .config import settings
        
        # Connect to Redis using configuration
        r = redis.Redis(
            host=settings.redis_host, 
            port=settings.redis_port, 
            db=0, 
            decode_responses=True
        )
        
        # Get all document keys
        doc_keys = r.keys("doc:*")
        recovered_count = 0
        
        for doc_key in doc_keys:
            try:
                # Get document metadata
                metadata_str = r.get(doc_key)
                if not metadata_str:
                    continue
                    
                metadata = json.loads(metadata_str)
                celery_task_id = metadata.get('celery_task_id')
                
                if not celery_task_id:
                    continue
                
                # Check task status
                result = AsyncResult(celery_task_id, app=celery_app)
                
                # If task is PENDING and document was uploaded more than 5 minutes ago
                if result.status == 'PENDING':
                    uploaded_at_str = metadata.get('uploaded_at', '')
                    if uploaded_at_str:
                        uploaded_at = datetime.fromisoformat(uploaded_at_str.replace('Z', '+00:00'))
                        time_since_upload = datetime.utcnow() - uploaded_at.replace(tzinfo=None)
                        
                        # Only recover tasks older than 5 minutes
                        if time_since_upload > timedelta(minutes=5):
                            document_id = metadata.get('document_id')
                            logger.warning(f"Found stuck task for document {document_id}, requeuing...")
                            
                            # Prepare document data
                            document_data = {
                                "file_path": f"{document_id}.pdf",
                                "mime_type": metadata.get("mime_type", "application/pdf"),
                                "file_size": metadata.get("file_size", 0),
                                "content_hash": metadata.get("content_hash", "")
                            }
                            
                            # Prepare context
                            context_data = {
                                "job_id": metadata.get("job_id"),
                                "document_id": document_id,
                                "metadata": {
                                    "file_name": metadata.get("file_name"),
                                    "upload_time": metadata.get("uploaded_at")
                                }
                            }
                            
                            # Queue new task
                            from .tasks import process_document_task
                            new_task = process_document_task.delay(document_data, context_data)
                            
                            # Update metadata with new task ID
                            metadata['celery_task_id'] = new_task.id
                            metadata['status'] = 'processing'
                            metadata['auto_recovered'] = True
                            metadata['recovery_time'] = datetime.utcnow().isoformat()
                            
                            # Save updated metadata
                            r.set(doc_key, json.dumps(metadata))
                            
                            recovered_count += 1
                            logger.info(f"Recovered document {document_id} with new task {new_task.id}")
                            
            except Exception as e:
                logger.error(f"Error checking document {doc_key}: {e}")
                continue
        
        if recovered_count > 0:
            logger.info(f"Recovered {recovered_count} stuck tasks")
        else:
            logger.info("No stuck tasks found")
            
    except Exception as e:
        logger.error(f"Error during task recovery: {e}")

@signals.task_failure.connect
def log_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None, **kw):
    """Log task failures for monitoring"""
    logger.error(f"Task {task_id} failed with exception: {exception}")
    
    # Update document status in Redis
    try:
        if args and len(args) > 1:
            context = args[1]  # Second argument is context
            if isinstance(context, dict):
                document_id = context.get('document_id')
                if document_id:
                    from .config import settings
                    r = redis.Redis(
                        host=settings.redis_host, 
                        port=settings.redis_port, 
                        db=0, 
                        decode_responses=True
                    )
                    doc_key = f'doc:{document_id}'
                    metadata_str = r.get(doc_key)
                    
                    if metadata_str:
                        metadata = json.loads(metadata_str)
                        metadata['status'] = 'failed'
                        metadata['error'] = str(exception)
                        metadata['failed_at'] = datetime.utcnow().isoformat()
                        r.set(doc_key, json.dumps(metadata))
                        logger.info(f"Updated document {document_id} status to failed")
    except Exception as e:
        logger.error(f"Error updating failed task status: {e}")

@signals.task_retry.connect
def log_task_retry(sender=None, task_id=None, reason=None, **kwargs):
    """Log task retries for monitoring"""
    logger.warning(f"Task {task_id} retrying. Reason: {reason}")

@signals.task_success.connect  
def log_task_success(sender=None, result=None, **kwargs):
    """Log successful task completion"""
    if isinstance(result, dict):
        document_id = result.get('document_id')
        if document_id:
            logger.info(f"Task completed successfully for document {document_id}")