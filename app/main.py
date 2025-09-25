"""
Main FastAPI Application

Entry point for the document processing API with endpoints for
document upload, status checking, and webhook management.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import uuid
import hashlib
from pathlib import Path
import shutil
import logging
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import settings
from .tasks import process_document_task, trigger_webhooks_task
from .agents import (
    AgentOrchestrator,
    ClassificationAgent,
    MistralOCRAgent,
    ContentAnalysisAgent,
    SchemaGenerationAgent,
    ValidationAgent
)
from .agents.base_agent import AgentContext
from .agents.agent_orchestrator import DocumentData, PipelineState
from .models.webhook_models import WebhookRegistration, WebhookUpdate, WebhookResponse
from .services.state_manager import get_state_manager
from celery.result import AsyncResult
from .celery_app import celery_app

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute", "1000 per hour"],
    storage_uri=f"redis://{settings.redis_host}:{settings.redis_port}/3"  # Use DB3 for rate limiting
)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiter to app state for access in routes
app.state.limiter = limiter

# Add rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize agent orchestrator
orchestrator = AgentOrchestrator()

# Initialize Redis state manager
state_manager = get_state_manager(
    redis_host=settings.redis_host,
    redis_port=settings.redis_port,
    db=0  # Use database 0 for application state
)

# Legacy storage (kept for backward compatibility, will migrate to Redis)
job_states: Dict[str, PipelineState] = {}
document_metadata: Dict[str, Dict[str, Any]] = {}
webhooks: Dict[str, Dict[str, Any]] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Create upload directory if it doesn't exist
    Path(settings.upload_directory).mkdir(parents=True, exist_ok=True)
    
    # Initialize and register agents
    classification_agent = ClassificationAgent()
    ocr_agent = MistralOCRAgent(
        api_key=settings.mistral_api_key,
        api_url=settings.mistral_api_url,
        rate_limit_delay=settings.mistral_rate_limit_delay
    )
    analysis_agent = ContentAnalysisAgent()
    schema_agent = SchemaGenerationAgent()
    validation_agent = ValidationAgent()
    
    orchestrator.register_agent("classification", classification_agent)
    orchestrator.register_agent("ocr", ocr_agent)
    orchestrator.register_agent("analysis", analysis_agent)
    orchestrator.register_agent("schema", schema_agent)
    orchestrator.register_agent("validation", validation_agent)
    
    logger.info("All agents registered successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down application")
    # Close OCR agent HTTP client
    if "ocr" in orchestrator.agents:
        await orchestrator.agents["ocr"].__aexit__(None, None, None)

# Dependency for API key authentication
async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Verify API key if authentication is enabled"""
    if settings.enable_api_key_auth:
        if not x_api_key or x_api_key not in settings.api_keys:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return True

# Document Processing Endpoints

@app.post(f"{settings.api_prefix}/documents/upload")
@limiter.limit("5 per minute")  # Limit uploads to 5 per minute per IP
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    authorized: bool = Depends(verify_api_key)
):
    """
    Upload a document for processing
    
    Returns:
        job_id: Unique identifier for tracking the processing job
    """
    # Validate file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_extension} not supported"
        )
    
    # Check file size
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {settings.max_upload_size_mb}MB limit"
        )
    
    # Generate unique identifiers
    job_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())
    
    # Calculate content hash for deduplication
    content_hash = hashlib.sha256(content).hexdigest()
    
    # Save file to disk
    file_path = Path(settings.upload_directory) / f"{document_id}{file_extension}"
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create document metadata
    metadata = {
        "job_id": job_id,
        "document_id": document_id,
        "file_name": file.filename,
        "file_size": file_size,
        "file_path": str(file_path),
        "content_hash": content_hash,
        "mime_type": file.content_type,
        "uploaded_at": datetime.utcnow().isoformat(),
        "status": "processing"
    }
    
    # Store in Redis for shared access
    state_manager.set_document_metadata(document_id, metadata)
    
    # Also store in legacy storage for backward compatibility
    document_metadata[document_id] = metadata
    
    # Create agent context
    context = AgentContext(
        job_id=job_id,
        document_id=document_id,
        metadata={
            "file_name": file.filename,
            "upload_time": datetime.utcnow().isoformat()
        }
    )
    
    # Create document data
    document = DocumentData(
        file_path=str(file_path),
        mime_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        content_hash=content_hash
    )
    
    # Queue document processing with Celery
    task = process_document_task.delay(
        document.dict(),
        context.dict()
    )
    
    # Store task ID for tracking
    document_metadata[document_id]["celery_task_id"] = task.id
    metadata["celery_task_id"] = task.id
    state_manager.set_document_metadata(document_id, metadata)
    
    return JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "document_id": document_id,
            "message": "Document uploaded and processing started",
            "status_url": f"{settings.api_prefix}/documents/{document_id}/status"
        }
    )

# Note: The process_document_task function has been moved to app/tasks.py
# and is now a Celery task that will be executed asynchronously by workers

@app.get(f"{settings.api_prefix}/documents/{{document_id}}/status")
async def get_document_status(
    document_id: str,
    authorized: bool = Depends(verify_api_key)
):
    """Get processing status for a document"""
    # Try Redis first, then fallback to in-memory
    metadata = state_manager.get_document_metadata(document_id)
    if not metadata and document_id in document_metadata:
        metadata = document_metadata[document_id]
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Document not found")
    
    job_id = metadata.get("job_id")
    celery_task_id = metadata.get("celery_task_id")
    
    # Get pipeline state from Celery if available
    pipeline_state = None
    status = metadata.get("status", "unknown")
    
    if celery_task_id:
        # Query Celery for task status
        async_result = AsyncResult(celery_task_id, app=celery_app)
        
        # Map Celery states to our status
        status_map = {
            "PENDING": "processing",
            "STARTED": "processing", 
            "RETRY": "processing",
            "SUCCESS": "completed",
            "FAILURE": "failed"
        }
        status = status_map.get(async_result.status, "processing")
        
        # Update metadata status if changed
        if status != metadata.get("status"):
            metadata["status"] = status
            state_manager.set_document_metadata(document_id, metadata)
        
        # Get detailed pipeline state from result
        if async_result.successful() and isinstance(async_result.result, dict):
            result = async_result.result
            pipeline_state = {
                "stage": result.get("stage", "completed"),
                "started_at": result.get("started_at"),
                "updated_at": result.get("completed_at"),
                "completed_at": result.get("completed_at"),
                "error": result.get("error")
            }
            
            # Store result in Redis for schema endpoint
            if job_id:
                state_manager.store_task_result(job_id, result)
        elif async_result.failed():
            pipeline_state = {
                "stage": "failed",
                "error": str(async_result.info) if async_result.info else "Task failed"
            }
    
    # Fallback to legacy job_states if no Celery task
    elif job_id and job_id in job_states:
        state = job_states[job_id]
        pipeline_state = {
            "stage": state.stage,
            "started_at": state.started_at,
            "updated_at": state.updated_at,
            "completed_at": state.completed_at,
            "error": state.error
        }
    
    return {
        "document_id": document_id,
        "status": status,
        "file_name": metadata.get("file_name"),
        "uploaded_at": metadata.get("uploaded_at"),
        "completed_at": metadata.get("completed_at") if status == "completed" else None,
        "pipeline_state": pipeline_state,
        "error": metadata.get("error")
    }

@app.get(f"{settings.api_prefix}/documents/{{document_id}}/schema")
async def get_document_schema(
    document_id: str,
    authorized: bool = Depends(verify_api_key)
):
    """Get generated JSON schema for a processed document"""
    # Try Redis first, then fallback to in-memory
    metadata = state_manager.get_document_metadata(document_id)
    if not metadata and document_id in document_metadata:
        metadata = document_metadata[document_id]
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Document not found")
    
    job_id = metadata.get("job_id")
    celery_task_id = metadata.get("celery_task_id")
    
    # Try to get schema from Celery result
    if celery_task_id:
        async_result = AsyncResult(celery_task_id, app=celery_app)
        
        if not async_result.successful():
            if async_result.failed():
                raise HTTPException(
                    status_code=400,
                    detail="Processing failed"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Processing not completed. Current status: {async_result.status}"
                )
        
        result = async_result.result
        if isinstance(result, dict):
            agent_results = result.get("agent_results", {})
            schema_data = agent_results.get("schema", {}).get("data")
            
            if schema_data:
                return schema_data
            else:
                # Try Redis task result storage
                if job_id:
                    stored_result = state_manager.get_task_result(job_id)
                    if stored_result:
                        agent_results = stored_result.get("agent_results", {})
                        schema_data = agent_results.get("schema", {}).get("data")
                        if schema_data:
                            return schema_data
    
    # Fallback to legacy job_states
    if job_id and job_id in job_states:
        state = job_states[job_id]
        
        if state.stage != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Processing not completed. Current stage: {state.stage}"
            )
        
        # Get schema from results
        schema_result = state.agent_results.get("schema")
        if schema_result and schema_result.data:
            return schema_result.data.dict()
    
    raise HTTPException(status_code=404, detail="Schema not available")

# Webhook Management Endpoints

@app.post(f"{settings.api_prefix}/webhooks/register")
@limiter.limit("10 per minute")  # Limit webhook registrations
async def register_webhook(
    request: Request,
    body: WebhookRegistration,
    authorized: bool = Depends(verify_api_key)
):
    """Register a webhook for document processing events - accepts JSON body"""
    webhook_id = str(uuid.uuid4())
    
    webhook_data = {
        "id": webhook_id,
        "name": body.webhook_name,
        "url": str(body.webhook_url),
        "events": body.events or ["document.processed"],
        "created_at": datetime.utcnow().isoformat(),
        "active": True
    }
    
    # Store in Redis for shared access with Celery workers
    state_manager.register_webhook(webhook_id, webhook_data)
    
    # Also store in legacy storage for backward compatibility
    webhooks[webhook_id] = webhook_data
    
    return {
        "webhook_id": webhook_id,
        "message": "Webhook registered successfully"
    }

@app.get(f"{settings.api_prefix}/webhooks/list")
async def list_webhooks(authorized: bool = Depends(verify_api_key)):
    """List all registered webhooks"""
    # Get webhooks from Redis
    redis_webhooks = state_manager.list_webhooks()
    
    # Merge with legacy storage if different
    all_webhooks = {w["id"]: w for w in redis_webhooks}
    for wid, wdata in webhooks.items():
        if wid not in all_webhooks:
            all_webhooks[wid] = wdata
    
    webhook_list = list(all_webhooks.values())
    
    return {
        "webhooks": webhook_list,
        "total": len(webhook_list)
    }

@app.put(f"{settings.api_prefix}/webhooks/{{webhook_id}}")
async def update_webhook(
    webhook_id: str,
    body: WebhookUpdate,
    authorized: bool = Depends(verify_api_key)
):
    """Update webhook configuration - accepts JSON body"""
    # Check Redis first
    webhook = state_manager.get_webhook(webhook_id)
    
    # Fallback to legacy storage
    if not webhook and webhook_id in webhooks:
        webhook = webhooks[webhook_id]
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Apply updates
    updates = body.dict(exclude_unset=True)
    if "webhook_url" in updates:
        updates["url"] = str(updates.pop("webhook_url"))
    if "webhook_name" in updates:
        updates["name"] = updates.pop("webhook_name")
    
    # Update in Redis
    state_manager.update_webhook(webhook_id, updates)
    
    # Update in legacy storage
    if webhook_id in webhooks:
        webhooks[webhook_id].update(updates)
        webhooks[webhook_id]["updated_at"] = datetime.utcnow().isoformat()
    
    return {
        "webhook_id": webhook_id,
        "message": "Webhook updated successfully"
    }

@app.delete(f"{settings.api_prefix}/webhooks/{{webhook_id}}")
async def delete_webhook(
    webhook_id: str,
    authorized: bool = Depends(verify_api_key)
):
    """Delete a webhook"""
    # Check if webhook exists in either storage
    webhook_exists = state_manager.get_webhook(webhook_id) or webhook_id in webhooks
    
    if not webhook_exists:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Delete from Redis
    state_manager.delete_webhook(webhook_id)
    
    # Delete from legacy storage
    if webhook_id in webhooks:
        del webhooks[webhook_id]
    
    return {
        "message": "Webhook deleted successfully"
    }

# Health and Monitoring Endpoints

@app.get("/health")
async def health_check(verbose: bool = Query(False, description="Return detailed health information")):
    """Health check endpoint with optional verbose mode"""
    agent_health = await orchestrator.health_check()
    
    response = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment,
        "agents": agent_health
    }
    
    # Add verbose information if requested
    if verbose:
        response["config"] = {
            "redis_host": settings.redis_host,
            "redis_port": settings.redis_port,
            "api_prefix": settings.api_prefix,
            "upload_directory": settings.upload_directory,
            "max_upload_size_mb": settings.max_upload_size_mb,
            "enable_api_key_auth": settings.enable_api_key_auth,
            "celery_broker": f"redis://{settings.redis_host}:{settings.redis_port}/1",
            "celery_backend": f"redis://{settings.redis_host}:{settings.redis_port}/2"
        }
        
        # Check Redis connectivity
        redis_healthy = state_manager.ping()
        response["services"] = {
            "redis": "healthy" if redis_healthy else "unhealthy",
            "celery": "configured"  # Could add actual Celery health check here
        }
    
    return response

@app.get(f"{settings.api_prefix}/metrics")
async def get_metrics(authorized: bool = Depends(verify_api_key)):
    """Get application metrics"""
    total_documents = len(document_metadata)
    completed_documents = sum(
        1 for doc in document_metadata.values()
        if doc.get("status") == "completed"
    )
    failed_documents = sum(
        1 for doc in document_metadata.values()
        if doc.get("status") == "failed"
    )
    
    return {
        "total_documents": total_documents,
        "completed_documents": completed_documents,
        "failed_documents": failed_documents,
        "processing_documents": total_documents - completed_documents - failed_documents,
        "registered_webhooks": len(webhooks),
        "active_jobs": len(job_states)
    }

# Note: Webhook triggering is now handled by the Celery task trigger_webhooks_task
# in app/tasks.py for better scalability and error handling

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )