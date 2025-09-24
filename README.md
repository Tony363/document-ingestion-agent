# Document Ingestion Agent

An intelligent multi-agent pipeline for processing multi-media documents (PDFs, images) through specialized AI agents, extracting structured data, and generating standardized JSON schemas for webhook and API automation triggers using the Mistral AI OCR API.

## Table of Contents
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Development Setup](#development-setup)
- [Multi-Agent System](#multi-agent-system)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Features

- **Multi-Format Support**: Process PDFs, images (PNG, JPG, TIFF, BMP)
- **5-Agent Architecture**: Specialized agents for classification, OCR, analysis, schema generation, and validation
- **Mistral AI OCR Integration**: Exclusive OCR provider for accurate text extraction with rate limiting
- **Async Processing**: Non-blocking document processing with Celery background tasks
- **Webhook Automation**: Automatic webhook triggers upon completion with customizable events
- **Docker Development**: Hybrid development modes with containerized dependencies
- **Health Monitoring**: Real-time agent health checks and application metrics
- **Schema Generation**: Standardized JSON output for automation triggers
- **Rate Limiting**: Intelligent API protection and throttling
- **Retry Logic**: Automatic retry with exponential backoff for fault tolerance
- **API Authentication**: Secure API key-based authentication
- **File Validation**: Content type checking, size limits, and deduplication

## Architecture Overview

### System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Client[Client Application]
        Webhook[Webhook Consumer]
        Docs[API Documentation<br/>Swagger/ReDoc]
    end
    
    subgraph "API Gateway Layer"
        FastAPI[FastAPI Server<br/>Port 8000]
        Auth[API Key Auth<br/>X-API-Key Header]
        CORS[CORS Middleware]
        Rate[Rate Limiting]
    end
    
    subgraph "Processing Layer"
        Orchestrator[Agent Orchestrator<br/>Pipeline Manager]
        BG[Background Tasks<br/>Celery Workers]
        
        subgraph "5-Agent Pipeline"
            CA[Classification Agent<br/>Document Type & Format]
            OA[Mistral OCR Agent<br/>Text Extraction API]
            AA[Content Analysis Agent<br/>Pattern-Based Parsing]
            SA[Schema Generation Agent<br/>JSON Schema Creation]
            VA[Validation Agent<br/>Business Rules Check]
        end
    end
    
    subgraph "Data Layer"
        Redis[(Redis Cache<br/>Port 6379<br/>State & Messages)]
        Storage[File Storage<br/>Document Files]
        Memory[In-Memory Store<br/>Dev Mode)]
    end
    
    subgraph "External Services"
        MistralAPI[Mistral AI<br/>OCR API]
        WebhookURL[Webhook Endpoints<br/>External Systems]
    end
    
    Client -->|POST /upload| FastAPI
    Client -->|GET /status| FastAPI
    Client -->|GET /schema| FastAPI
    
    FastAPI --> Auth
    FastAPI --> CORS
    FastAPI --> Rate
    Auth --> Orchestrator
    
    Orchestrator --> BG
    BG --> CA
    CA -->|Document Type| OA
    OA -->|HTTP Request| MistralAPI
    MistralAPI -->|Extracted Text| OA
    OA --> AA
    AA -->|Parsed Fields| SA
    SA -->|JSON Schema| VA
    VA -->|Validated Data| Orchestrator
    
    Orchestrator --> Redis
    Orchestrator --> Storage
    Orchestrator -->|Trigger Webhook| WebhookURL
    
    FastAPI --> Docs
    
    style FastAPI fill:#4CAF50
    style Orchestrator fill:#2196F3
    style Redis fill:#DC382D
    style OA fill:#FF9800
    style MistralAPI fill:#FF6B35
    style BG fill:#9C27B0
```

### Pipeline State Flow

```mermaid
stateDiagram-v2
    [*] --> RECEIVED: Document Upload<br/>POST /upload
    RECEIVED --> CLASSIFICATION: Background Task Started
    CLASSIFICATION --> OCR: Document Type Identified
    OCR --> ANALYSIS: Mistral AI Text Extraction
    ANALYSIS --> SCHEMA_GENERATION: Fields Extracted & Parsed
    SCHEMA_GENERATION --> VALIDATION: JSON Schema Generated
    VALIDATION --> COMPLETED: Business Rules Passed
    VALIDATION --> FAILED: Validation Error
    COMPLETED --> [*]: Webhook Triggered
    FAILED --> [*]: Error Response
    
    CLASSIFICATION --> FAILED: Invalid Format
    OCR --> FAILED: OCR API Error
    ANALYSIS --> FAILED: Parsing Error
    SCHEMA_GENERATION --> FAILED: Schema Error
    
    note right of OCR: Rate Limited<br/>Retry with Backoff
    note right of VALIDATION: Configurable Rules<br/>Data Quality Check
    note right of COMPLETED: Automatic Webhook<br/>JSON Payload
```

### Development Workflow

```mermaid
flowchart LR
    subgraph "Local Development"
        Code[Source Code]
        App[FastAPI App<br/>localhost:8000]
        Tests[pytest Tests]
    end
    
    subgraph "Docker Dependencies"
        Redis[Redis Container<br/>Port 6379]
        Celery[Celery Worker<br/>Container]
    end
    
    subgraph "External Services"
        Mistral[Mistral AI API]
        Webhooks[Test Webhooks]
    end
    
    Code --> App
    App --> Redis
    App --> Celery
    App --> Mistral
    App --> Webhooks
    Tests --> App
    
    style App fill:#4CAF50
    style Redis fill:#DC382D
    style Celery fill:#9C27B0
```

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Mistral AI API Key

### 1. Clone & Setup
```bash
git clone https://github.com/yourusername/document-ingestion-agent.git
cd document-ingestion-agent
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit with your configuration
nano .env
```

Required environment variables:
```env
MISTRAL_API_KEY=your_mistral_api_key_here
API_HOST=0.0.0.0
API_PORT=8000
REDIS_HOST=localhost
DATABASE_URL=postgresql://user:password@localhost/dbname
```

### 3. Quick Start Options

**Option A: Hybrid Development (Recommended)**
```bash
# Start dependencies only
docker-compose -f docker-compose.dev.yml up -d

# Run app locally
./run_server.sh
```

**Option B: Full Docker**
```bash
# Start everything in containers
docker-compose up --build
```

### 4. Test the Pipeline
```bash
# Test with sample document
python test_pipeline.py

# Or upload via API
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "X-API-Key: dev-key-123" \
  -F "file=@sample_document.pdf"
```

## API Documentation

The Document Ingestion Agent provides a comprehensive REST API with 9 endpoints for document processing, status monitoring, webhook management, and system health checks.

**Base URL**: `http://localhost:8000/api/v1`
**Authentication**: `X-API-Key` header (if enabled)
**Content-Type**: `application/json` or `multipart/form-data`

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

### 1. Document Upload

**Endpoint**: `POST /api/v1/documents/upload`

Upload a document for processing through the 5-agent pipeline.

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "X-API-Key: your-api-key" \
  -H "Accept: application/json" \
  -F "file=@document.pdf"
```

**With custom filename**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "X-API-Key: dev-key-123" \
  -F "file=@/path/to/invoice.pdf;filename=customer_invoice_2024.pdf"
```

**Response** (202 Accepted):
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "document_id": "doc-uuid-here",
  "message": "Document uploaded and processing started",
  "status_url": "/api/v1/documents/doc-uuid-here/status"
}
```

**Error Responses**:
```bash
# File too large (400)
{
  "detail": "File size exceeds 10MB limit"
}

# Unsupported file type (400)
{
  "detail": "File type .txt not supported"
}

# Invalid API key (401)
{
  "detail": "Invalid API key"
}
```

### 2. Document Status

**Endpoint**: `GET /api/v1/documents/{document_id}/status`

Check processing status and pipeline progress for a document.

**Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/documents/doc-uuid-here/status" \
  -H "X-API-Key: your-api-key" \
  -H "Accept: application/json"
```

**Response** (200 OK):
```json
{
  "document_id": "doc-uuid-here",
  "status": "completed",
  "file_name": "invoice.pdf",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:32:15Z",
  "pipeline_state": {
    "stage": "completed",
    "started_at": "2024-01-15T10:30:01Z",
    "updated_at": "2024-01-15T10:32:15Z",
    "completed_at": "2024-01-15T10:32:15Z",
    "error": null
  },
  "error": null
}
```

**Status Values**:
- `processing`: Document uploaded, pipeline running
- `completed`: Successfully processed through all agents
- `failed`: Error occurred during processing

**Pipeline Stages**:
- `RECEIVED`: Document uploaded and queued
- `CLASSIFICATION`: Identifying document type
- `OCR`: Extracting text via Mistral AI
- `ANALYSIS`: Parsing fields and content
- `SCHEMA_GENERATION`: Creating JSON schema
- `VALIDATION`: Business rules validation
- `COMPLETED`: Ready for retrieval

### 3. Get Generated Schema

**Endpoint**: `GET /api/v1/documents/{document_id}/schema`

Retrieve the generated JSON schema for a successfully processed document.

**Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/documents/doc-uuid-here/schema" \
  -H "X-API-Key: your-api-key" \
  -H "Accept: application/json"
```

**Response** (200 OK):
```json
{
  "document_type": "invoice",
  "confidence_score": 0.95,
  "extracted_fields": {
    "invoice_number": "INV-2024-001",
    "date": "2024-01-15",
    "total_amount": 1250.00,
    "currency": "USD",
    "vendor": {
      "name": "ABC Corp",
      "address": "123 Business St, City, State 12345",
      "tax_id": "123456789"
    },
    "line_items": [
      {
        "description": "Professional Services",
        "quantity": 10,
        "unit_price": 125.00,
        "total": 1250.00
      }
    ]
  },
  "validation_results": {
    "is_valid": true,
    "errors": [],
    "warnings": []
  },
  "processing_metadata": {
    "ocr_confidence": 0.98,
    "processing_time_ms": 2150,
    "agent_versions": {
      "classification": "1.0.0",
      "ocr": "1.0.0",
      "analysis": "1.0.0",
      "schema": "1.0.0",
      "validation": "1.0.0"
    }
  }
}
```

### 4. Register Webhook

**Endpoint**: `POST /api/v1/webhooks/register`

Register a webhook URL to receive automatic notifications when documents are processed.

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/register" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://your-app.com/webhooks/document-processed",
    "webhook_name": "Production Document Handler",
    "events": ["document.processed", "document.failed"]
  }'
```

**Minimal request**:
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/register" \
  -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://webhook.site/unique-url",
    "webhook_name": "Test Webhook"
  }'
```

**Response** (200 OK):
```json
{
  "webhook_id": "webhook-uuid-here",
  "message": "Webhook registered successfully"
}
```

**Webhook Payload** (sent to your URL):
```json
{
  "event": "document.processed",
  "timestamp": "2024-01-15T10:32:15Z",
  "document_id": "doc-uuid-here",
  "job_id": "job-uuid-here",
  "schema": {
    "document_type": "invoice",
    "extracted_fields": { ... },
    "validation_results": { ... }
  }
}
```

### 5. List Webhooks

**Endpoint**: `GET /api/v1/webhooks/list`

Retrieve all registered webhooks with their configuration.

**Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/webhooks/list" \
  -H "X-API-Key: your-api-key" \
  -H "Accept: application/json"
```

**Response** (200 OK):
```json
{
  "webhooks": [
    {
      "id": "webhook-uuid-1",
      "name": "Production Handler",
      "url": "https://api.yourapp.com/webhooks/docs",
      "events": ["document.processed"],
      "created_at": "2024-01-15T09:00:00Z",
      "active": true
    },
    {
      "id": "webhook-uuid-2",
      "name": "Backup Webhook",
      "url": "https://backup.yourapp.com/webhook",
      "events": ["document.processed", "document.failed"],
      "created_at": "2024-01-15T09:15:00Z",
      "active": false
    }
  ],
  "total": 2
}
```

### 6. Update Webhook

**Endpoint**: `PUT /api/v1/webhooks/{webhook_id}`

Update webhook configuration including URL and active status.

**Request**:
```bash
curl -X PUT "http://localhost:8000/api/v1/webhooks/webhook-uuid-here" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://new-endpoint.yourapp.com/webhook",
    "active": false
  }'
```

**Disable webhook only**:
```bash
curl -X PUT "http://localhost:8000/api/v1/webhooks/webhook-uuid-here" \
  -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"active": false}'
```

**Response** (200 OK):
```json
{
  "webhook_id": "webhook-uuid-here",
  "message": "Webhook updated successfully"
}
```

### 7. Delete Webhook

**Endpoint**: `DELETE /api/v1/webhooks/{webhook_id}`

Permanently delete a webhook registration.

**Request**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/webhooks/webhook-uuid-here" \
  -H "X-API-Key: your-api-key"
```

**Response** (200 OK):
```json
{
  "message": "Webhook deleted successfully"
}
```

### 8. Health Check

**Endpoint**: `GET /health`

System health check with agent status and application information.

**Request**:
```bash
curl -X GET "http://localhost:8000/health" \
  -H "Accept: application/json"
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:45:30Z",
  "version": "1.0.0",
  "environment": "development",
  "agents": {
    "classification": {
      "status": "healthy",
      "last_check": "2024-01-15T10:45:29Z"
    },
    "ocr": {
      "status": "healthy",
      "last_check": "2024-01-15T10:45:29Z",
      "api_status": "connected"
    },
    "analysis": {
      "status": "healthy",
      "last_check": "2024-01-15T10:45:29Z"
    },
    "schema": {
      "status": "healthy",
      "last_check": "2024-01-15T10:45:29Z"
    },
    "validation": {
      "status": "healthy",
      "last_check": "2024-01-15T10:45:29Z"
    }
  }
}
```

### 9. Application Metrics

**Endpoint**: `GET /api/v1/metrics`

Retrieve application performance metrics and statistics.

**Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/metrics" \
  -H "X-API-Key: your-api-key" \
  -H "Accept: application/json"
```

**Response** (200 OK):
```json
{
  "total_documents": 156,
  "completed_documents": 142,
  "failed_documents": 8,
  "processing_documents": 6,
  "registered_webhooks": 3,
  "active_jobs": 2,
  "uptime_seconds": 86400,
  "avg_processing_time_ms": 2847
}
```

### Complete API Workflow Example

Here's a complete workflow demonstrating document processing from upload to webhook:

```bash
#!/bin/bash
# Complete Document Processing Workflow

API_KEY="your-api-key"
BASE_URL="http://localhost:8000/api/v1"

echo "1. Upload document..."
UPLOAD_RESPONSE=$(curl -s -X POST "${BASE_URL}/documents/upload" \
  -H "X-API-Key: ${API_KEY}" \
  -F "file=@sample_invoice.pdf")

DOCUMENT_ID=$(echo $UPLOAD_RESPONSE | jq -r '.document_id')
echo "Document ID: $DOCUMENT_ID"

echo "2. Register webhook..."
WEBHOOK_RESPONSE=$(curl -s -X POST "${BASE_URL}/webhooks/register" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://webhook.site/unique-url",
    "webhook_name": "Test Processing Webhook"
  }')

WEBHOOK_ID=$(echo $WEBHOOK_RESPONSE | jq -r '.webhook_id')
echo "Webhook ID: $WEBHOOK_ID"

echo "3. Monitor processing status..."
while true; do
  STATUS_RESPONSE=$(curl -s -X GET "${BASE_URL}/documents/${DOCUMENT_ID}/status" \
    -H "X-API-Key: ${API_KEY}")
  
  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
  STAGE=$(echo $STATUS_RESPONSE | jq -r '.pipeline_state.stage // "unknown"')
  
  echo "Status: $STATUS, Stage: $STAGE"
  
  if [ "$STATUS" = "completed" ]; then
    echo "4. Retrieve generated schema..."
    curl -s -X GET "${BASE_URL}/documents/${DOCUMENT_ID}/schema" \
      -H "X-API-Key: ${API_KEY}" | jq '.'
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Processing failed!"
    echo $STATUS_RESPONSE | jq '.error'
    break
  fi
  
  sleep 2
done

echo "5. Check application metrics..."
curl -s -X GET "${BASE_URL}/metrics" \
  -H "X-API-Key: ${API_KEY}" | jq '.'

echo "Workflow completed!"
```

## Development Setup

### Hybrid Development (Recommended)

Run dependencies in Docker while developing the application locally for fast iteration:

```bash
# 1. Start Redis and Celery in Docker
docker-compose -f docker-compose.dev.yml up -d

# 2. Install Python dependencies locally
pip install -r requirements.txt

# 3. Run the FastAPI server locally
./run_server.sh

# 4. Run tests
python test_pipeline.py
```

### Full Docker Development

Run everything in containers for environment consistency:

```bash
# Start all services
docker-compose up --build

# View logs
docker-compose logs -f app
docker-compose logs -f celery

# Run tests in container
docker-compose exec app python test_pipeline.py
```

### Dependencies-Only Development

Use Docker only for external dependencies:

```bash
# Start only Redis
./scripts/start-docker-deps.sh

# Install and run locally
pip install -r requirements.txt
python -m app.main
```

### Environment Variables

Create `.env` file in the project root:

```env
# Required
MISTRAL_API_KEY=your_mistral_api_key_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# Authentication (Optional)
ENABLE_API_KEY_AUTH=true
API_KEYS=dev-key-123,prod-key-456

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Database (Optional - uses in-memory for development)
DATABASE_URL=postgresql://user:password@localhost/document_agent

# File Processing
MAX_UPLOAD_SIZE_MB=10
ALLOWED_EXTENSIONS=.pdf,.png,.jpg,.jpeg,.tiff,.bmp
UPLOAD_DIRECTORY=./uploads

# Mistral AI Configuration
MISTRAL_API_URL=https://api.mistral.ai/v1/chat/completions
MISTRAL_RATE_LIMIT_DELAY=1.0

# Webhook Configuration
WEBHOOK_TIMEOUT_SECONDS=30

# Application
APP_NAME=Document Ingestion Agent
APP_VERSION=1.0.0
ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG=true

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Development Commands

```bash
# Format code
black app/ --line-length 100

# Lint code
ruff check app/

# Type checking
mypy app/

# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Test specific component
pytest tests/test_ocr_agent.py -v

# Integration test
python test_pipeline.py path/to/test/document.pdf
```

## Multi-Agent System

### Agent Architecture

The system implements a **5-Agent Architecture** where each agent inherits from `BaseAgent` and has a specific responsibility in the document processing pipeline.

#### BaseAgent Class

**File**: `app/agents/base_agent.py`

All agents inherit from `BaseAgent` which provides:
- Async execution with `execute()` method
- Automatic retry logic with exponential backoff
- Health check capabilities
- Standardized error handling
- Metrics collection hooks

```python
class BaseAgent:
    async def execute(self, data, context: AgentContext) -> AgentResult
    async def health_check() -> Dict[str, Any]
    def get_metrics() -> Dict[str, Any]
```

### 1. ClassificationAgent

**File**: `app/agents/classification_agent.py`

**Purpose**: Identifies document type and validates file format

**Responsibilities**:
- File format validation (PDF, PNG, JPG, TIFF, BMP)
- Document type classification (invoice, receipt, contract, etc.)
- Content type verification
- Size limit enforcement

**Output**: Document classification with confidence score

### 2. MistralOCRAgent

**File**: `app/agents/mistral_ocr_agent.py`

**Purpose**: Text extraction via Mistral AI OCR API (exclusive OCR provider)

**Responsibilities**:
- PDF and image text extraction
- Rate limiting with configurable delays
- Retry logic with exponential backoff
- OCR confidence scoring
- API error handling

**Key Features**:
- Uses httpx for async HTTP requests
- Intelligent rate limiting
- Supports multiple document formats
- Returns structured text with confidence metrics

### 3. ContentAnalysisAgent

**File**: `app/agents/content_analysis_agent.py`

**Purpose**: Pattern-based field extraction and content parsing

**Responsibilities**:
- Extract structured fields from raw text
- Pattern recognition for different document types
- Field validation and normalization
- Data cleaning and preprocessing

**Patterns Supported**:
- Invoice: number, date, amounts, vendor info
- Receipt: merchant, items, totals
- Contract: parties, dates, terms
- Custom: user-defined patterns

### 4. SchemaGenerationAgent

**File**: `app/agents/schema_generation_agent.py`

**Purpose**: Creates standardized JSON schemas for automation

**Responsibilities**:
- Generate structured JSON schemas
- Map extracted fields to standardized formats
- Create metadata and confidence scores
- Prepare data for webhook delivery

**Schema Format**:
```json
{
  "document_type": "string",
  "confidence_score": "float",
  "extracted_fields": "object",
  "validation_results": "object",
  "processing_metadata": "object"
}
```

### 5. ValidationAgent

**File**: `app/agents/validation_agent.py`

**Purpose**: Business rule validation and data quality assessment

**Responsibilities**:
- Apply business rules validation
- Data quality assessment
- Completeness checks
- Error detection and reporting
- Final approval for webhook triggering

**Validation Types**:
- Required field validation
- Format validation (dates, amounts, etc.)
- Business logic rules
- Data consistency checks

### Agent Orchestrator

**File**: `app/agents/agent_orchestrator.py`

**Purpose**: Manages pipeline execution and state transitions

**Key Features**:
- Sequential agent execution
- State management and persistence
- Error handling and recovery
- Parallel processing capabilities
- Health monitoring across all agents

**Pipeline Execution**:
```python
async def execute_pipeline(document: DocumentData, context: AgentContext) -> PipelineState:
    # RECEIVED -> CLASSIFICATION
    classification_result = await self.agents["classification"].execute(document, context)
    
    # CLASSIFICATION -> OCR
    ocr_result = await self.agents["ocr"].execute(document, context)
    
    # OCR -> ANALYSIS
    analysis_result = await self.agents["analysis"].execute(ocr_result, context)
    
    # ANALYSIS -> SCHEMA_GENERATION
    schema_result = await self.agents["schema"].execute(analysis_result, context)
    
    # SCHEMA_GENERATION -> VALIDATION
    validation_result = await self.agents["validation"].execute(schema_result, context)
    
    # Return final state
    return pipeline_state
```

## Configuration

### Pydantic Settings

**File**: `app/config.py`

The application uses Pydantic V2 for configuration management with environment variable mapping and validation.

**Key Features**:
- Automatic type validation
- Environment variable mapping with aliases
- Default value handling
- Configuration validation on startup

**Configuration Categories**:

#### API Configuration
```python
app_name: str = "Document Ingestion Agent"
app_version: str = "1.0.0"
api_host: str = "0.0.0.0"
api_port: int = 8000
api_prefix: str = "/api/v1"
```

#### Authentication
```python
enable_api_key_auth: bool = False
api_keys: List[str] = ["dev-key-123"]
```

#### File Processing
```python
max_upload_size_mb: int = 10
allowed_extensions: List[str] = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
upload_directory: str = "./uploads"
```

#### Mistral AI Integration
```python
mistral_api_key: str
mistral_api_url: str = "https://api.mistral.ai/v1/chat/completions"
mistral_rate_limit_delay: float = 1.0
```

#### Infrastructure
```python
redis_host: str = "localhost"
redis_port: int = 6379
database_url: Optional[str] = None
```

### Environment Variable Mapping

The configuration supports both standard and aliased environment variables for backward compatibility:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    mistral_api_key: str = Field(alias="MISTRAL_API_KEY")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
```

### Docker Configuration

#### Development Mode (`docker-compose.dev.yml`)
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  celery:
    build: .
    command: celery -A app.celery_app worker --loglevel=info
    volumes:
      - .:/app
    depends_on:
      - redis
```

#### Production Mode (`docker-compose.yml`)
```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MISTRAL_API_KEY=${MISTRAL_API_KEY}
      - REDIS_HOST=redis
    depends_on:
      - redis
      - postgres
  
  celery:
    build: .
    command: celery -A app.celery_app worker --loglevel=info
    depends_on:
      - redis
      - postgres
  
  redis:
    image: redis:7-alpine
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: document_agent
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
```

## Testing

### Integration Testing

**File**: `test_pipeline.py`

Complete end-to-end pipeline testing with sample documents:

```bash
# Test with default sample
python test_pipeline.py

# Test with specific document
python test_pipeline.py path/to/document.pdf

# Test with multiple documents
python test_pipeline.py doc1.pdf doc2.png doc3.jpg
```

**Test Output**:
```
=== Document Processing Test ===
File: sample_invoice.pdf
Size: 156.7 KB
Type: application/pdf

✅ Upload successful
   Job ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
   Document ID: doc-uuid-here
   Status URL: /api/v1/documents/doc-uuid-here/status

⏳ Processing pipeline...
   Stage: CLASSIFICATION (2.1s)
   Stage: OCR (8.7s)
   Stage: ANALYSIS (1.8s)
   Stage: SCHEMA_GENERATION (0.9s)
   Stage: VALIDATION (0.4s)

✅ Processing completed in 14.2s

📋 Generated Schema:
{
  "document_type": "invoice",
  "confidence_score": 0.95,
  "extracted_fields": {
    "invoice_number": "INV-2024-001",
    "total_amount": 1250.00
  }
}
```

### Unit Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Test specific components
pytest tests/test_ocr_agent.py -v
pytest tests/test_classification_agent.py -v
pytest tests/test_orchestrator.py -v
```

### Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_agents/
│   ├── test_classification_agent.py
│   ├── test_mistral_ocr_agent.py
│   ├── test_content_analysis_agent.py
│   ├── test_schema_generation_agent.py
│   └── test_validation_agent.py
├── test_orchestrator.py     # Pipeline orchestration tests
├── test_api.py              # FastAPI endpoint tests
└── test_integration.py      # End-to-end integration tests
```

### Performance Testing

```bash
# Load testing with curl and parallel processing
seq 1 10 | xargs -P 10 -I {} curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "X-API-Key: dev-key-123" \
  -F "file=@test_document.pdf"

# Memory usage monitoring
docker stats document-ingestion-agent_app_1

# Processing time benchmarks
time python test_pipeline.py large_document.pdf
```

## Deployment

### Docker Production Deployment

```bash
# Build production image
docker build -t document-agent:latest .

# Run with production configuration
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up --scale celery=3
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: document-agent
  template:
    metadata:
      labels:
        app: document-agent
    spec:
      containers:
      - name: app
        image: document-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: MISTRAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: mistral-key
        - name: REDIS_HOST
          value: redis-service
---
apiVersion: v1
kind: Service
metadata:
  name: document-agent-service
spec:
  selector:
    app: document-agent
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Environment-Specific Configuration

**Development**:
```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_API_KEY_AUTH=false
```

**Staging**:
```env
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
ENABLE_API_KEY_AUTH=true
```

**Production**:
```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
ENABLE_API_KEY_AUTH=true
MAX_UPLOAD_SIZE_MB=5
```

### Health Monitoring

**Prometheus Metrics** (`docker-compose.monitoring.yml`):
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

**Health Check Endpoint**:
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed metrics
curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/metrics
```

## Troubleshooting

### Common Issues

#### 1. Mistral API Connection Issues

**Symptoms**:
- OCR agent failures
- "API key invalid" errors
- Connection timeouts

**Solutions**:
```bash
# Verify API key
curl -H "Authorization: Bearer $MISTRAL_API_KEY" \
  https://api.mistral.ai/v1/models

# Check rate limiting
export MISTRAL_RATE_LIMIT_DELAY=2.0

# Verify network connectivity
nslookup api.mistral.ai
```

#### 2. Redis Connection Problems

**Symptoms**:
- Celery worker startup failures
- Pipeline state not persisting
- Background tasks not executing

**Solutions**:
```bash
# Check Redis connectivity
redis-cli ping

# Verify Redis is running
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Test connection
python -c "import redis; r=redis.Redis(host='localhost'); print(r.ping())"
```

#### 3. File Upload Issues

**Symptoms**:
- "File type not supported" errors
- Upload size limit exceeded
- Permission denied on upload directory

**Solutions**:
```bash
# Check allowed extensions
echo $ALLOWED_EXTENSIONS

# Verify upload directory permissions
ls -la ./uploads/
chmod 755 ./uploads/

# Check file size limits
echo "MAX_UPLOAD_SIZE_MB=$MAX_UPLOAD_SIZE_MB"

# Test with small file
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "X-API-Key: dev-key-123" \
  -F "file=@small_test.pdf"
```

#### 4. Pipeline Processing Failures

**Symptoms**:
- Documents stuck in processing
- Agent timeouts
- Validation failures

**Solutions**:
```bash
# Check agent health
curl http://localhost:8000/health

# View application logs
docker-compose logs app

# Check pipeline state
curl -H "X-API-Key: dev-key-123" \
  http://localhost:8000/api/v1/documents/{document_id}/status

# Test individual agents
python -c "
from app.agents import ClassificationAgent
agent = ClassificationAgent()
print(await agent.health_check())
"
```

#### 5. Webhook Delivery Issues

**Symptoms**:
- Webhooks not triggering
- Webhook endpoint timeouts
- Invalid webhook URLs

**Solutions**:
```bash
# Test webhook endpoint
curl -X POST "https://your-webhook-url.com/endpoint" \
  -H "Content-Type: application/json" \
  -d '{"test": "payload"}'

# Check webhook configuration
curl -H "X-API-Key: dev-key-123" \
  http://localhost:8000/api/v1/webhooks/list

# Verify webhook timeout settings
echo "WEBHOOK_TIMEOUT_SECONDS=$WEBHOOK_TIMEOUT_SECONDS"

# Use webhook.site for testing
curl -X POST "http://localhost:8000/api/v1/webhooks/register" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://webhook.site/unique-url", "webhook_name": "Test"}'
```

### Performance Optimization

#### 1. Processing Speed

```bash
# Increase Celery workers
docker-compose up --scale celery=4

# Optimize Mistral API calls
export MISTRAL_RATE_LIMIT_DELAY=0.5

# Use SSD storage for uploads
mkdir /tmp/fast-uploads
export UPLOAD_DIRECTORY=/tmp/fast-uploads
```

#### 2. Memory Usage

```bash
# Monitor memory usage
docker stats

# Limit memory per container
docker-compose.yml:
  services:
    app:
      deploy:
        resources:
          limits:
            memory: 512M
```

#### 3. Concurrent Processing

```python
# app/config.py
class Settings(BaseSettings):
    max_concurrent_jobs: int = 10
    celery_worker_concurrency: int = 4
```

### Debug Mode

Enable comprehensive debugging:

```env
DEBUG=true
LOG_LEVEL=DEBUG
MISTRAL_API_VERBOSE=true
```

**Debug Endpoints**:
```bash
# Detailed health check
curl http://localhost:8000/health?verbose=true

# Agent diagnostics
curl -H "X-API-Key: dev-key-123" \
  http://localhost:8000/api/v1/debug/agents

# Pipeline state dump
curl -H "X-API-Key: dev-key-123" \
  http://localhost:8000/api/v1/debug/pipeline/{job_id}
```

### Support and Maintenance

**Log Locations**:
- Application logs: `docker-compose logs app`
- Celery logs: `docker-compose logs celery`
- Redis logs: `docker-compose logs redis`
- System logs: `/var/log/document-agent/`

**Monitoring Checklist**:
- [ ] Health endpoint responding (`/health`)
- [ ] Redis connectivity working
- [ ] Mistral API accessible
- [ ] File upload directory writable
- [ ] Webhook endpoints reachable
- [ ] Agent processing times within limits
- [ ] Memory usage under thresholds

**Backup Strategy**:
- Document uploads: Regular filesystem backups
- Configuration: Version control `.env` templates
- Database: PostgreSQL dumps (when implemented)
- Redis state: Periodic snapshots

---

## Latest Updates

### Recent Changes (January 2025)

1. **Enhanced Documentation**: Comprehensive API documentation with detailed curl examples for all 9 endpoints
2. **Improved Architecture Diagrams**: Updated mermaid diagrams showing system components, pipeline flow, and development workflow
3. **Development Workflow**: Three flexible development modes (Hybrid, Full Docker, Dependencies Only)
4. **Configuration Management**: Pydantic V2 implementation with environment variable aliases and validation
5. **Error Handling**: Improved error responses and troubleshooting documentation
6. **Performance Monitoring**: Added metrics endpoint and health checking capabilities
7. **Webhook System**: Complete webhook management with registration, updates, and automatic triggering
8. **Testing Framework**: Comprehensive testing setup with integration tests and performance benchmarks

### Technical Improvements

- **Celery Integration**: Background task processing with Redis message broker
- **Async Processing**: Non-blocking document processing with FastAPI background tasks
- **Rate Limiting**: Intelligent API protection with configurable limits
- **File Validation**: Content type checking, size limits, and deduplication
- **Health Monitoring**: Real-time agent status and application metrics
- **Docker Development**: Multi-environment Docker configurations for different development needs

### Dependencies

- **Python 3.11+**: Modern Python features and performance improvements
- **FastAPI**: High-performance async web framework
- **Celery 5.4.0**: Distributed task queue for background processing
- **Redis 7**: Message broker and caching layer
- **Mistral AI**: Exclusive OCR provider with rate limiting
- **Pydantic V2**: Configuration management and data validation
- **Docker & Docker Compose**: Containerization and orchestration

---

**Project Status**: Production Ready ✅  
**Last Updated**: January 2025  
**Version**: 1.0.0  
**License**: MIT  

For issues, feature requests, or contributions, please refer to the project repository.