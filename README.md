# Document Ingestion Agent

An intelligent multi-agent pipeline for processing documents (PDFs, images) through 5 specialized AI agents, extracting structured data, and generating JSON schemas for webhook automation using Mistral AI OCR API.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Redis](https://img.shields.io/badge/redis-7.0+-red.svg)](https://redis.io)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Table of Contents

- [Features](#features)
- [Security](#security)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Features

- 📄 **Multi-Format Support**: Process PDFs, images, and scanned documents
- 🤖 **5-Agent Pipeline**: Classification → OCR → Analysis → Schema Generation → Validation
- 🔄 **Async Processing**: Celery-based distributed task queue with Redis
- 🏗️ **JSON Schema Generation**: Automated webhook-ready data structures
- 📊 **Real-time Status**: Track document processing through pipeline stages
- 🔌 **Webhook Integration**: Automated notifications on document completion
- 🛡️ **Enterprise Security**: Path traversal protection, DoS prevention, O(1) API key validation
- 🔧 **Admin Tools**: Stuck task management and recovery endpoints
- 📈 **Production Ready**: Docker support, health checks, metrics endpoints
- ⚡ **High Performance**: Parallel processing, Redis multi-database architecture

## Security

### Recent Security Enhancements (v2.1.0)

The application includes comprehensive security measures to protect against various attack vectors:

#### Path Traversal Protection
- **Complete Prevention**: Blocks all directory traversal attempts (`../`, `..\\`, encoded variations)
- **Pattern Detection**: Advanced pattern matching for dangerous sequences
- **Null Byte Protection**: Prevents null byte injection attacks (`\x00`)
- **Control Character Filtering**: Blocks dangerous control characters
- **Path Length Limits**: DoS prevention via extremely long paths (4096 char limit)
- **Directory Depth Limits**: Prevents deep nesting attacks (10 level max)

#### File Upload Security
- **Filename Sanitization**: Comprehensive filename validation and cleaning
- **DoS Prevention**: Streaming file size validation to prevent memory exhaustion
- **Content-Length Validation**: Pre-upload size checking
- **Secure Path Resolution**: UUID-based filenames prevent filename-based attacks
- **Multiple Validation Layers**: Filename → Extension → Path → Storage validation

#### API Security
- **O(1) API Key Validation**: High-performance authentication using hash sets
- **Rate Limiting**: Per-endpoint rate limits (uploads: 5/min, webhooks: 10/min)
- **Request Validation**: Comprehensive input sanitization
- **Security Event Logging**: Real-time attack detection and monitoring

#### Security Event Monitoring
- **Attack Detection**: Real-time logging of security violations
- **Threat Attribution**: IP address and endpoint tracking
- **Security Metrics**: Comprehensive security event categorization
- **Audit Trail**: Full security event audit logs

## Architecture

### System Overview

```mermaid
graph TB
    subgraph "Client Layer"
        C[Client Application]
    end

    subgraph "API Layer"
        A[FastAPI Server]
        RL[Rate Limiter<br/>SlowAPI]
        AUTH[API Key Auth<br/>O(1) Validation]
        SEC[Security Utils<br/>Path Validation]
    end

    subgraph "Queue Layer"
        CQ[Celery Queue<br/>Redis DB1]
        CW[Celery Workers<br/>Auto-Recovery]
        CR[Celery Results<br/>Redis DB2]
    end

    subgraph "State Management"
        RS[Redis State Manager<br/>Redis DB0]
        RRL[Rate Limit Store<br/>Redis DB3]
    end

    subgraph "Agent Pipeline"
        CA[Classification Agent<br/>Document Type ID]
        OCR[Mistral OCR Agent<br/>Text Extraction]
        AA[Content Analysis Agent<br/>Field Extraction]
        SG[Schema Generation Agent<br/>JSON Schema]
        VA[Validation Agent<br/>Quality Check]
    end

    subgraph "External Services"
        MA[Mistral AI API<br/>OCR Processing]
        WH[Webhook Endpoints<br/>Event Delivery]
    end

    subgraph "Security Layer"
        PTV[Path Traversal<br/>Protection]
        DOS[DoS Prevention<br/>File Size Limits]
        LOG[Security Logging<br/>Event Monitoring]
    end

    C -->|Upload| A
    A --> RL
    RL --> AUTH
    AUTH --> SEC
    SEC --> PTV
    SEC --> DOS
    SEC --> LOG
    SEC --> CQ
    CQ --> CW
    CW --> CA
    CA --> OCR
    OCR --> MA
    OCR --> AA
    AA --> SG
    SG --> VA
    VA --> CR
    CR --> RS
    RS --> A
    A -->|Status/Schema| C
    VA -->|Trigger| WH
    RL --> RRL
```

### Multi-Agent Pipeline Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI API
    participant Security as Security Layer
    participant Redis
    participant Celery
    participant Agents
    participant Mistral as Mistral AI

    Client->>API: POST /upload (PDF)
    API->>Security: Validate filename & path
    Security->>Security: Check traversal patterns
    Security->>Security: Sanitize & secure path
    API->>Redis: Store metadata (DB0)
    API->>Celery: Queue task (DB1)
    API-->>Client: 202 (job_id)
    
    Note over Celery,Agents: Async Pipeline Processing
    Celery->>Agents: Execute Classification
    Agents->>Agents: Document type detection
    Agents->>Security: Validate file access
    Security->>Agents: Secure file path
    Agents->>Mistral: OCR Processing
    Mistral-->>Agents: Text extraction
    Agents->>Agents: Content Analysis
    Agents->>Agents: Schema Generation
    Agents->>Agents: Validation & Quality Check
    
    Agents->>Redis: Store results (DB2)
    Agents->>Celery: Task complete
    
    Client->>API: GET /status
    API->>Redis: Fetch status (DB0)
    API-->>Client: Pipeline state
    
    Client->>API: GET /schema
    API->>Redis: Fetch schema (DB2)
    API-->>Client: JSON schema
```

### Redis Multi-Database Architecture

```mermaid
graph LR
    subgraph "Redis Instance"
        DB0[DB0: Application State<br/>- Document metadata<br/>- Job states<br/>- Pipeline status<br/>- Webhook configs]
        DB1[DB1: Celery Broker<br/>- Task queue<br/>- Message routing<br/>- Worker coordination]
        DB2[DB2: Celery Backend<br/>- Task results<br/>- Agent outputs<br/>- Processing results]
        DB3[DB3: Rate Limiting<br/>- Request counts<br/>- Time windows<br/>- IP tracking]
    end

    API[FastAPI Server] -->|Read/Write| DB0
    API -->|Rate Check| DB3
    CW[Celery Workers] -->|Consume| DB1
    CW -->|Store| DB2
    API -->|Fetch Results| DB2
    ADMIN[Admin Endpoints] -->|Monitor| DB0
    ADMIN -->|Query| DB2
```

### Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        INPUT[Input Validation]
        PATH[Path Security]
        AUTH[Authentication]
        RATE[Rate Limiting]
        LOG[Security Logging]
    end

    subgraph "Attack Prevention"
        TRAV[Path Traversal<br/>Protection]
        DOS[DoS Prevention<br/>File Size Limits]
        NULL[Null Byte<br/>Protection]
        CTRL[Control Character<br/>Filtering]
    end

    subgraph "Monitoring"
        EVT[Security Events]
        AUDIT[Audit Trail]
        ALERT[Real-time Alerts]
    end

    INPUT --> PATH
    PATH --> TRAV
    PATH --> DOS
    PATH --> NULL
    PATH --> CTRL
    AUTH --> RATE
    RATE --> LOG
    LOG --> EVT
    EVT --> AUDIT
    EVT --> ALERT
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Redis (via Docker)
- Mistral AI API Key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/document-ingestion-agent.git
cd document-ingestion-agent
```

2. **Set up environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
# Copy example config
cp .env.example .env

# Edit .env and add your Mistral API key
export MISTRAL_API_KEY=your_key_here
```

4. **Start services**
```bash
# Start Redis and Celery in Docker
docker-compose -f docker-compose.dev.yml up -d

# Start FastAPI server
./run_server.sh
```

5. **Verify installation**
```bash
# Check health
curl http://localhost:8000/health

# Should return:
{
  "status": "healthy",
  "version": "2.1.0",
  "agents": {
    "orchestrator": "healthy",
    "agents": {...}
  }
}
```

## API Documentation

### Authentication

All endpoints require API key authentication when enabled:

```bash
# Set API key in environment
export API_KEY="your-api-key"

# Include in requests
curl -H "X-API-Key: ${API_KEY}" http://localhost:8000/api/v1/...
```

### Core Endpoints

#### 1. Upload Document
**POST** `/api/v1/documents/upload`

Upload a document for processing through the multi-agent pipeline.

```bash
# Basic upload
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "X-API-Key: ${API_KEY}" \
  -F "file=@document.pdf"

# Response
{
  "job_id": "8bf38eae-0f82-4c1c-ac28-9bd9a1c52f0e",
  "document_id": "706d21f4-28e2-4233-903d-750b49f527f2",
  "message": "Document uploaded and processing started",
  "status_url": "/api/v1/documents/706d21f4-28e2-4233-903d-750b49f527f2/status"
}

# Upload with metadata
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "X-API-Key: ${API_KEY}" \
  -F "file=@invoice.pdf" \
  -F "metadata={\"source\":\"email\",\"priority\":\"high\"}"
```

**Security Features:**
- Filename sanitization and validation
- Path traversal prevention
- DoS protection with streaming size validation
- Content-Length header validation
- UUID-based secure file naming

**Rate Limit**: 5 uploads per minute per IP

#### 2. Check Processing Status
**GET** `/api/v1/documents/{document_id}/status`

Get real-time processing status for a document.

```bash
# Check status
curl -X GET "http://localhost:8000/api/v1/documents/706d21f4-28e2-4233-903d-750b49f527f2/status" \
  -H "X-API-Key: ${API_KEY}"

# Response - Processing
{
  "document_id": "706d21f4-28e2-4233-903d-750b49f527f2",
  "status": "processing",
  "file_name": "document.pdf",
  "uploaded_at": "2025-09-25T07:36:40.963266",
  "completed_at": null,
  "pipeline_state": {
    "stage": "ocr",
    "started_at": "2025-09-25T07:36:41.123456",
    "updated_at": "2025-09-25T07:36:45.789012"
  }
}

# Response - Completed
{
  "document_id": "706d21f4-28e2-4233-903d-750b49f527f2",
  "status": "completed",
  "file_name": "document.pdf",
  "uploaded_at": "2025-09-25T07:36:40.963266",
  "completed_at": "2025-09-25T07:37:32.408342",
  "pipeline_state": {
    "stage": "completed",
    "started_at": "2025-09-25T07:37:31.024821",
    "updated_at": "2025-09-25T07:37:32.408342",
    "completed_at": "2025-09-25T07:37:32.408342",
    "error": null
  }
}
```

#### 3. Get Document Schema
**GET** `/api/v1/documents/{document_id}/schema`

Retrieve the generated JSON schema for a processed document.

```bash
# Get schema
curl -X GET "http://localhost:8000/api/v1/documents/706d21f4-28e2-4233-903d-750b49f527f2/schema" \
  -H "X-API-Key: ${API_KEY}"

# Response
{
  "schema_version": "1.0",
  "schema_id": "afe37105-ce3d-475f-9f01-c310bcf16f8e",
  "document_id": "706d21f4-28e2-4233-903d-750b49f527f2",
  "document_type": "invoice",
  "timestamp": "2025-09-25T07:37:32.407941",
  "confidence_score": 0.92,
  "extracted_data": {
    "document_type": "invoice",
    "fields": {
      "invoice_number": {
        "value": "INV-2025-001",
        "confidence": 0.95,
        "location": {"page": 1, "bbox": [100, 200, 300, 250]}
      },
      "total_amount": {
        "value": 1250.00,
        "confidence": 0.88,
        "type": "currency",
        "currency": "USD"
      },
      "vendor_name": {
        "value": "Acme Corp",
        "confidence": 0.91
      }
    },
    "tables": [
      {
        "name": "line_items",
        "headers": ["Item", "Quantity", "Price", "Total"],
        "rows": [
          ["Widget A", "5", "$50.00", "$250.00"],
          ["Widget B", "10", "$100.00", "$1000.00"]
        ]
      }
    ]
  },
  "automation_triggers": [
    {
      "trigger_id": "3743ffa1-9d41-4def-b827-7958ab19a165",
      "action": "webhook",
      "endpoint": "/api/invoices/process",
      "method": "POST",
      "payload_template": {
        "invoice_number": "{{fields.invoice_number.value}}",
        "amount": "{{fields.total_amount.value}}"
      }
    }
  ]
}
```

#### 4. Register Webhook
**POST** `/api/v1/webhooks/register`

Register a webhook to receive notifications when documents are processed.

```bash
# Register webhook
curl -X POST "http://localhost:8000/api/v1/webhooks/register" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/documents",
    "events": ["document.completed", "document.failed"],
    "document_types": ["invoice", "receipt"],
    "active": true,
    "headers": {
      "Authorization": "Bearer webhook-secret-token"
    },
    "retry_config": {
      "max_retries": 3,
      "retry_delay": 60
    }
  }'

# Response
{
  "id": "wh_123456",
  "url": "https://your-app.com/webhooks/documents",
  "events": ["document.completed", "document.failed"],
  "document_types": ["invoice", "receipt"],
  "active": true,
  "created_at": "2025-09-25T08:00:00.000000"
}
```

**Rate Limit**: 10 registrations per minute per IP

#### 5. Health Check
**GET** `/health`

Check application health and component status.

```bash
# Basic health check
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "timestamp": "2025-09-25T08:00:00.000000",
  "version": "2.1.0",
  "environment": "development"
}

# Verbose health check
curl "http://localhost:8000/health?verbose=true"

# Response
{
  "status": "healthy",
  "timestamp": "2025-09-25T08:00:00.000000",
  "version": "2.1.0",
  "environment": "development",
  "agents": {
    "orchestrator": "healthy",
    "agents": {
      "classification": {
        "name": "classification_agent",
        "status": "healthy",
        "max_retries": 2,
        "timeout": 10.0
      },
      "ocr": {
        "name": "mistral_ocr_agent",
        "status": "healthy",
        "max_retries": 3,
        "timeout": 60.0,
        "api_status": "connected"
      }
    }
  },
  "redis": {
    "connected": true,
    "databases": {
      "app_state": "DB0",
      "celery_broker": "DB1", 
      "celery_results": "DB2",
      "rate_limiting": "DB3"
    }
  },
  "celery": {
    "workers": 2,
    "active_tasks": 3,
    "pending_tasks": 0
  }
}
```

#### 6. Metrics
**GET** `/api/v1/metrics`

Get application metrics and statistics.

```bash
# Get metrics
curl -X GET "http://localhost:8000/api/v1/metrics" \
  -H "X-API-Key: ${API_KEY}"

# Response
{
  "total_documents": 150,
  "completed_documents": 145,
  "failed_documents": 3,
  "processing_documents": 2,
  "registered_webhooks": 5,
  "active_jobs": 2,
  "pipeline_stats": {
    "average_processing_time": 8.5,
    "success_rate": 0.98,
    "by_document_type": {
      "invoice": 80,
      "receipt": 45,
      "contract": 20
    }
  },
  "agent_performance": {
    "ocr": {
      "average_time": 3.2,
      "success_rate": 0.99
    },
    "analysis": {
      "average_time": 2.1,
      "success_rate": 0.97
    }
  }
}
```

### Admin Endpoints

#### 7. List Stuck Tasks
**GET** `/api/v1/admin/stuck-tasks`

List all stuck or pending tasks for monitoring and recovery.

```bash
# List stuck tasks
curl -X GET "http://localhost:8000/api/v1/admin/stuck-tasks" \
  -H "X-API-Key: ${API_KEY}"

# Response
{
  "total_stuck": 3,
  "tasks": [
    {
      "document_id": "162cc67d-940a-4ea8-9166-51e23c3d348f",
      "file_name": "invoice.pdf",
      "uploaded_at": "2025-09-25T03:50:37.019653",
      "time_stuck": "4:30:15",
      "status": "processing",
      "celery_task_id": "1e31a196-39dd-49b3-8134-3a1347991966",
      "celery_status": "PENDING",
      "auto_recovered": false
    }
  ]
}
```

#### 8. Retry Stuck Task
**POST** `/api/v1/admin/retry-task/{document_id}`

Manually retry a stuck document processing task.

```bash
# Retry stuck task
curl -X POST "http://localhost:8000/api/v1/admin/retry-task/162cc67d-940a-4ea8-9166-51e23c3d348f" \
  -H "X-API-Key: ${API_KEY}"

# Response
{
  "message": "Task retried successfully",
  "document_id": "162cc67d-940a-4ea8-9166-51e23c3d348f",
  "new_task_id": "68415f4e-4dcf-4aee-9259-81f856607ad8",
  "old_task_id": "1e31a196-39dd-49b3-8134-3a1347991966"
}
```

### Webhook Management

#### 9. List Webhooks
**GET** `/api/v1/webhooks/list`

```bash
curl -X GET "http://localhost:8000/api/v1/webhooks/list" \
  -H "X-API-Key: ${API_KEY}"
```

#### 10. Update Webhook
**PUT** `/api/v1/webhooks/{webhook_id}`

```bash
curl -X PUT "http://localhost:8000/api/v1/webhooks/wh_123456" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"active": false}'
```

#### 11. Delete Webhook
**DELETE** `/api/v1/webhooks/{webhook_id}`

```bash
curl -X DELETE "http://localhost:8000/api/v1/webhooks/wh_123456" \
  -H "X-API-Key: ${API_KEY}"
```

### Error Responses

All endpoints return consistent error responses:

```bash
# 400 Bad Request
{
  "detail": "Invalid file format. Supported formats: PDF, PNG, JPG, JPEG"
}

# 401 Unauthorized
{
  "detail": "Invalid API key"
}

# 404 Not Found
{
  "detail": "Document not found"
}

# 413 Payload Too Large
{
  "detail": "File size 15.2MB exceeds 10MB limit"
}

# 429 Too Many Requests
{
  "detail": "Rate limit exceeded. Try again in 60 seconds"
}

# 500 Internal Server Error
{
  "detail": "Internal server error",
  "error_id": "err_123456",
  "timestamp": "2025-09-25T08:00:00.000000"
}
```

## Configuration

### Environment Variables

```bash
# Required
MISTRAL_API_KEY=your_mistral_api_key

# Optional - Redis Configuration
REDIS_HOST=localhost            # Default: localhost
REDIS_PORT=6379                # Default: 6379
REDIS_PASSWORD=                # Default: none
REDIS_DB=0                     # Default: 0

# Optional - API Configuration  
API_HOST=0.0.0.0              # Default: 0.0.0.0
API_PORT=8000                  # Default: 8000
API_PREFIX=/api/v1             # Default: /api/v1
API_KEY_REQUIRED=true          # Default: false
API_KEYS=key1,key2,key3       # Comma-separated list

# Optional - Security Configuration
MAX_UPLOAD_SIZE_MB=10         # Default: 10 MB
ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg
RATE_LIMIT_UPLOADS=5/minute   # Default: 5/minute
RATE_LIMIT_WEBHOOKS=10/minute # Default: 10/minute

# Optional - Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_TASK_TIME_LIMIT=300    # Default: 300 seconds
CELERY_WORKER_CONCURRENCY=2   # Default: 2

# Optional - Document Processing
UPLOAD_DIRECTORY=./uploads     # Default: ./uploads
OCR_CONFIDENCE_THRESHOLD=0.7   # Default: 0.7
VALIDATION_STRICT_MODE=true    # Default: true

# Optional - Monitoring
LOG_LEVEL=INFO                # Default: INFO
ENABLE_METRICS=true           # Default: true
SENTRY_DSN=                   # Optional Sentry integration
```

### Redis Multi-Database Setup

The application uses Redis with multiple databases for optimal performance:

- **DB0**: Application state (document metadata, job states)
- **DB1**: Celery message broker (task queue)
- **DB2**: Celery result backend (task results)
- **DB3**: Rate limiting data (slowapi)

```bash
# Redis connection examples
redis-cli -n 0  # Application state
redis-cli -n 1  # Celery broker
redis-cli -n 2  # Celery results
redis-cli -n 3  # Rate limiting
```

## Development

### Project Structure

```
document-ingestion-agent/
├── app/
│   ├── agents/                 # Multi-agent system
│   │   ├── base_agent.py      # Base agent interface
│   │   ├── classification_agent.py
│   │   ├── mistral_ocr_agent.py
│   │   ├── content_analysis_agent.py
│   │   ├── schema_generation_agent.py
│   │   ├── validation_agent.py
│   │   └── agent_orchestrator.py
│   ├── services/
│   │   └── state_manager.py   # Redis state management
│   ├── utils/
│   │   └── security.py        # Security utilities
│   ├── models/                 # Pydantic models
│   ├── main.py                 # FastAPI application
│   ├── tasks.py                # Celery tasks
│   ├── celery_app.py          # Celery configuration
│   ├── worker_signals.py      # Task recovery signals
│   └── config.py               # Settings management
├── tests/                       # Test suite
│   ├── unit/                   # Unit tests
│   │   ├── test_agents/
│   │   ├── test_services/
│   │   ├── test_security.py    # Security tests
│   │   └── test_models/
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test data
├── uploads/                     # Document storage
├── docker-compose.dev.yml      # Development environment
├── requirements.txt            # Python dependencies
├── SECURITY_FIXES.md           # Security documentation
└── README.md                   # This file
```

### Development Commands

```bash
# Run in development mode (FastAPI local, services in Docker)
./run_server.sh

# Run full Docker mode
docker-compose -f docker-compose.dev.yml up --build

# Run specific services
docker-compose -f docker-compose.dev.yml up redis  # Just Redis
docker-compose -f docker-compose.dev.yml up celery # Just Celery worker

# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# Code formatting
black app/ --line-length 100

# Linting
ruff check app/

# Type checking
mypy app/

# Run security tests
pytest tests/unit/test_security.py -v

# Generate API documentation
python -m app.generate_openapi > openapi.json
```

### Multi-Agent System

The system processes documents through 5 sequential agents:

#### 1. Classification Agent
- **Purpose**: Identify document type and validate format
- **Input**: Raw document file
- **Output**: Document type, confidence score
- **Processing Time**: ~0.5s

#### 2. Mistral OCR Agent
- **Purpose**: Extract text using Mistral AI API
- **Input**: Document file path (securely validated)
- **Output**: Extracted text, confidence scores
- **Processing Time**: ~3-5s
- **Rate Limiting**: Configurable delay between requests
- **Security**: Path traversal protection, secure file access validation

#### 3. Content Analysis Agent
- **Purpose**: Pattern-based field extraction
- **Input**: OCR text output
- **Output**: Structured fields, tables, metadata
- **Processing Time**: ~2s

#### 4. Schema Generation Agent
- **Purpose**: Create standardized JSON schemas
- **Input**: Analyzed content
- **Output**: JSON schema with automation triggers
- **Processing Time**: ~1s

#### 5. Validation Agent
- **Purpose**: Business rule validation
- **Input**: Generated schema
- **Output**: Validation status, quality score
- **Processing Time**: ~0.5s

### State Management

The system uses Redis for distributed state management:

State transitions:
```
RECEIVED → CLASSIFICATION → OCR → ANALYSIS → SCHEMA_GENERATION → VALIDATION → COMPLETED
```

### Adding a New Agent

1. **Create agent file** in `app/agents/`:
```python
from .base_agent import BaseAgent, AgentInput, AgentOutput

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="custom_agent",
            description="Custom processing agent",
            max_retries=2,
            timeout=30.0
        )
    
    async def process(
        self,
        input_data: AgentInput,
        context: AgentContext
    ) -> AgentOutput:
        # Implement processing logic
        result = await self.custom_processing(input_data)
        return AgentOutput(
            status="completed",
            data=result,
            metadata={"processing_time": 1.5}
        )
```

2. **Register in** `app/main.py`:
```python
@app.on_event("startup")
async def startup_event():
    orchestrator.register_agent("custom", CustomAgent())
```

3. **Update pipeline** in `app/agents/agent_orchestrator.py`:
```python
class PipelineStage(str, Enum):
    CLASSIFICATION = "classification"
    OCR = "ocr"
    ANALYSIS = "analysis"
    CUSTOM = "custom"  # Add new stage
    SCHEMA = "schema"
    VALIDATION = "validation"
```

## Testing

### Test Structure

```bash
tests/
├── unit/                # Unit tests
│   ├── test_agents/
│   ├── test_services/
│   ├── test_security.py # 25+ security test cases
│   └── test_models/
├── integration/         # Integration tests
│   ├── test_api.py
│   ├── test_pipeline.py
│   └── test_webhooks.py
├── performance/         # Performance tests
└── fixtures/           # Test data
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_agents/test_ocr_agent.py

# Run security tests
pytest tests/unit/test_security.py -v

# Run with markers
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Only integration tests

# Run with verbose output
pytest -v --tb=short

# Generate coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Security Testing

The project includes comprehensive security tests covering:

- **Path traversal prevention**: 15+ attack scenarios
- **Filename validation**: Dangerous pattern detection
- **File upload security**: DoS prevention, size validation
- **API security**: Rate limiting, authentication
- **Input validation**: Malicious input handling

```bash
# Run security test suite
pytest tests/unit/test_security.py::TestValidateFilename -v
pytest tests/unit/test_security.py::TestPathTraversalPrevention -v
pytest tests/unit/test_security.py::TestSecurityIntegration -v
```

### Test Examples

```python
# Test document upload
def test_document_upload(client, mock_celery):
    with open("tests/fixtures/sample.pdf", "rb") as f:
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            headers={"X-API-Key": "test-key"}
        )
    assert response.status_code == 202
    assert "job_id" in response.json()

# Test security validation
def test_path_traversal_prevention():
    with pytest.raises(PathTraversalError):
        validate_filename("../../../etc/passwd")
    
    with pytest.raises(PathTraversalError):
        validate_filename("file\x00.txt")

# Test pipeline execution
@pytest.mark.asyncio
async def test_pipeline_execution():
    orchestrator = AgentOrchestrator()
    result = await orchestrator.execute_pipeline(
        document=test_document,
        context=test_context
    )
    assert result.stage == "completed"
```

## Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in production mode
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale celery=4
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-agent-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: document-agent-api
  template:
    metadata:
      labels:
        app: document-agent-api
    spec:
      containers:
      - name: api
        image: document-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: MISTRAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: document-agent-secrets
              key: mistral-api-key
        - name: API_KEY_REQUIRED
          value: "true"
        - name: RATE_LIMIT_UPLOADS
          value: "10/minute"
```

### Production Considerations

#### Security
- **Enable API key authentication**: `API_KEY_REQUIRED=true`
- **Use HTTPS with TLS certificates**
- **Implement request signing for webhooks**
- **Rotate API keys regularly**
- **Monitor security logs for attacks**
- **Set appropriate file size limits**

#### Scaling
- **Use Redis Cluster for high availability**
- **Scale Celery workers based on load**
- **Implement horizontal pod autoscaling**
- **Use CDN for static assets**
- **Configure load balancing**

#### Monitoring
- **Set up Prometheus metrics**
- **Configure Grafana dashboards**
- **Implement distributed tracing**
- **Set up alerts for failures**
- **Monitor security events**

#### Performance
- **Enable Redis persistence**
- **Optimize worker concurrency**
- **Implement caching strategies**
- **Use connection pooling**
- **Monitor resource usage**

## Troubleshooting

### Common Issues

#### 1. Document Stuck in PENDING Status

**Problem**: Document status remains "PENDING" indefinitely

**Causes**:
- Celery workers not running
- Redis connection issues
- Task was queued before workers started

**Solutions**:
```bash
# Check if Celery workers are running
docker-compose -f docker-compose.dev.yml ps

# Start Celery workers
docker-compose -f docker-compose.dev.yml up -d celery

# List stuck tasks
curl -X GET "http://localhost:8000/api/v1/admin/stuck-tasks" \
  -H "X-API-Key: ${API_KEY}"

# Manually retry stuck task
curl -X POST "http://localhost:8000/api/v1/admin/retry-task/{document_id}" \
  -H "X-API-Key: ${API_KEY}"
```

#### 2. Redis Connection Refused

**Problem**: `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`

**Solutions**:
```bash
# Start Redis
docker-compose -f docker-compose.dev.yml up -d redis

# Verify Redis is running
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping
# Should return: PONG
```

#### 3. Security Validation Errors

**Problem**: File uploads failing with security errors

**Common Causes & Solutions**:
```bash
# Path traversal attempt
# Error: "Dangerous pattern '../' detected in filename"
# Solution: Use clean filenames without path separators

# File size too large
# Error: "File size exceeds 10MB limit"
# Solution: Increase MAX_UPLOAD_SIZE_MB or reduce file size

# Invalid filename
# Error: "Control characters detected in filename"
# Solution: Use standard ASCII characters in filenames
```

#### 4. Rate Limiting Issues

**Problem**: `429 Too Many Requests` errors

**Solutions**:
```bash
# Check rate limit status
curl -I "http://localhost:8000/api/v1/documents/upload"
# Look for X-RateLimit-* headers

# Verify Redis DB3 is accessible for rate limiting
docker-compose -f docker-compose.dev.yml exec redis redis-cli -n 3 ping

# Adjust rate limits in environment
export RATE_LIMIT_UPLOADS="10/minute"
export RATE_LIMIT_WEBHOOKS="20/minute"
```

#### 5. Mistral API Issues

**Problem**: OCR processing failures

**Solutions**:
```bash
# Test Mistral API connectivity
curl -X GET "https://api.mistral.ai/v1/models" \
  -H "Authorization: Bearer ${MISTRAL_API_KEY}"

# Check API key is set
echo $MISTRAL_API_KEY

# Verify rate limiting configuration
# Increase delay if hitting rate limits
export MISTRAL_RATE_LIMIT_DELAY=0.5
```

### Debug Commands

```bash
# View Celery worker logs
docker-compose -f docker-compose.dev.yml logs -f celery

# Monitor Redis keys
docker-compose -f docker-compose.dev.yml exec redis redis-cli monitor

# Check task queue depth
docker-compose -f docker-compose.dev.yml exec redis redis-cli -n 1 llen celery

# View FastAPI logs
tail -f logs/app.log

# Check system resources
docker stats

# Monitor security events
grep "SECURITY EVENT" logs/app.log

# Check stuck tasks count
curl -s "http://localhost:8000/api/v1/admin/stuck-tasks" | jq '.total_stuck'
```

### Security Monitoring

```bash
# Monitor security events
tail -f logs/app.log | grep "SECURITY EVENT"

# Check for path traversal attempts
grep "PATH_TRAVERSAL_ATTEMPT" logs/app.log

# Monitor dangerous filename attempts
grep "DANGEROUS_FILENAME_ATTEMPT" logs/app.log

# Check rate limiting effectiveness
curl -s "http://localhost:8000/api/v1/metrics" | jq '.rate_limiting'
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests (including security tests if applicable)
5. Run quality checks
6. Submit a pull request

### Code Style

- Follow PEP 8
- Use Black for formatting (`black app/ --line-length 100`)
- Add type hints
- Write docstrings
- Keep functions small and focused
- Add security considerations to code reviews

### Security Guidelines

- **Never bypass security validations**
- **Always use secure path utilities** for file operations
- **Test security features thoroughly**
- **Document security implications** of changes
- **Review security logs** during development

### Commit Messages

Follow conventional commits:
```
feat: add new OCR provider support
fix: resolve memory leak in agent pipeline  
security: implement path traversal protection
docs: update API examples
test: add integration tests for webhooks
refactor: simplify state management
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: This README
- **Issues**: [GitHub Issues](https://github.com/yourusername/document-ingestion-agent/issues)
- **Security Issues**: Please report security vulnerabilities privately
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/document-ingestion-agent/discussions)

## Acknowledgments

- **Mistral AI** for OCR capabilities
- **FastAPI** framework for the API layer
- **Celery** distributed task queue
- **Redis** for state management and caching
- **Security Community** for vulnerability disclosure and testing
- **The open-source community** for continuous improvement

---

**Built with ❤️ and 🔒 by the Document Ingestion Agent Team**

*Last updated: September 25, 2025 | Version 2.1.0*