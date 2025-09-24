#!/usr/bin/env python3
"""
Document Ingestion Agent v2.0 - Agentic Pipeline
FastAPI application for PDF/image document processing with Mistral OCR integration
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
import os

# Import configuration and agent orchestrator
from .config import settings
from .agents.agent_orchestrator import AgentOrchestrator

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize agent orchestrator
orchestrator = AgentOrchestrator(mistral_api_key=settings.mistral_api_key)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Agentic pipeline for PDF/image document processing with Mistral OCR integration",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., description="Unique document identifier")
    status: str = Field(..., description="Processing status")
    upload_url: Optional[str] = Field(None, description="Pre-signed upload URL if applicable")
    message: str = Field(..., description="Response message")

class DocumentStatus(BaseModel):
    document_id: str
    status: str  # received, queued, text_extracted, classified, extracted, validated, webhook_ready, completed, failed
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Progress percentage (0.0-1.0)")
    processing_stage: str
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

class ExtractedContent(BaseModel):
    document_id: str
    document_type: str
    raw_text: Optional[str] = None
    structured_content: Dict[str, Any]
    confidence_score: float
    metadata: Dict[str, Any]

class DocumentSchema(BaseModel):
    document_id: str
    document_type: str
    schema_version: str
    schema: Dict[str, Any]
    extraction_confidence: float
    webhook_ready: bool
    created_at: datetime

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    agents_status: Dict[str, str]

# In-memory storage for demo (replace with proper database in production)
documents_db = {}
processing_status_db = {}

# Get supported file types from configuration
SUPPORTED_FILE_TYPES = set(settings.supported_file_types_list)
MAX_FILE_SIZE = settings.max_file_size

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Document Ingestion Agent v2.0",
        "version": "2.0.0",
        "description": "Agentic pipeline for PDF/image document processing",
        "docs_url": "/docs",
        "health_check": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.utcnow(),
        agents_status={
            "validation_agent": "active",
            "classification_agent": "active", 
            "mistral_ocr_agent": "active",
            "content_analysis_agent": "active",
            "schema_generation_agent": "active"
        }
    )

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file format and size"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in SUPPORTED_FILE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_extension}. Supported: {', '.join(SUPPORTED_FILE_TYPES)}"
        )
    
    # Note: file.size might not be available in all cases, so we'll check during processing
    logger.info(f"File validation passed: {file.filename}")

@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: Optional[str] = None
):
    """
    Upload PDF or image document for processing
    
    Args:
        file: PDF or image file (max 50MB)
        document_type: Optional document type hint (invoice, receipt, contract, form)
    
    Returns:
        DocumentUploadResponse with document_id and processing status
    """
    try:
        # Validate file
        validate_file(file)
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {len(content)} bytes. Maximum: {MAX_FILE_SIZE} bytes (50MB)"
            )
        
        # Store document metadata
        documents_db[document_id] = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "content": content,
            "document_type_hint": document_type,
            "uploaded_at": datetime.utcnow()
        }
        
        # Initialize processing status
        processing_status_db[document_id] = DocumentStatus(
            document_id=document_id,
            status="received",
            progress=0.1,
            processing_stage="validation",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Start background processing
        background_tasks.add_task(process_document_pipeline, document_id)
        
        logger.info(f"Document uploaded successfully: {document_id} ({file.filename})")
        
        return DocumentUploadResponse(
            document_id=document_id,
            status="received",
            message=f"Document {file.filename} uploaded successfully. Processing started."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during upload")

@app.get("/documents/{document_id}/status", response_model=DocumentStatus)
async def get_document_status(document_id: str):
    """Get processing status for a document"""
    if document_id not in processing_status_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return processing_status_db[document_id]

@app.get("/documents/{document_id}/content", response_model=ExtractedContent)
async def get_document_content(document_id: str):
    """Get extracted content from processed document"""
    if document_id not in processing_status_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    status = processing_status_db[document_id]
    if status.status not in ["completed", "webhook_ready"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Document not ready. Current status: {status.status}"
        )
    
    # Get actual processing results
    processing_results = documents_db.get(document_id, {}).get("processing_results", {})
    
    # Extract data from agent results
    content_analysis = processing_results.get("agent_results", {}).get("content_analysis", {})
    classification = processing_results.get("agent_results", {}).get("classification", {})
    ocr_result = processing_results.get("agent_results", {}).get("ocr_processing", {})
    
    # Build response from actual results
    document_type = classification.get("classification", {}).get("document_type", "unknown")
    extracted_fields = content_analysis.get("content_analysis", {}).get("extracted_fields", {})
    
    # Convert extracted fields to structured content
    structured_content = {}
    for field_name, field_data in extracted_fields.items():
        structured_content[field_name] = field_data.get("value", "")
    
    return ExtractedContent(
        document_id=document_id,
        document_type=document_type,
        raw_text=ocr_result.get("ocr_result", {}).get("extracted_text", ""),
        structured_content=structured_content,
        confidence_score=content_analysis.get("content_analysis", {}).get("confidence_scores", {}).get("overall", 0.0),
        metadata={
            "processing_time": processing_results.get("total_processing_time", 0.0),
            "pages": ocr_result.get("ocr_result", {}).get("page_count", 1),
            "language": ocr_result.get("ocr_result", {}).get("language", "en")
        }
    )

@app.get("/documents/{document_id}/schema", response_model=DocumentSchema)
async def get_document_schema(document_id: str):
    """Get generated JSON schema for processed document"""
    if document_id not in processing_status_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    status = processing_status_db[document_id]
    if status.status not in ["completed", "webhook_ready"]:
        raise HTTPException(
            status_code=400,
            detail=f"Schema not ready. Current status: {status.status}"
        )
    
    # Get actual processing results
    processing_results = documents_db.get(document_id, {}).get("processing_results", {})
    
    # Extract schema from schema generation agent results
    schema_generation = processing_results.get("agent_results", {}).get("schema_generation", {})
    classification = processing_results.get("agent_results", {}).get("classification", {})
    
    # Get the generated schema
    generated_schema = schema_generation.get("schema_generation", {})
    document_type = classification.get("classification", {}).get("document_type", "unknown")
    
    # Build response from actual results
    if generated_schema.get("generated_schema"):
        schema_data = generated_schema["generated_schema"]
        webhook_ready = generated_schema.get("webhook_ready", False)
        confidence = generated_schema.get("validation", {}).get("confidence", 0.0)
    else:
        # Fallback to empty schema if generation failed
        schema_data = {
            "document_type": document_type,
            "error": "Schema generation failed",
            "webhook_ready": False
        }
        webhook_ready = False
        confidence = 0.0
    
    return DocumentSchema(
        document_id=document_id,
        document_type=document_type,
        schema_version=generated_schema.get("schema_version", "1.0"),
        schema=schema_data,
        extraction_confidence=confidence,
        webhook_ready=webhook_ready,
        created_at=datetime.utcnow()
    )

@app.post("/documents/batch")
async def batch_upload(documents: List[dict]):
    """Batch document processing endpoint"""
    # Placeholder for batch processing
    raise HTTPException(status_code=501, detail="Batch processing not yet implemented")

@app.get("/schemas/{doc_type}")
async def get_schema_template(doc_type: str):
    """Get JSON schema template for document type"""
    templates = {
        "invoice": {
            "type": "object",
            "properties": {
                "vendor_info": {"type": "object"},
                "invoice_details": {"type": "object"},
                "line_items": {"type": "array"},
                "totals": {"type": "object"}
            }
        },
        "receipt": {
            "type": "object", 
            "properties": {
                "merchant_info": {"type": "object"},
                "transaction_details": {"type": "object"},
                "items": {"type": "array"},
                "payment": {"type": "object"}
            }
        }
    }
    
    if doc_type not in templates:
        raise HTTPException(status_code=404, detail=f"Schema template for '{doc_type}' not found")
    
    return templates[doc_type]

# Background processing pipeline
async def process_document_pipeline(document_id: str):
    """
    Main processing pipeline that coordinates all agents
    This is where the agentic pipeline magic happens
    """
    try:
        logger.info(f"Starting processing pipeline for document: {document_id}")
        
        # Get document data
        if document_id not in documents_db:
            raise ValueError(f"Document {document_id} not found in database")
        
        document_data = documents_db[document_id]
        
        # Prepare data for agent orchestrator
        processing_data = {
            "document_id": document_id,
            "filename": document_data["filename"],
            "content": document_data["content"],
            "content_type": document_data["content_type"],
            "size": document_data["size"],
            "document_type_hint": document_data.get("document_type_hint")
        }
        
        # Process through agent orchestrator
        pipeline_results = await orchestrator.process_document(
            processing_data,
            status_callback=lambda doc_id, stage, status: update_status_async(
                doc_id, status, get_progress_from_stage(stage), stage
            )
        )
        
        # Store results
        documents_db[document_id]["processing_results"] = pipeline_results
        
        # Update final status based on pipeline results
        if pipeline_results.get("overall_success"):
            await update_status(document_id, "webhook_ready", 1.0, "completed")
            logger.info(f"Processing completed successfully for document: {document_id}")
        else:
            error_msg = pipeline_results.get("error_details", "Unknown error")
            await update_status(document_id, "failed", 0.0, "error", error_msg)
            logger.error(f"Processing failed for document {document_id}: {error_msg}")
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        await update_status(document_id, "failed", 0.0, "error", str(e))

def get_progress_from_stage(stage: str) -> float:
    """Map processing stage to progress percentage"""
    stage_progress = {
        "validation": 0.2,
        "classification": 0.4,
        "ocr_processing": 0.6,
        "content_analysis": 0.8,
        "schema_generation": 0.9,
        "completed": 1.0
    }
    return stage_progress.get(stage, 0.5)

async def update_status_async(document_id: str, status: str, progress: float, stage: str):
    """Async wrapper for status update"""
    await update_status(document_id, status, progress, stage)

async def update_status(document_id: str, status: str, progress: float, stage: str, error: str = None):
    """Update document processing status"""
    if document_id in processing_status_db:
        processing_status_db[document_id].status = status
        processing_status_db[document_id].progress = progress
        processing_status_db[document_id].processing_stage = stage
        processing_status_db[document_id].updated_at = datetime.utcnow()
        if error:
            processing_status_db[document_id].error_message = error

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)