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
- **Redis State Management**: Multi-database Redis configuration for state, queuing, and rate limiting
- **Docker Development**: Hybrid development modes with containerized dependencies
- **Health Monitoring**: Real-time agent health checks and application metrics
- **Schema Generation**: Standardized JSON output for automation triggers
- **Rate Limiting**: Intelligent API protection and throttling with Redis backend
- **Retry Logic**: Automatic retry with exponential backoff for fault tolerance
- **API Authentication**: Secure API key-based authentication with header binding fix
- **File Validation**: Content type checking, size limits, and deduplication

## Architecture Overview

### System Architecture

```mermaid
graph TB
    subgraph ClientLayer ["Client Layer"]
        Client[Client Application]
        WebhookConsumer[Webhook Consumer]
        Docs[API Documentation]
    end
    
    subgraph APILayer ["API Gateway Layer"]
        FastAPI[FastAPI Server Port 8000]
        Auth[API Key Authentication]
        CORS[CORS Middleware]
        RateLimit[Rate Limiting with Redis DB3]
    end
    
    subgraph ProcessingLayer ["Processing Layer"]
        Orchestrator[Agent Orchestrator]
        CeleryWorkers[Celery Workers]
        TaskQueue[Redis Message Broker]
        
        subgraph AgentPipeline ["5-Agent Pipeline"]
            CA[Classification Agent]
            OA[Mistral OCR Agent]
            AA[Content Analysis Agent]
            SA[Schema Generation Agent]
            VA[Validation Agent]
        end
    end
    
    subgraph DataLayer ["Data Layer"]
        Redis[(Redis Multi-DB)]
        RedisDB0[DB0 State Management]
        RedisDB1[DB1 Celery Broker]
        RedisDB2[DB2 Task Results]
        RedisDB3[DB3 Rate Limiting]
        Storage[File Storage]
    end
    
    subgraph ExternalServices ["External Services"]
        MistralAPI[Mistral AI OCR API]
        WebhookURLs[External Webhook Endpoints]
    end
    
    Client --> FastAPI
    FastAPI --> Auth
    FastAPI --> CORS
    FastAPI --> RateLimit
    Auth --> Orchestrator
    
    Orchestrator --> TaskQueue
    TaskQueue --> CeleryWorkers
    CeleryWorkers --> CA
    CA --> OA
    OA --> MistralAPI
    OA --> AA
    AA --> SA
    SA --> VA
    
    Orchestrator --> Redis
    Redis --> RedisDB0
    Redis --> RedisDB1
    Redis --> RedisDB2
    Redis --> RedisDB3
    Orchestrator --> Storage
    Orchestrator --> WebhookURLs
    
    style FastAPI fill:#4CAF50
    style Orchestrator fill:#2196F3
    style Redis fill:#DC382D
    style OA fill:#FF9800
    style MistralAPI fill:#FF6B35
    style CeleryWorkers fill:#9C27B0
```

### Pipeline State Flow

```mermaid
stateDiagram-v2
    [*] --> RECEIVED
    RECEIVED --> CLASSIFICATION
    CLASSIFICATION --> OCR
    OCR --> ANALYSIS
    ANALYSIS --> SCHEMA_GENERATION
    SCHEMA_GENERATION --> VALIDATION
    VALIDATION --> COMPLETED
    VALIDATION --> FAILED
    COMPLETED --> [*]
    FAILED --> [*]
    
    CLASSIFICATION --> FAILED
    OCR --> FAILED
    ANALYSIS --> FAILED
    SCHEMA_GENERATION --> FAILED
    
    RECEIVED : Document Upload POST /upload
    CLASSIFICATION : Document Type Identification
    OCR : Mistral AI Text Extraction
    ANALYSIS : Fields Extracted & Parsed
    SCHEMA_GENERATION : JSON Schema Generated
    VALIDATION : Business Rules Check
    COMPLETED : Webhook Triggered
    FAILED : Error Response
```

### Redis State Management Architecture

```mermaid
graph LR
    subgraph RedisInstance ["Redis Server Port 6379"]
        DB0[DB0 - Application State<br/>Document metadata<br/>Pipeline states]
        DB1[DB1 - Celery Broker<br/>Task queue<br/>Message routing]
        DB2[DB2 - Task Results<br/>Processing outcomes<br/>Agent responses]
        DB3[DB3 - Rate Limiting<br/>API throttling<br/>Request counters]
    end
    
    subgraph Applications ["Application Layer"]
        FastAPI[FastAPI Server]
        CeleryWorker[Celery Workers]
        StateManager[State Manager Service]
    end
    
    FastAPI --> DB0
    FastAPI --> DB3
    CeleryWorker --> DB1
    CeleryWorker --> DB2
    StateManager --> DB0
    
    style DB0 fill:#E3F2FD
    style DB1 fill:#FFF3E0
    style DB2 fill:#E8F5E8
    style DB3 fill:#FCE4EC
    style FastAPI fill:#4CAF50
    style CeleryWorker fill:#9C27B0
    style StateManager fill:#2196F3
```

### Development Workflow

```mermaid
flowchart LR
    subgraph LocalDev ["Local Development"]
        Code[Source Code]
        App[FastAPI App localhost:8000]
        Tests[pytest Tests]
    end
    
    subgraph DockerDeps ["Docker Dependencies"]
        Redis[Redis Container Port 6379]
        CeleryWorker[Celery Worker Container]
    end
    
    subgraph ExtServices ["External Services"]
        Mistral[Mistral AI API]
        Webhooks[Test Webhooks]
    end
    
    Code --> App
    App --> Redis
    App --> CeleryWorker
    App --> Mistral
    App --> Webhooks
    Tests --> App
    
    style App fill:#4CAF50
    style Redis fill:#DC382D
    style CeleryWorker fill:#9C27B0
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
# Required
MISTRAL_API_KEY=your_mistral_api_key_here

# Optional (with defaults)
API_HOST=0.0.0.0
API_PORT=8000
REDIS_HOST=localhost
REDIS_PORT=6379

# Database Configuration (Optional - Redis is used for state management by default)
# DATABASE_URL=postgresql://user:password@localhost/dbname

# Rate Limiting (Optional)
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REDIS_DB=3
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
docker-compose -f docker-compose.dev.yml up --build
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

Check processing status and pipeline progress for a document using Celery task tracking.

**Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/documents/doc-uuid-here/status" \
  -H "X-API-Key: your-api-key" \
  -H "Accept: application/json"
```

**Response** (200 OK) - Processing:
```json
{
  "document_id": "doc-uuid-here",
  "status": "processing",
  "file_name": "invoice.pdf",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "celery_status": "PROGRESS",
  "pipeline_state": {
    "stage": "ocr",
    "started_at": "2024-01-15T10:30:01Z",
    "updated_at": "2024-01-15T10:31:45Z",
    "progress": "Extracting text from document...",
    "error": null
  },
  "error": null
}
```

**Response** (200 OK) - Completed:
```json
{
  "document_id": "doc-uuid-here",
  "status": "completed",
  "file_name": "invoice.pdf",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:32:15Z",
  "celery_status": "SUCCESS",
  "pipeline_state": {
    "stage": "completed",
    "started_at": "2024-01-15T10:30:01Z",
    "updated_at": "2024-01-15T10:32:15Z",
    "completed_at": "2024-01-15T10:32:15Z",
    "error": null
  },
  "processing_time_seconds": 135.2,
  "error": null
}
```

**Status Values**:
- `processing`: Document uploaded, Celery task running
- `completed`: Successfully processed through all agents
- `failed`: Error occurred during processing

**Celery Status Values**:
- `PENDING`: Task not yet started or unknown
- `PROGRESS`: Task is currently running
- `SUCCESS`: Task completed successfully
- `FAILURE`: Task failed with error
- `RETRY`: Task is being retried after failure

**Pipeline Stages**:
- `RECEIVED`: Document uploaded and queued
- `CLASSIFICATION`: Identifying document type and format
- `OCR`: Extracting text via Mistral AI OCR API
- `ANALYSIS`: Parsing fields and extracting structured data
- `SCHEMA_GENERATION`: Creating standardized JSON schema
- `VALIDATION`: Business rules validation and quality checks
- `COMPLETED`: Ready for retrieval and webhook delivery

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

**Rate Limits**: 10 requests per minute per IP (when rate limiting enabled)

**Request with JSON body (recommended)**:
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/register" \
  -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://webhook.site/unique-url",
    "webhook_name": "Test Webhook",
    "events": ["document.processed"]
  }'
```

**Request with query parameters (alternative)**:
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/register?webhook_url=https://webhook.site/unique-url&webhook_name=Test%20Webhook&events=document.processed" \
  -H "X-API-Key: dev-key-123"
```

**Full example with multiple events**:
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

**Response** (200 OK):
```json
{
  "webhook_id": "webhook-uuid-here",
  "message": "Webhook registered successfully"
}
```

**Error Responses**:
```json
// Invalid API key (401)
{
  "detail": "Invalid API key"
}

// Missing webhook_url (422)
{
  "detail": [
    {
      "loc": ["query", "webhook_url"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
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
    "extracted_fields": { "..." },
    "validation_results": { "..." }
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

**Note**: Current implementation uses query parameters instead of JSON body.

**Request**:
```bash
curl -X PUT "http://localhost:8000/api/v1/webhooks/webhook-uuid-here?webhook_url=https://new-endpoint.yourapp.com/webhook&active=false" \
  -H "X-API-Key: your-api-key"
```

**Disable webhook only**:
```bash
curl -X PUT "http://localhost:8000/api/v1/webhooks/webhook-uuid-here?active=false" \
  -H "X-API-Key: dev-key-123"
```

**Update URL only**:
```bash
curl -X PUT "http://localhost:8000/api/v1/webhooks/webhook-uuid-here?webhook_url=https://new-endpoint.com/webhook" \
  -H "X-API-Key: dev-key-123"
```

**Using JSON body (alternative format)**:
```bash
curl -X PUT "http://localhost:8000/api/v1/webhooks/webhook-uuid-here" \
  -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://new-endpoint.com/webhook",
    "active": false
  }'
```

**Response** (200 OK):
```json
{
  "webhook_id": "webhook-uuid-here",
  "message": "Webhook updated successfully"
}
```

**Error Responses**:
```json
// Webhook not found (404)
{
  "detail": "Webhook not found"
}

// Invalid API key (401)
{
  "detail": "Invalid API key"
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

System health check with agent status and application information. **No authentication required**.

**Basic health check**:
```bash
curl -X GET "http://localhost:8000/health" \
  -H "Accept: application/json"
```

**Verbose health check with detailed information**:
```bash
curl -X GET "http://localhost:8000/health?verbose=true" \
  -H "Accept: application/json"
```

**Check specific components**:
```bash
# Check Redis connectivity
curl -X GET "http://localhost:8000/health?verbose=true&check_redis=true"

# Check Celery workers
curl -X GET "http://localhost:8000/health?verbose=true&check_celery=true"
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
      "api_status": "connected",
      "rate_limit_status": "ok"
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
  },
  "infrastructure": {
    "redis": {
      "status": "healthy",
      "databases": {
        "db0": "connected",
        "db1": "connected", 
        "db2": "connected",
        "db3": "connected"
      },
      "memory_usage": "2.1MB"
    },
    "celery": {
      "status": "healthy",
      "active_workers": 2,
      "queued_tasks": 0,
      "failed_tasks": 0
    },
    "rate_limiter": {
      "status": "enabled",
      "requests_per_minute": 45,
      "blocked_requests": 0
    }
  }
}
```

**Error Response** (503 Service Unavailable):
```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-15T10:45:30Z",
  "version": "1.0.0",
  "environment": "development",
  "agents": {
    "ocr": {
      "status": "unhealthy",
      "last_check": "2024-01-15T10:45:29Z",
      "error": "Mistral API connection failed"
    }
  }
}
```

### 9. Application Metrics

**Endpoint**: `GET /api/v1/metrics`

Retrieve application performance metrics and statistics. **Authentication required**.

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
  "active_jobs": 2
}
```

**Response with no documents processed** (200 OK):
```json
{
  "total_documents": 0,
  "completed_documents": 0,
  "failed_documents": 0,
  "processing_documents": 0,
  "registered_webhooks": 0,
  "active_jobs": 0
}
```

**Error Responses**:
```json
// Invalid API key (401)
{
  "detail": "Invalid API key"
}

// API key authentication disabled but required (401)
{
  "detail": "Invalid API key"
}
```

**Metrics Explanation**:
- `total_documents`: Total number of documents uploaded since server start
- `completed_documents`: Documents successfully processed through all pipeline stages
- `failed_documents`: Documents that failed at any pipeline stage
- `processing_documents`: Documents currently being processed (calculated as total - completed - failed)
- `registered_webhooks`: Number of webhook registrations (active and inactive)
- `active_jobs`: Number of pipeline states currently tracked in memory

**Note**: Additional metrics like uptime tracking and processing time averages can be implemented by extending the metrics endpoint in `app/main.py`.

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
docker-compose -f docker-compose.dev.yml up --build

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

# Redis Configuration (Multi-Database Setup)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0                    # Default database for general state
REDIS_PASSWORD=               # Optional Redis password

# Celery Configuration (uses Redis DB1 and DB2)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_TASK_TIME_LIMIT=300
CELERY_TASK_SOFT_TIME_LIMIT=270

# Rate Limiting (uses Redis DB3)
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REDIS_DB=3
RATE_LIMIT_DEFAULT_LIMITS=200 per minute,1000 per hour

# Database (Optional - Redis is now primary state management)
# DATABASE_URL=postgresql://user:password@localhost/document_agent

# File Processing
MAX_UPLOAD_SIZE_MB=10
ALLOWED_EXTENSIONS=.pdf,.png,.jpg,.jpeg,.tiff,.bmp
UPLOAD_DIRECTORY=./uploads
MAX_CONCURRENT_DOCUMENTS=5
PROCESSING_TIMEOUT=300

# Mistral AI Configuration
MISTRAL_API_URL=https://api.mistral.ai/v1/chat/completions
MISTRAL_RATE_LIMIT_DELAY=1.0
OCR_CONFIDENCE_THRESHOLD=0.7

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

# Security
ENABLE_NATIVE_PDF_DETECTION=true
VALIDATION_STRICT_MODE=true
MAX_PAGES_PER_DOCUMENT=10
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

## Celery Task Processing

### Overview

The Document Ingestion Agent uses Celery for distributed task processing, enabling:
- **Async Document Processing**: Non-blocking API responses with background pipeline execution
- **Scalable Workers**: Multiple Celery workers can process documents in parallel
- **Automatic Retries**: Failed tasks retry with exponential backoff
- **Task Monitoring**: Real-time task status tracking via Redis backend

### Architecture Components

#### Celery Application (`app/celery_app.py`)
```python
# Redis Configuration
broker: redis://redis:6379/1  # Message queue
backend: redis://redis:6379/2  # Result storage
```

#### Task Definitions (`app/tasks.py`)
- `process_document_task`: Main pipeline execution with agent orchestration
- `trigger_webhooks_task`: Async webhook delivery with failure handling
- `health_check_task`: Worker health verification

### Task Flow

1. **Document Upload** → FastAPI receives file
2. **Task Queuing** → Document processing queued to Celery via Redis
3. **Worker Execution** → Celery worker runs pipeline through agents
4. **Result Storage** → Task results stored in Redis backend
5. **Status Queries** → API retrieves status from Redis

### Starting Celery Workers

```bash
# Development (with Docker)
docker-compose -f docker-compose.dev.yml up celery

# Production
celery -A app.celery_app worker --loglevel=info --concurrency=4

# With Flower monitoring
celery -A app.celery_app flower --port=5555
```

### Monitoring Tasks

```bash
# Check worker status
celery -A app.celery_app inspect active

# View scheduled tasks
celery -A app.celery_app inspect scheduled

# Monitor in real-time
celery -A app.celery_app events

# Web UI (if Flower is running)
open http://localhost:5555
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

### Celery Task Queue Architecture

**Files**: `app/celery_app.py`, `app/tasks.py`

**Purpose**: Asynchronous background processing for document pipeline execution

**Key Features**:
- **Redis Message Broker**: Uses Redis databases 1 & 2 for broker and result backend
- **Task Routing**: Automatic task distribution to available Celery workers
- **Retry Logic**: Configurable retry attempts with exponential backoff
- **Result Persistence**: Task results stored in Redis with 1-hour expiration
- **Webhook Integration**: Automatic webhook triggering upon completion

#### Celery Configuration

**File**: `app/celery_app.py`
```python
celery_app = Celery(
    "document_agent",
    broker=f"redis://{redis_host}:{redis_port}/1",
    backend=f"redis://{redis_host}:{redis_port}/2",
    include=["app.tasks"]
)

# Key Configuration:
- Task time limit: 5 minutes (hard), 4.5 minutes (soft)
- Result expiration: 1 hour
- Worker prefetch: 1 task at a time
- JSON serialization for cross-platform compatibility
```

#### Task Definitions

**File**: `app/tasks.py`

**Primary Tasks**:
1. **`process_document_task`**: Main pipeline execution
   - Instantiates agent orchestrator with all 5 agents
   - Handles async-to-sync conversion for Celery compatibility
   - Automatic retry on failure (max 3 attempts)
   - Triggers webhooks on successful completion

2. **`trigger_webhooks_task`**: Webhook delivery
   - Sends processed schema to registered webhook URLs
   - Handles HTTP timeouts and retries
   - Tracks delivery success/failure metrics

3. **`health_check_task`**: Worker health verification
   - Simple connectivity test for Celery workers
   - Used by monitoring systems

#### Integration with FastAPI

**Modified**: `app/main.py`
- Document upload endpoints now queue Celery tasks instead of direct processing
- Non-blocking API responses with job tracking
- Status endpoint queries Celery task results
- Background task monitoring and health checks

#### Development Workflow

**Hybrid Development Mode** (`docker-compose.dev.yml`):
```yaml
services:
  celery:
    command: celery -A app.celery_app worker --loglevel=info --concurrency=2
    volumes:
      - ./app:/app/app  # Hot reload for development
```

**Production Mode**:
- Multiple Celery workers for horizontal scaling
- Persistent Redis configuration for task durability
- Health checks and restart policies

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

#### 5. Celery Worker Not Starting

**Symptoms**:
- Error: `The module app.celery_app was not found`
- Celery worker fails to start
- Background task processing not working

**Root Cause**:
- Missing `app/celery_app.py` file
- Incorrect module imports

**Solution**:
The project now includes the required Celery configuration files:
- `app/celery_app.py`: Celery application configuration
- `app/tasks.py`: Task definitions for document processing

If you still encounter issues:
```bash
# Verify files exist
ls -la app/celery_app.py app/tasks.py

# Check Celery worker logs
docker-compose -f docker-compose.dev.yml logs celery

# Restart Celery worker
docker-compose -f docker-compose.dev.yml restart celery

# Test Celery connection
docker-compose -f docker-compose.dev.yml exec celery celery -A app.celery_app inspect ping
```

#### 6. Redis Memory Overcommit Warning

**Symptoms**:
- Warning: `WARNING Memory overcommit must be enabled!`
- Appears in Redis container logs
- May cause background save failures under memory pressure

**Note**: This is an informational warning in Docker environments and doesn't prevent Redis from functioning.

**Solutions**:

**Option 1: Fix on Host System (Recommended for Production)**
```bash
# Set memory overcommit on host
sudo sysctl vm.overcommit_memory=1

# Make permanent
echo "vm.overcommit_memory = 1" | sudo tee -a /etc/sysctl.conf

# Verify setting
sysctl vm.overcommit_memory
```

**Option 2: Ignore for Development**
The warning doesn't affect development functionality. Redis will work normally despite the warning.

**Option 3: Use Different Redis Configuration**
```yaml
# In docker-compose.dev.yml
redis:
  command: redis-server --save "" --appendonly no  # Disable persistence
```

#### 7. Rate Limiting Issues

**Symptoms**:
- "Rate limit exceeded" error responses
- 429 Too Many Requests status
- Slowapi connection errors

**Solutions**:
```bash
# Check rate limiting status
curl -X GET "http://localhost:8000/health?verbose=true" | jq '.infrastructure.rate_limiter'

# Verify Redis DB3 connectivity
redis-cli -n 3 ping

# Check current rate limit counters
redis-cli -n 3 KEYS "*"

# Disable rate limiting temporarily
export RATE_LIMIT_ENABLED=false

# Adjust rate limits
export RATE_LIMIT_DEFAULT_LIMITS="500 per minute,5000 per hour"
```

#### 8. Redis Multi-Database Issues

**Symptoms**:
- State not persisting across requests
- Celery tasks not processing
- Rate limiting not working

**Solutions**:
```bash
# Check all Redis databases
for db in {0..3}; do
  echo "DB$db:"
  redis-cli -n $db info keyspace
done

# Verify database connections
python -c "
import redis
for db in range(4):
    try:
        r = redis.Redis(host='localhost', port=6379, db=db)
        print(f'DB{db}: {r.ping()}')
    except Exception as e:
        print(f'DB{db}: ERROR - {e}')
"

# Clear specific database if corrupted
redis-cli -n 3 FLUSHDB  # Clear rate limiting data

# Monitor Redis commands
redis-cli monitor
```

#### 9. Webhook Delivery Issues

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
- [ ] Redis multi-database connectivity (DB0-DB3)
- [ ] Celery workers running and processing tasks
- [ ] Rate limiting functioning properly
- [ ] Mistral API accessible and within rate limits
- [ ] File upload directory writable
- [ ] Webhook endpoints reachable and responding
- [ ] Agent processing times within limits
- [ ] Memory usage under thresholds
- [ ] State persistence across API calls
- [ ] Background task queue processing

**Backup Strategy**:
- Document uploads: Regular filesystem backups
- Configuration: Version control `.env` templates
- Database: PostgreSQL dumps (when implemented)
- Redis state: Periodic snapshots

---

## Latest Updates

## Developer Guide (Claude Code Instructions)

This section provides guidance for Claude Code (claude.ai/code) and developers working with this repository.

### Key Implementation Details

#### Agent Base Class Pattern
All agents inherit from `BaseAgent` (app/agents/base_agent.py) which provides:
- Async execution with `execute()` method
- Automatic retry logic with exponential backoff
- Health check capabilities
- Standardized error handling
- Metrics collection hooks

#### Mistral OCR Integration
The `MistralOCRAgent` (app/agents/mistral_ocr_agent.py) is the exclusive OCR provider:
- Handles rate limiting with configurable delay
- Implements intelligent retry logic
- Supports both PDF and image formats
- Uses httpx for async HTTP requests

#### State Management
- In-memory state storage for development (dictionaries in main.py)
- Production should use Redis or PostgreSQL (models not yet implemented)
- Pipeline states tracked in `PipelineState` objects

### File Structure Patterns

- **Agents**: All in `app/agents/` directory, inherit from `base_agent.py`
- **Configuration**: Centralized in `app/config.py` using Pydantic Settings
- **API Routes**: All in `app/main.py` (consider splitting if it grows)
- **Docker**: `docker-compose.yml` for full stack, `Dockerfile` for app image
- **Celery Tasks**: `app/tasks.py` for async processing, `app/celery_app.py` for configuration

### Common Development Tasks

#### Adding a New Agent
1. Create new file in `app/agents/`
2. Inherit from `BaseAgent`
3. Implement `async def process()` method
4. Register in `AgentOrchestrator` in `app/main.py` startup event

#### Modifying Pipeline Flow
1. Update `PipelineStage` enum in `agent_orchestrator.py`
2. Modify `execute_pipeline()` method to add new stage
3. Update agent registration in `startup_event()`

#### Adding New Document Type
1. Update classification patterns in `ClassificationAgent`
2. Add extraction logic in `ContentAnalysisAgent`
3. Define schema template in `SchemaGenerationAgent`
4. Add validation rules in `ValidationAgent`

### Code Quality Commands

```bash
# Format code
black app/ --line-length 100

# Lint code
ruff check app/

# Type checking
mypy app/

# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_ocr_agent.py -v
```

### Testing Individual Components

```bash
# Test the pipeline with sample document
python test_pipeline.py

# Test with specific document
python test_pipeline.py path/to/document.pdf

# Test specific endpoint
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "X-API-Key: test-key-1" \
  -F "file=@sample.pdf"
```

### Recent Changes (September 2025)

#### Latest Implementation Updates

**1. Redis State Management System**
- **New File**: `app/services/state_manager.py` - Comprehensive Redis-based state management
- **Multi-Database Architecture**: Separate Redis databases for different purposes:
  - DB0: Application state and document metadata
  - DB1: Celery message broker and task queue
  - DB2: Task results and processing outcomes
  - DB3: Rate limiting counters and API throttling
- **Shared State**: Cross-process communication between FastAPI and Celery workers
- **TTL Management**: Automatic expiration of documents (24h) and job states (1h)

**2. Webhook JSON Body Support**
- **New File**: `app/models/webhook_models.py` - Pydantic models for webhook handling
- **Enhanced Registration**: Support for both JSON body and query parameter formats
- **Model Validation**: Structured webhook registration, updates, and responses
- **Event Subscriptions**: Flexible event filtering for webhook deliveries

**3. Rate Limiting with slowapi**
- **Integration**: Added slowapi for Redis-backed rate limiting
- **Configuration**: 200 requests/minute, 1000/hour default limits
- **Redis Backend**: Uses Redis DB3 for distributed rate limiting
- **Per-IP Throttling**: Automatic IP-based request throttling and blocking

**4. Celery Status Integration**
- **AsyncResult Tracking**: Real-time Celery task status in API responses
- **Enhanced Status Endpoint**: Now includes Celery task states (PENDING, PROGRESS, SUCCESS, FAILURE)
- **Progress Tracking**: Detailed pipeline stage progression with timestamps
- **Error Handling**: Improved error reporting with task failure details

**5. API Authentication Fix**
- **Header Binding**: Fixed X-API-Key header dependency injection
- **Consistent Auth**: Proper authentication across all protected endpoints
- **Error Responses**: Clear 401 Unauthorized responses for invalid keys

**6. Verbose Health Check**
- **Detailed Monitoring**: Added verbose parameter for comprehensive health information
- **Infrastructure Status**: Redis multi-database connectivity checks
- **Celery Health**: Worker status, queue length, and failure counts
- **Rate Limiter Status**: Current request rates and blocked request counters

**7. Configuration Enhancements**
- **DATABASE_URL Optional**: Redis now primary state management, PostgreSQL optional
- **Environment Variables**: New Redis-specific configuration options
- **Rate Limiting Config**: Configurable rate limits and Redis database selection

#### Mermaid Diagram Fixes & Documentation Enhancements
1. **Fixed Mermaid Syntax Issues**: Resolved "Could not find a suitable point for the given distance" errors
   - Fixed complex node labels with line breaks causing rendering failures
   - Simplified connection syntax in system architecture diagram
   - Updated pipeline state flow diagram with cleaner state definitions
   - Added new Redis State Management Architecture diagram

2. **Comprehensive API Documentation**: Complete curl examples for all 9 endpoints
   - Added detailed error response examples for every endpoint
   - Updated webhook registration to show JSON body as recommended approach
   - Enhanced status endpoint documentation with Celery integration
   - Added rate limiting information to relevant endpoints
   - Included verbose health check examples with infrastructure monitoring

#### Current Implementation Status
3. **Celery Task Queue System**: Fully implemented with Redis message broker
   - `app/celery_app.py`: Redis broker (DB1) and backend (DB2) configuration
   - `app/tasks.py`: Document processing, webhook triggering, and health check tasks
   - `app/main.py`: API endpoints using Celery task queuing instead of background tasks
   - Automatic retry logic with exponential backoff (max 3 retries)

4. **Redis State Management**: Multi-database configuration
   - Database 0: General caching and application state
   - Database 1: Celery message broker queue
   - Database 2: Celery task results backend

5. **API Endpoint Implementation**: All 9 endpoints fully functional
   - Document upload with Celery task queuing
   - Status monitoring with pipeline state tracking
   - Schema retrieval for completed documents
   - Complete webhook CRUD operations (register, list, update, delete)
   - Health check with agent status monitoring
   - Application metrics with processing statistics

#### Architecture & Configuration
6. **Multi-Agent Pipeline**: 5-agent architecture fully implemented
   - ClassificationAgent: Document type identification
   - MistralOCRAgent: Exclusive OCR provider with rate limiting
   - ContentAnalysisAgent: Pattern-based field extraction
   - SchemaGenerationAgent: Standardized JSON schema creation
   - ValidationAgent: Business rules validation

7. **Configuration Management**: Pydantic V2 with environment variables
   - Comprehensive settings in `app/config.py`
   - Docker development modes (Hybrid, Full Docker, Dependencies Only)
   - Environment-specific configuration templates

8. **Development & Deployment**: Production-ready setup
   - Docker Compose configurations for development and production
   - Kubernetes deployment manifests
   - Health monitoring and metrics collection
   - Comprehensive troubleshooting documentation

### Technical Improvements

**Current Implementation Features**:
- **Celery Task Processing**: Distributed background processing with Redis message broker
- **Multi-Database Redis**: Separate databases for caching (DB0), broker (DB1), and results (DB2)
- **Async Pipeline Execution**: Non-blocking document processing through 5-agent architecture
- **Intelligent Rate Limiting**: Mistral API rate limiting with exponential backoff retry logic
- **Comprehensive File Validation**: MIME type checking, size limits, and SHA-256 deduplication
- **Real-Time Health Monitoring**: Agent status checking with detailed error reporting
- **Flexible Development Modes**: Hybrid, Full Docker, and Dependencies-Only configurations
- **Production-Ready Deployment**: Docker Compose and Kubernetes configurations
- **Complete API Coverage**: 9 endpoints with authentication, webhooks, and metrics

### Dependencies & Technology Stack

**Core Framework**:
- **Python 3.11+**: Modern async features and performance improvements
- **FastAPI**: High-performance async web framework with automatic OpenAPI documentation
- **Celery 5.4.0**: Distributed task queue with Redis broker and result backend
- **Redis 7**: Multi-database data store (state management, message broker, results, rate limiting)
- **Pydantic V2**: Data validation, serialization, and configuration management with Settings

**AI & Processing**:
- **Mistral AI**: Exclusive OCR provider with intelligent rate limiting and retry logic
- **httpx**: Async HTTP client for external API calls and webhook delivery

**State Management & Caching**:
- **Redis Multi-Database**: Separated concerns across DB0-DB3
- **State Manager Service**: Cross-process communication between FastAPI and Celery
- **TTL Management**: Automatic expiration of temporary data

**API & Security**:
- **slowapi**: Redis-backed rate limiting and API throttling
- **CORS Middleware**: Cross-origin resource sharing configuration
- **API Key Authentication**: Header-based authentication with dependency injection

**Infrastructure**:
- **Docker & Docker Compose**: Multi-environment containerization and orchestration
- **uvicorn**: ASGI server for FastAPI application
- **python-multipart**: File upload handling for multipart/form-data requests

**Development & Testing**:
- **pytest**: Testing framework with async support and coverage reporting
- **pytest-asyncio**: Async test support for pipeline testing
- **pytest-httpx**: HTTP client mocking for API tests
- **mypy**: Static type checking for code quality
- **black**: Code formatting and style enforcement
- **ruff**: Fast Python linter for code quality checks

**Monitoring & Logging**:
- **prometheus-client**: Metrics collection and monitoring
- **python-json-logger**: Structured logging for better debugging

---

**Project Status**: Production Ready ✅  
**Last Updated**: September 2025 (Latest Implementation Updates)  
**Version**: 1.0.0  
**License**: MIT  

**Latest Architecture Features**:
- ✅ Redis Multi-Database State Management (DB0-DB3)
- ✅ Rate Limiting with slowapi and Redis Backend
- ✅ Webhook JSON Body Support with Pydantic Models
- ✅ Celery AsyncResult Status Tracking Integration
- ✅ Verbose Health Check with Infrastructure Monitoring
- ✅ Fixed Mermaid Diagrams and Enhanced Documentation

**Quick Start Commands**:
```bash
# Start development environment with Redis multi-database
docker-compose -f docker-compose.dev.yml up -d

# Run server with rate limiting and state management
./run_server.sh

# Test the complete pipeline with new features
python test_pipeline.py

# Check comprehensive API documentation
open http://localhost:8000/api/v1/docs

# Monitor health with verbose infrastructure status
curl "http://localhost:8000/health?verbose=true"

# Test rate limiting and webhook registration
curl -X POST "http://localhost:8000/api/v1/webhooks/register" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://webhook.site/test", "webhook_name": "Test"}'
```

**File Structure Summary**:
- `app/services/state_manager.py` - Redis state management service
- `app/models/webhook_models.py` - Webhook Pydantic models  
- `app/main.py` - Updated with rate limiting and AsyncResult integration
- `app/config.py` - Enhanced configuration with Redis multi-database support
- `requirements.txt` - Added slowapi for rate limiting

For issues, feature requests, or contributions, please refer to the project repository.