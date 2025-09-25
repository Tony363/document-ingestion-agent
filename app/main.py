"""
Main FastAPI Application

Entry point for the document processing API with endpoints for
document upload, status checking, and webhook management.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import uuid
import hashlib
from pathlib import Path
import shutil
import logging
from datetime import datetime

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

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Initialize agent orchestrator
orchestrator = AgentOrchestrator()

# Storage for job states (in production, use database)
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
async def verify_api_key(x_api_key: Optional[str] = None):
    """Verify API key if authentication is enabled"""
    if settings.enable_api_key_auth:
        if not x_api_key or x_api_key not in settings.api_keys:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return True

# Document Processing Endpoints

@app.post(f"{settings.api_prefix}/documents/upload")
async def upload_document(
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
    document_metadata[document_id] = {
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
    if document_id not in document_metadata:
        raise HTTPException(status_code=404, detail="Document not found")
    
    metadata = document_metadata[document_id]
    job_id = metadata.get("job_id")
    
    # Get pipeline state if available
    pipeline_state = None
    if job_id and job_id in job_states:
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
        "status": metadata.get("status", "unknown"),
        "file_name": metadata.get("file_name"),
        "uploaded_at": metadata.get("uploaded_at"),
        "completed_at": metadata.get("completed_at"),
        "pipeline_state": pipeline_state,
        "error": metadata.get("error")
    }

@app.get(f"{settings.api_prefix}/documents/{{document_id}}/schema")
async def get_document_schema(
    document_id: str,
    authorized: bool = Depends(verify_api_key)
):
    """Get generated JSON schema for a processed document"""
    if document_id not in document_metadata:
        raise HTTPException(status_code=404, detail="Document not found")
    
    metadata = document_metadata[document_id]
    job_id = metadata.get("job_id")
    
    if not job_id or job_id not in job_states:
        raise HTTPException(status_code=404, detail="Processing not completed")
    
    state = job_states[job_id]
    
    if state.stage != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Processing not completed. Current stage: {state.stage}"
        )
    
    # Get schema from results
    schema_result = state.agent_results.get("schema")
    if not schema_result or not schema_result.data:
        raise HTTPException(status_code=404, detail="Schema not available")
    
    return schema_result.data.dict()

# Webhook Management Endpoints

@app.post(f"{settings.api_prefix}/webhooks/register")
async def register_webhook(
    webhook_url: str,
    webhook_name: str,
    events: Optional[List[str]] = None,
    authorized: bool = Depends(verify_api_key)
):
    """Register a webhook for document processing events"""
    webhook_id = str(uuid.uuid4())
    
    webhooks[webhook_id] = {
        "id": webhook_id,
        "name": webhook_name,
        "url": webhook_url,
        "events": events or ["document.processed"],
        "created_at": datetime.utcnow().isoformat(),
        "active": True
    }
    
    return {
        "webhook_id": webhook_id,
        "message": "Webhook registered successfully"
    }

@app.get(f"{settings.api_prefix}/webhooks/list")
async def list_webhooks(authorized: bool = Depends(verify_api_key)):
    """List all registered webhooks"""
    return {
        "webhooks": list(webhooks.values()),
        "total": len(webhooks)
    }

@app.put(f"{settings.api_prefix}/webhooks/{{webhook_id}}")
async def update_webhook(
    webhook_id: str,
    webhook_url: Optional[str] = None,
    active: Optional[bool] = None,
    authorized: bool = Depends(verify_api_key)
):
    """Update webhook configuration"""
    if webhook_id not in webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook = webhooks[webhook_id]
    
    if webhook_url:
        webhook["url"] = webhook_url
    if active is not None:
        webhook["active"] = active
    
    webhook["updated_at"] = datetime.utcnow().isoformat()
    
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
    if webhook_id not in webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    del webhooks[webhook_id]
    
    return {
        "message": "Webhook deleted successfully"
    }

# Health and Monitoring Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    agent_health = await orchestrator.health_check()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment,
        "agents": agent_health
    }

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