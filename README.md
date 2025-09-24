# Document Ingestion Agent

An intelligent multi-agent pipeline for processing multi-media documents (PDFs, images) through specialized AI agents, extracting structured data, and generating standardized JSON schemas for webhook and API automation.

## Table of Contents
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [API Documentation](#api-documentation)
- [Multi-Agent System](#multi-agent-system)
- [Pipeline Flow](#pipeline-flow)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## Features

- **Multi-Format Support**: Process PDFs, images (PNG, JPG, TIFF, BMP)
- **5-Agent Architecture**: Specialized agents for classification, OCR, analysis, schema generation, and validation
- **Mistral AI OCR Integration**: Exclusive OCR provider for accurate text extraction
- **Async Processing**: Non-blocking document processing with Celery
- **Webhook Automation**: Automatic webhook triggers upon completion
- **Docker Development**: Hybrid development with Docker dependencies
- **Health Monitoring**: Real-time agent health checks
- **Schema Generation**: Standardized JSON output for automation
- **Rate Limiting**: Intelligent rate limiting for API protection
- **Retry Logic**: Automatic retry with exponential backoff

## Architecture Overview

### System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Client[Client Application]
        Webhook[Webhook Consumer]
    end
    
    subgraph "API Layer"
        FastAPI[FastAPI Server<br/>Port 8000]
        Auth[API Key Auth]
    end
    
    subgraph "Processing Layer"
        Orchestrator[Agent Orchestrator]
        subgraph "5-Agent Pipeline"
            CA[Classification Agent]
            OA[Mistral OCR Agent]
            AA[Content Analysis Agent]
            SA[Schema Generation Agent]
            VA[Validation Agent]
        end
    end
    
    subgraph "Infrastructure Layer"
        Redis[(Redis Cache<br/>Port 6379)]
        Celery[Celery Worker]
        Storage[File Storage]
    end
    
    Client -->|Upload Document| FastAPI
    FastAPI --> Auth
    Auth --> Orchestrator
    Orchestrator --> CA
    CA -->|Document Type| OA
    OA -->|Extracted Text| AA
    AA -->|Parsed Fields| SA
    SA -->|JSON Schema| VA
    VA -->|Validated Data| Orchestrator
    Orchestrator --> Redis
    Orchestrator --> Celery
    Celery --> Storage
    Orchestrator -->|Trigger| Webhook
    
    style FastAPI fill:#4CAF50
    style Orchestrator fill:#2196F3
    style Redis fill:#DC382D
    style OA fill:#FF9800
```

### Pipeline State Flow

```mermaid
stateDiagram-v2
    [*] --> RECEIVED: Document Upload
    RECEIVED --> CLASSIFICATION: Start Pipeline
    CLASSIFICATION --> OCR: Document Classified
    OCR --> ANALYSIS: Text Extracted
    ANALYSIS --> SCHEMA_GENERATION: Fields Parsed
    SCHEMA_GENERATION --> VALIDATION: Schema Created
    VALIDATION --> COMPLETED: Validation Passed
    VALIDATION --> FAILED: Validation Failed
    COMPLETED --> [*]: Success
    FAILED --> [*]: Error
    
    note right of OCR: Mistral AI OCR API
    note right of VALIDATION: Business Rules Check
    note right of COMPLETED: Webhook Triggered
```

### Development Architecture

```mermaid
graph LR
    subgraph "Local Machine"
        subgraph "Python Environment"
            FastAPI[FastAPI<br/>Hot Reload<br/>Port 8000]
        end
        
        subgraph "Docker Containers"
            Redis[Redis<br/>Port 6379]
            Celery[Celery Worker<br/>Mounted Code]
        end
    end
    
    subgraph "External"
        Mistral[Mistral AI API]
    end
    
    FastAPI <-->|localhost:6379| Redis
    FastAPI <-->|Task Queue| Celery
    Celery <-->|Redis Protocol| Redis
    FastAPI -->|HTTPS| Mistral
    Celery -->|HTTPS| Mistral
    
    style FastAPI fill:#4CAF50
    style Redis fill:#DC382D
    style Celery fill:#9C27B0
    style Mistral fill:#FF9800
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Mistral API Key

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/document-ingestion-agent.git
cd document-ingestion-agent

# Copy environment template
cp .env.example .env

# Edit .env and add your Mistral API key
nano .env  # Set MISTRAL_API_KEY=your-key-here
```

### 2. Start the Application

```bash
# Start with hybrid development mode (recommended)
./run_server.sh

# OR start with full Docker mode
docker-compose up --build
```

The API will be available at `http://localhost:8000`

### 3. Quick Test

```bash
# Check health
curl http://localhost:8000/health

# Upload a document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@sample.pdf"
```

## Development Setup

### Development Modes

#### 1. Hybrid Mode (Recommended)
FastAPI runs locally with hot reload, dependencies in Docker:

```bash
./run_server.sh
```

**Benefits:**
- Hot reload for FastAPI changes
- No local Redis/Celery installation needed
- Docker handles dependencies
- Automatic cleanup on exit

#### 2. Full Docker Mode
Everything runs in containers:

```bash
docker-compose up --build
```

**Benefits:**
- Production-like environment
- Complete isolation
- Multi-service orchestration

#### 3. Dependencies Only Mode
Start only Docker dependencies, run FastAPI manually:

```bash
# Start dependencies
./scripts/start-docker-deps.sh

# In another terminal
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# When done
./scripts/stop-docker-deps.sh
```

**Benefits:**
- Full control over FastAPI startup
- Better for debugging
- Custom launch configurations

### Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| Redis | 6379 | Cache and message broker |
| Celery | N/A | Background task processing |
| FastAPI | 8000 | REST API server |
| Flower | 5555 | Celery monitoring (optional) |
| PostgreSQL | 5432 | Database (optional) |

## API Documentation

### Interactive Documentation
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

### Authentication
All API endpoints (except `/health`) require API key authentication:

```bash
-H "X-API-Key: your-api-key"
```

### Complete API Endpoints

#### 1. Upload Document
**POST** `/api/v1/documents/upload`

Upload a document for processing through the multi-agent pipeline.

```bash
# Basic upload
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@invoice.pdf"

# With metadata
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@receipt.jpg" \
  -F "metadata={\"source\":\"mobile\",\"user_id\":\"12345\"}"

# With webhook callback
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@contract.pdf" \
  -F "webhook_url=https://your-app.com/webhook" \
  -F "webhook_secret=your-webhook-secret"
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Document uploaded successfully",
  "estimated_completion": "2024-01-20T10:30:00Z"
}
```

#### 2. Check Processing Status
**GET** `/api/v1/documents/{document_id}/status`

Get the current processing status of a document.

```bash
# Check status
curl -X GET http://localhost:8000/api/v1/documents/550e8400-e29b-41d4-a716-446655440000/status \
  -H "X-API-Key: your-api-key"

# With verbose details
curl -X GET "http://localhost:8000/api/v1/documents/550e8400-e29b-41d4-a716-446655440000/status?verbose=true" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "stage": "VALIDATION",
  "progress": 100,
  "stages_completed": [
    "CLASSIFICATION",
    "OCR",
    "ANALYSIS",
    "SCHEMA_GENERATION",
    "VALIDATION"
  ],
  "processing_time": 12.5,
  "document_type": "invoice",
  "confidence_score": 0.95
}
```

#### 3. Get Generated Schema
**GET** `/api/v1/documents/{document_id}/schema`

Retrieve the generated JSON schema for a processed document.

```bash
# Get schema
curl -X GET http://localhost:8000/api/v1/documents/550e8400-e29b-41d4-a716-446655440000/schema \
  -H "X-API-Key: your-api-key"

# Pretty printed
curl -X GET http://localhost:8000/api/v1/documents/550e8400-e29b-41d4-a716-446655440000/schema \
  -H "X-API-Key: your-api-key" | python -m json.tool
```

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "invoice",
  "extracted_data": {
    "invoice_number": "INV-2024-001",
    "date": "2024-01-20",
    "vendor": "Acme Corp",
    "total_amount": 1500.00,
    "line_items": [
      {
        "description": "Professional Services",
        "quantity": 10,
        "unit_price": 150.00,
        "total": 1500.00
      }
    ],
    "tax_rate": 0.08,
    "tax_amount": 120.00,
    "grand_total": 1620.00
  },
  "confidence_scores": {
    "overall": 0.95,
    "fields": {
      "invoice_number": 0.99,
      "date": 0.98,
      "total_amount": 0.97
    }
  },
  "validation_status": "passed",
  "processing_metadata": {
    "ocr_model": "mistral-ocr-latest",
    "processing_time": 12.5,
    "timestamp": "2024-01-20T10:30:00Z"
  }
}
```

#### 4. Register Webhook
**POST** `/api/v1/webhooks/register`

Register a webhook endpoint to receive notifications.

```bash
# Register basic webhook
curl -X POST http://localhost:8000/api/v1/webhooks/register \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["document.processed", "document.failed"],
    "active": true
  }'

# With authentication
curl -X POST http://localhost:8000/api/v1/webhooks/register \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["document.processed"],
    "active": true,
    "secret": "webhook-secret-key",
    "headers": {
      "Authorization": "Bearer your-webhook-token"
    }
  }'

# With retry configuration
curl -X POST http://localhost:8000/api/v1/webhooks/register \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["document.processed", "document.failed"],
    "active": true,
    "max_retries": 5,
    "retry_delay": 60
  }'
```

**Response:**
```json
{
  "webhook_id": "wh_123456",
  "url": "https://your-app.com/webhook",
  "events": ["document.processed", "document.failed"],
  "active": true,
  "created_at": "2024-01-20T10:00:00Z"
}
```

#### 5. List Webhooks
**GET** `/api/v1/webhooks/list`

List all registered webhooks.

```bash
# List all webhooks
curl -X GET http://localhost:8000/api/v1/webhooks/list \
  -H "X-API-Key: your-api-key"

# Filter by active status
curl -X GET "http://localhost:8000/api/v1/webhooks/list?active=true" \
  -H "X-API-Key: your-api-key"

# Pagination
curl -X GET "http://localhost:8000/api/v1/webhooks/list?page=1&limit=10" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "webhooks": [
    {
      "webhook_id": "wh_123456",
      "url": "https://your-app.com/webhook",
      "events": ["document.processed"],
      "active": true,
      "created_at": "2024-01-20T10:00:00Z",
      "last_triggered": "2024-01-20T10:30:00Z",
      "success_count": 15,
      "failure_count": 1
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

#### 6. Update Webhook
**PUT** `/api/v1/webhooks/{webhook_id}`

Update an existing webhook configuration.

```bash
# Update webhook URL
curl -X PUT http://localhost:8000/api/v1/webhooks/wh_123456 \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://new-endpoint.com/webhook"
  }'

# Disable webhook
curl -X PUT http://localhost:8000/api/v1/webhooks/wh_123456 \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "active": false
  }'

# Update events and secret
curl -X PUT http://localhost:8000/api/v1/webhooks/wh_123456 \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "events": ["document.processed", "document.failed", "document.validated"],
    "secret": "new-secret-key"
  }'
```

**Response:**
```json
{
  "webhook_id": "wh_123456",
  "message": "Webhook updated successfully",
  "updated_fields": ["url", "active", "events", "secret"]
}
```

#### 7. Delete Webhook
**DELETE** `/api/v1/webhooks/{webhook_id}`

Delete a webhook registration.

```bash
# Delete webhook
curl -X DELETE http://localhost:8000/api/v1/webhooks/wh_123456 \
  -H "X-API-Key: your-api-key"

# Force delete (skip confirmation)
curl -X DELETE "http://localhost:8000/api/v1/webhooks/wh_123456?force=true" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "message": "Webhook deleted successfully",
  "webhook_id": "wh_123456"
}
```

#### 8. Health Check
**GET** `/health`

Check the health status of the application and all agents.

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl "http://localhost:8000/health?detailed=true"

# With timeout
curl --max-time 5 http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:00:00Z",
  "version": "2.0.0",
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
        "timeout": 60.0
      },
      "analysis": {
        "name": "content_analysis_agent",
        "status": "healthy",
        "max_retries": 2,
        "timeout": 30.0
      },
      "schema": {
        "name": "schema_generation_agent",
        "status": "healthy",
        "max_retries": 2,
        "timeout": 20.0
      },
      "validation": {
        "name": "validation_agent",
        "status": "healthy",
        "max_retries": 2,
        "timeout": 15.0
      }
    }
  },
  "dependencies": {
    "redis": "connected",
    "mistral_api": "reachable"
  }
}
```

#### 9. Metrics
**GET** `/api/v1/metrics`

Get application metrics and statistics.

```bash
# Get all metrics
curl -X GET http://localhost:8000/api/v1/metrics \
  -H "X-API-Key: your-api-key"

# Filter by time range
curl -X GET "http://localhost:8000/api/v1/metrics?start_date=2024-01-01&end_date=2024-01-31" \
  -H "X-API-Key: your-api-key"

# Specific metric type
curl -X GET "http://localhost:8000/api/v1/metrics?type=processing_times" \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "metrics": {
    "total_documents_processed": 1523,
    "success_rate": 0.97,
    "average_processing_time": 8.5,
    "documents_by_type": {
      "invoice": 650,
      "receipt": 430,
      "contract": 280,
      "form": 163
    },
    "agent_performance": {
      "classification_agent": {
        "success_rate": 0.99,
        "avg_time": 0.5
      },
      "mistral_ocr_agent": {
        "success_rate": 0.96,
        "avg_time": 3.2
      },
      "content_analysis_agent": {
        "success_rate": 0.97,
        "avg_time": 2.1
      },
      "schema_generation_agent": {
        "success_rate": 0.98,
        "avg_time": 1.5
      },
      "validation_agent": {
        "success_rate": 0.99,
        "avg_time": 1.2
      }
    },
    "error_distribution": {
      "ocr_failure": 15,
      "validation_error": 20,
      "timeout": 5,
      "unknown": 8
    },
    "peak_usage_hour": "14:00",
    "daily_average": 51
  },
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  }
}
```

### Webhook Payload Examples

When a document is processed, the registered webhook receives:

```json
{
  "event": "document.processed",
  "timestamp": "2024-01-20T10:30:00Z",
  "document": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "invoice",
    "status": "completed"
  },
  "data": {
    "invoice_number": "INV-2024-001",
    "vendor": "Acme Corp",
    "total_amount": 1500.00,
    "date": "2024-01-20"
  },
  "metadata": {
    "processing_time": 8.5,
    "confidence_score": 0.95,
    "ocr_model": "mistral-ocr-latest"
  }
}
```

## Multi-Agent System

### Agent Descriptions

| Agent | Responsibility | Timeout | Retries |
|-------|---------------|---------|---------|
| **ClassificationAgent** | Identifies document type and format | 10s | 2 |
| **MistralOCRAgent** | Extracts text using Mistral AI OCR | 60s | 3 |
| **ContentAnalysisAgent** | Pattern-based field extraction | 30s | 2 |
| **SchemaGenerationAgent** | Creates standardized JSON schemas | 20s | 2 |
| **ValidationAgent** | Business rule validation | 15s | 2 |

### Agent Implementation Pattern

All agents inherit from `BaseAgent`:

```python
class BaseAgent:
    async def execute(self, input_data: Dict) -> AgentResult
    async def health_check(self) -> HealthStatus
    def get_retry_policy(self) -> RetryPolicy
```

## Pipeline Flow

### Document Processing Workflow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant O as Orchestrator
    participant CA as Classification
    participant OCR as Mistral OCR
    participant AA as Analysis
    participant SA as Schema Gen
    participant VA as Validation
    participant W as Webhook
    
    C->>API: Upload Document
    API->>O: Start Pipeline
    O->>CA: Classify Document
    CA-->>O: Document Type
    O->>OCR: Extract Text
    OCR-->>O: Raw Text
    O->>AA: Analyze Content
    AA-->>O: Parsed Fields
    O->>SA: Generate Schema
    SA-->>O: JSON Schema
    O->>VA: Validate Data
    VA-->>O: Validation Result
    O->>W: Trigger Webhook
    O-->>API: Processing Complete
    API-->>C: Response
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Application Settings
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=development

# Server Settings
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Mistral OCR API Configuration (REQUIRED)
MISTRAL_API_KEY=your-mistral-api-key-here
MISTRAL_OCR_MODEL=mistral-ocr-latest
MISTRAL_RATE_LIMIT=60

# File Processing
MAX_FILE_SIZE=52428800  # 50MB in bytes
SUPPORTED_FILE_TYPES=.pdf,.png,.jpg,.jpeg,.tiff,.bmp
UPLOAD_DIRECTORY=/tmp/document-uploads

# Processing Settings
MAX_CONCURRENT_DOCUMENTS=5
PROCESSING_TIMEOUT=300

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Database Configuration (Optional)
DATABASE_URL=postgresql://user:password@localhost/document_agent

# Security Settings
API_KEY_REQUIRED=false
API_KEY=your-secure-api-key-here
ALLOWED_ORIGINS=*

# Webhook Settings
WEBHOOK_TIMEOUT=10
WEBHOOK_RETRY_ATTEMPTS=3
WEBHOOK_SECRET=your-webhook-secret-here

# Monitoring
ENABLE_METRICS=true
ENABLE_TRACING=false

# Cost Optimization
ENABLE_NATIVE_PDF_DETECTION=true
OCR_CONFIDENCE_THRESHOLD=0.7
```

### Pydantic V2 Configuration

The application uses Pydantic V2 with field aliases for environment variable mapping:

```python
class Settings(BaseSettings):
    # Maps HOST env var to both host and api_host attributes
    host: str = Field(default="0.0.0.0", alias="HOST")
    api_host: str = Field(default="0.0.0.0", alias="HOST")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",  # Ignores unknown env vars
    }
```

## Testing

### Unit Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_ocr_agent.py -v
```

### Integration Testing
```bash
# Test document upload
python test_pipeline.py samples/invoice.pdf

# Test with custom document
python test_pipeline.py path/to/document.pdf
```

### Load Testing
```bash
# Using Apache Bench
ab -n 100 -c 10 -T "multipart/form-data" \
   -H "X-API-Key: your-api-key" \
   http://localhost:8000/api/v1/documents/upload

# Using curl in loop
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/documents/upload \
    -H "X-API-Key: your-api-key" \
    -F "file=@sample.pdf" &
done
```

## Deployment

### Production with Docker

```bash
# Build production image
docker build -t document-agent:latest .

# Run with environment file
docker run -d \
  --name document-agent \
  --env-file .env.production \
  -p 8000:8000 \
  document-agent:latest
```

### Docker Compose Production

```yaml
version: '3.8'
services:
  app:
    image: document-agent:latest
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    depends_on:
      - redis
      - postgres
    restart: always
```

### Kubernetes Deployment

```yaml
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
      - name: document-agent
        image: document-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: MISTRAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: mistral-key
```

## Troubleshooting

### Common Issues

#### 1. Docker Not Running
```bash
Error: Docker daemon is not running
```
**Solution**: Start Docker Desktop or run `sudo systemctl start docker`

#### 2. Port Already in Use
```bash
Error: bind: address already in use
```
**Solution**: 
```bash
# Find process using port
lsof -i :8000
# Kill process or change port in .env
```

#### 3. Mistral API Key Missing
```bash
Error: MISTRAL_API_KEY environment variable is not set
```
**Solution**: Add your API key to `.env` file

#### 4. Redis Connection Refused
```bash
Error: Cannot connect to Redis
```
**Solution**: 
```bash
# Check Redis container
docker-compose -f docker-compose.dev.yml ps
docker-compose -f docker-compose.dev.yml logs redis
```

#### 5. Celery Worker Not Processing
**Solution**: 
```bash
# Check Celery logs
docker-compose -f docker-compose.dev.yml logs celery
# Restart Celery
docker-compose -f docker-compose.dev.yml restart celery
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG

# Or via environment
DEBUG=true LOG_LEVEL=DEBUG ./run_server.sh
```

### Performance Optimization

1. **Increase Workers**: Set `WORKERS=8` for more concurrent processing
2. **Redis Memory**: Configure Redis max memory in docker-compose.yml
3. **Celery Concurrency**: Adjust `--concurrency` flag in Celery command
4. **Rate Limiting**: Adjust `MISTRAL_RATE_LIMIT` for API throttling

## Performance Benchmarks

| Document Type | Avg Processing Time | Success Rate |
|--------------|-------------------|--------------|
| Invoice (1 page) | 5-8 seconds | 97% |
| Receipt | 3-5 seconds | 98% |
| Contract (10 pages) | 30-45 seconds | 95% |
| Form | 8-12 seconds | 96% |

## Security Features

- **API Key Authentication**: Required for all endpoints except health
- **Rate Limiting**: Configurable per-endpoint limits
- **Input Validation**: File type and size restrictions
- **Webhook Secrets**: HMAC signature validation
- **Environment Isolation**: Docker containers for dependencies
- **Secure File Handling**: Temporary file cleanup

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/document-ingestion-agent/issues)
- **Documentation**: This README
- **API Reference**: http://localhost:8000/api/v1/docs

## Acknowledgments

- Mistral AI for OCR capabilities
- FastAPI framework
- Redis for caching
- Celery for async processing
- Docker for containerization

---
*Document Ingestion Agent v2.0.0 - Intelligent Document Processing Pipeline*