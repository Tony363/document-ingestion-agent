"""
Celery Tasks for Document Processing

This module defines asynchronous tasks for document processing
through the multi-agent pipeline.
"""

from celery import Task
from celery.utils.log import get_task_logger
from typing import Dict, Any
import asyncio
from datetime import datetime

from .celery_app import celery_app
from .agents import (
    AgentOrchestrator,
    ClassificationAgent,
    MistralOCRAgent,
    ContentAnalysisAgent,
    SchemaGenerationAgent,
    ValidationAgent
)
from .agents.base_agent import AgentContext
from .agents.agent_orchestrator import DocumentData
from .config import settings
from .services.state_manager import get_state_manager

# Configure logging
logger = get_task_logger(__name__)


class DocumentProcessingTask(Task):
    """Base task class with shared resources"""
    _orchestrator = None
    
    @property
    def orchestrator(self):
        """Lazy initialization of orchestrator with agents"""
        if self._orchestrator is None:
            self._orchestrator = AgentOrchestrator()
            
            # Initialize agents
            classification_agent = ClassificationAgent()
            ocr_agent = MistralOCRAgent(
                api_key=settings.mistral_api_key,
                api_url=settings.mistral_api_url,
                rate_limit_delay=settings.mistral_rate_limit_delay
            )
            analysis_agent = ContentAnalysisAgent()
            schema_agent = SchemaGenerationAgent()
            validation_agent = ValidationAgent()
            
            # Register agents
            self._orchestrator.register_agent("classification", classification_agent)
            self._orchestrator.register_agent("ocr", ocr_agent)
            self._orchestrator.register_agent("analysis", analysis_agent)
            self._orchestrator.register_agent("schema", schema_agent)
            self._orchestrator.register_agent("validation", validation_agent)
            
            logger.info("Document processing orchestrator initialized")
        
        return self._orchestrator


@celery_app.task(
    name="app.tasks.process_document",
    base=DocumentProcessingTask,
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def process_document_task(self, document_dict: Dict[str, Any], context_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a document through the multi-agent pipeline
    
    Args:
        document_dict: Serialized DocumentData
        context_dict: Serialized AgentContext
        
    Returns:
        Processing result with status and extracted data
    """
    try:
        logger.info(f"Starting document processing for job_id: {context_dict.get('job_id')}")
        
        # Reconstruct objects from dictionaries
        document = DocumentData(**document_dict)
        context = AgentContext(**context_dict)
        
        # Run async processing in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Execute pipeline
            pipeline_state = loop.run_until_complete(
                self.orchestrator.execute_pipeline(document, context)
            )
            
            # Prepare result
            result = {
                "job_id": context.job_id,
                "document_id": context.document_id,
                "status": "completed" if pipeline_state.stage == "completed" else "failed",
                "stage": pipeline_state.stage,
                "started_at": pipeline_state.started_at,
                "completed_at": pipeline_state.completed_at or datetime.utcnow().isoformat(),
                "agent_results": {}
            }
            
            # Extract agent results
            for agent_name, agent_result in pipeline_state.agent_results.items():
                if agent_result and agent_result.data:
                    result["agent_results"][agent_name] = {
                        "success": agent_result.success,
                        "data": agent_result.data.dict() if hasattr(agent_result.data, 'dict') else agent_result.data
                    }
            
            # Store result in Redis for status/schema endpoints
            state_manager = get_state_manager(settings.redis_host, settings.redis_port, 0)
            state_manager.store_task_result(context.job_id, result)
            
            # Update document status in Redis
            state_manager.update_document_status(context.document_id, "completed")
            
            # Check if validation passed for webhook triggering
            if pipeline_state.stage == "completed":
                validation_result = pipeline_state.agent_results.get("validation", {})
                if validation_result and validation_result.data and hasattr(validation_result.data, 'is_valid'):
                    if validation_result.data.is_valid:
                        # Queue webhook notification task with full payload
                        webhook_payload = {
                            "event": "document.processed",
                            "timestamp": datetime.utcnow().isoformat(),
                            "document_id": context.document_id,
                            "job_id": context.job_id,
                            "schema": result["agent_results"].get("schema", {}).get("data", {})
                        }
                        trigger_webhooks_task.delay(webhook_payload)
            
            logger.info(f"Document processing completed for job_id: {context.job_id}")
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Document processing failed: {str(e)}", exc_info=True)
        
        # Retry if retries available
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task, attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=e)
        
        # Return error result
        return {
            "job_id": context_dict.get("job_id"),
            "document_id": context_dict.get("document_id"),
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        }


@celery_app.task(
    name="app.tasks.trigger_webhooks",
    max_retries=3,
    default_retry_delay=30
)
def trigger_webhooks_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trigger registered webhooks with document processing results
    
    Args:
        payload: Full webhook payload with event, timestamp, document_id, job_id, and schema
        
    Returns:
        Webhook delivery results
    """
    import httpx
    
    logger.info(f"Triggering webhooks for document {payload.get('document_id')}")
    
    results = {
        "webhooks_triggered": 0,
        "webhooks_failed": 0,
        "details": []
    }
    
    # Get webhooks from Redis shared state
    state_manager = get_state_manager(settings.redis_host, settings.redis_port, 0)
    
    try:
        # Fetch active webhooks from Redis
        webhooks = state_manager.list_webhooks(active_only=True)
        
        for webhook in webhooks:
            if not webhook.get("active"):
                continue
                
            # Check if webhook is subscribed to this event
            events = webhook.get("events", ["document.processed"])
            if payload.get("event") not in events:
                continue
                
            try:
                with httpx.Client() as client:
                    response = client.post(
                        webhook["url"],
                        json=payload,  # Send full payload, not just schema
                        timeout=settings.webhook_timeout_seconds,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if 200 <= response.status_code < 300:
                        results["webhooks_triggered"] += 1
                        results["details"].append({
                            "webhook_id": webhook["id"],
                            "status": "success",
                            "status_code": response.status_code
                        })
                        logger.info(f"Webhook {webhook['id']} triggered successfully")
                    else:
                        results["webhooks_failed"] += 1
                        results["details"].append({
                            "webhook_id": webhook["id"],
                            "status": "failed",
                            "status_code": response.status_code
                        })
                        logger.error(f"Webhook {webhook['id']} failed with status {response.status_code}")
                        
            except Exception as e:
                results["webhooks_failed"] += 1
                results["details"].append({
                    "webhook_id": webhook["id"],
                    "status": "error",
                    "error": str(e)
                })
                logger.error(f"Failed to trigger webhook {webhook['id']}: {e}")
                
    except Exception as e:
        logger.error(f"Failed to fetch webhooks: {e}")
        
    return results


@celery_app.task(name="app.tasks.health_check")
def health_check_task() -> Dict[str, str]:
    """
    Simple health check task to verify Celery is working
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "worker": "celery",
        "timestamp": datetime.utcnow().isoformat()
    }