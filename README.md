# Document Ingestion Agent 📄🤖

An intelligent, production-ready agentic pipeline for multi-media document processing that automatically extracts, classifies, and transforms documents into structured JSON schemas for webhook and API automation triggers.

## 🎯 Overview

This system implements a sophisticated multi-agent architecture that processes PDF and image documents through a series of specialized agents, each responsible for a specific aspect of document understanding. The pipeline uses **Mistral OCR API exclusively** for text extraction and generates actionable JSON schemas that can trigger downstream automations.

## 🏗️ System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        A[Document Upload] 
        B[API Client]
    end
    
    subgraph "API Layer"
        C[FastAPI Server]
        D[Authentication]
        E[Rate Limiting]
    end
    
    subgraph "Processing Pipeline"
        F[Agent Orchestrator]
        G[Classification Agent]
        H[Mistral OCR Agent]
        I[Content Analysis Agent]
        J[Schema Generation Agent]
        K[Validation Agent]
    end
    
    subgraph "Storage Layer"
        L[(PostgreSQL)]
        M[(Redis Cache)]
        N[File Storage]
    end
    
    subgraph "Integration Layer"
        O[Webhook Manager]
        P[API Triggers]
        Q[Event Bus]
    end
    
    A --> C
    B --> C
    C --> D
    D --> E
    E --> F
    
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
    K --> O
    
    F -.-> L
    F -.-> M
    F -.-> N
    
    O --> P
    O --> Q
    
    style F fill:#f96,stroke:#333,stroke-width:4px
    style H fill:#9cf,stroke:#333,stroke-width:2px
```

### Detailed Component Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Orchestrator
    participant Classification
    participant OCR
    participant Analysis
    participant Schema
    participant Validation
    participant Webhook
    
    Client->>API: POST /documents/upload
    API->>API: Validate & Store File
    API->>Orchestrator: Start Pipeline
    API-->>Client: 202 Accepted (job_id)
    
    Orchestrator->>Classification: Identify Document Type
    Classification-->>Orchestrator: Type & Confidence
    
    Orchestrator->>OCR: Extract Text (Mistral API)
    OCR-->>Orchestrator: Extracted Text & Metadata
    
    Orchestrator->>Analysis: Parse Content
    Analysis-->>Orchestrator: Structured Fields
    
    Orchestrator->>Schema: Generate JSON Schema
    Schema-->>Orchestrator: Schema & Triggers
    
    Orchestrator->>Validation: Validate Data
    Validation-->>Orchestrator: Validation Results
    
    Orchestrator->>Webhook: Trigger Automations
    Webhook-->>External: POST to Endpoints
    
    Client->>API: GET /documents/{id}/status
    API-->>Client: Processing Status
    
    Client->>API: GET /documents/{id}/schema
    API-->>Client: JSON Schema Result
```

### Agent Architecture

The system employs a **5-Agent Architecture** with clear separation of concerns:

1. **Classification Agent** 🏷️
   - Identifies document type (invoice, receipt, contract, form)
   - Validates file format and MIME type
   - Provides initial confidence scoring
   - Routes documents to appropriate processing paths

2. **Mistral OCR Agent** 🔍
   - Exclusive integration with Mistral AI OCR API
   - Handles both PDF and image processing
   - Implements intelligent rate limiting and retry logic
   - Performs digital text extraction for PDFs (skips OCR when possible)
   - Provides page-level confidence scoring

3. **Content Analysis Agent** 📊
   - Pattern-based field extraction
   - Document-specific parsing logic
   - Table detection and extraction
   - Cross-field relationship analysis
   - Multi-language support ready

4. **Schema Generation Agent** 🔧
   - Creates standardized JSON schemas
   - Maps extracted data to automation triggers
   - Implements version control for schemas
   - Generates webhook payloads
   - Supports conditional trigger logic

5. **Validation Agent** ✅
   - Business rule validation
   - Data quality assessment
   - Cross-field validation
   - Confidence threshold enforcement
   - Generates improvement suggestions

### Base Agent Framework

All agents inherit from a robust base class providing:
- Async execution support
- Standardized error handling
- Automatic retry logic with exponential backoff
- Metrics collection
- Health check capabilities
- Timeout management

## 📋 Features

### Core Capabilities

- **Multi-Format Support**: PDF, PNG, JPG, JPEG, TIFF, BMP
- **Intelligent OCR**: Automatically detects digital vs scanned PDFs
- **Document Classification**: Automatic categorization with confidence scoring
- **Field Extraction**: Pattern-based extraction for common document types
- **Table Processing**: Structured data extraction from tables
- **Schema Generation**: Dynamic JSON schema creation with versioning
- **Validation Framework**: Comprehensive data quality checks
- **Webhook Automation**: Conditional trigger system for downstream actions

### Production Features

- **Scalability**: Async processing with Celery task queue
- **Reliability**: Circuit breakers, retry logic, and dead letter queues
- **Observability**: Prometheus metrics, structured logging, distributed tracing
- **Security**: API key authentication, input sanitization, rate limiting
- **Performance**: Redis caching, connection pooling, batch processing
- **Extensibility**: Modular agent design for easy customization

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Redis
- PostgreSQL (optional, for production)
- Mistral AI API Key

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/document-ingestion-agent.git
cd document-ingestion-agent

# Set your Mistral API key
export MISTRAL_API_KEY="your-mistral-api-key"

# Start the services
docker-compose up --build
```

#### Option 2: Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MISTRAL_API_KEY="your-mistral-api-key"
export REDIS_HOST="localhost"
export DATABASE_URL="postgresql://user:password@localhost/document_agent"

# Run the application
./run_server.sh
```

### Quick Start

1. **Start the server**:
```bash
./run_server.sh
```

2. **Upload a document**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@invoice.pdf"
```

3. **Check processing status**:
```bash
curl "http://localhost:8000/api/v1/documents/{document_id}/status" \
  -H "X-API-Key: your-api-key"
```

4. **Retrieve JSON schema**:
```bash
curl "http://localhost:8000/api/v1/documents/{document_id}/schema" \
  -H "X-API-Key: your-api-key"
```

## 📚 API Documentation

### Complete API Endpoints with CURL Examples

#### 1. Upload Document
```http
POST /api/v1/documents/upload
```

**CURL Example**:
```bash
# Upload a PDF invoice
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@invoice.pdf"

# Upload a PNG receipt
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@receipt.png"

# Upload with verbose output
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@contract.pdf" \
  -v | jq '.'
```

**Response** (202 Accepted):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Document uploaded and processing started",
  "status_url": "/api/v1/documents/123e4567/status"
}
```

#### 2. Get Processing Status
```http
GET /api/v1/documents/{document_id}/status
```

**CURL Examples**:
```bash
# Check status with document ID
curl -X GET "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/status" \
  -H "X-API-Key: your-api-key"

# Check status with pretty print
curl -X GET "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/status" \
  -H "X-API-Key: your-api-key" | jq '.'

# Poll status until completed (bash script)
DOCUMENT_ID="123e4567-e89b-12d3-a456-426614174000"
while true; do
  STATUS=$(curl -s -X GET "http://localhost:8000/api/v1/documents/$DOCUMENT_ID/status" \
    -H "X-API-Key: your-api-key" | jq -r '.status')
  echo "Status: $STATUS"
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 2
done
```

**Response** (200 OK):
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "file_name": "invoice.pdf",
  "uploaded_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:00:30Z",
  "pipeline_state": {
    "stage": "completed",
    "started_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:30Z"
  }
}
```

#### 3. Get Document Schema
```http
GET /api/v1/documents/{document_id}/schema
```

**CURL Examples**:
```bash
# Get document schema
curl -X GET "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/schema" \
  -H "X-API-Key: your-api-key"

# Save schema to file
curl -X GET "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/schema" \
  -H "X-API-Key: your-api-key" \
  -o schema_output.json

# Extract specific fields using jq
curl -X GET "http://localhost:8000/api/v1/documents/123e4567-e89b-12d3-a456-426614174000/schema" \
  -H "X-API-Key: your-api-key" | jq '.extracted_data.structured.amounts'
```

**Response** (200 OK):
```json
{
  "schema_version": "1.0",
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "document_type": "invoice",
  "confidence_score": 0.92,
  "extracted_data": {
    "structured": {
      "invoice_details": {
        "number": "INV-2024-001",
        "date": "01/15/2024",
        "due_date": "02/15/2024"
      },
      "vendor": {
        "name": "Acme Corp",
        "tax_id": "12-3456789"
      },
      "amounts": {
        "subtotal": 1000.00,
        "tax": 100.00,
        "total": 1100.00
      },
      "line_items": [
        {
          "description": "Product A",
          "quantity": 10,
          "price": 50.00,
          "total": 500.00
        }
      ]
    }
  },
  "automation_triggers": [
    {
      "trigger_id": "abc123",
      "action": "webhook",
      "endpoint": "/api/invoices/high-value",
      "method": "POST",
      "condition": {
        "total_amount": {"$gte": 1000}
      }
    }
  ],
  "validation_status": "passed"
}
```

### Webhook Management Endpoints

#### 4. Register Webhook
```http
POST /api/v1/webhooks/register
```

**CURL Examples**:
```bash
# Register a webhook for invoice processing
curl -X POST "http://localhost:8000/api/v1/webhooks/register" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://your-app.com/webhook/invoice",
    "webhook_name": "Invoice Processor",
    "events": ["document.processed", "document.validated"]
  }'

# Register webhook with minimal configuration
curl -X POST "http://localhost:8000/api/v1/webhooks/register" \
  -H "X-API-Key: your-api-key" \
  -G \
  --data-urlencode "webhook_url=https://your-app.com/webhook" \
  --data-urlencode "webhook_name=Document Handler"

# Register webhook for high-value invoices
curl -X POST "http://localhost:8000/api/v1/webhooks/register" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://accounting.example.com/high-value",
    "webhook_name": "High Value Invoice Alert",
    "events": ["invoice.high_value"],
    "conditions": {"total_amount": {"$gte": 10000}}
  }'
```

**Response** (200 OK):
```json
{
  "webhook_id": "wh_123e4567-e89b-12d3-a456-426614174000",
  "message": "Webhook registered successfully"
}
```

#### 5. List Webhooks
```http
GET /api/v1/webhooks/list
```

**CURL Examples**:
```bash
# List all webhooks
curl -X GET "http://localhost:8000/api/v1/webhooks/list" \
  -H "X-API-Key: your-api-key"

# List webhooks with formatting
curl -X GET "http://localhost:8000/api/v1/webhooks/list" \
  -H "X-API-Key: your-api-key" | jq '.webhooks[] | {id: .id, name: .name, url: .url, active: .active}'

# Count active webhooks
curl -X GET "http://localhost:8000/api/v1/webhooks/list" \
  -H "X-API-Key: your-api-key" | jq '[.webhooks[] | select(.active == true)] | length'
```

**Response** (200 OK):
```json
{
  "webhooks": [
    {
      "id": "wh_123e4567",
      "name": "Invoice Processor",
      "url": "https://your-app.com/webhook",
      "events": ["document.processed"],
      "created_at": "2024-01-15T10:00:00Z",
      "active": true
    }
  ],
  "total": 1
}
```

#### 6. Update Webhook
```http
PUT /api/v1/webhooks/{webhook_id}
```

**CURL Examples**:
```bash
# Update webhook URL
curl -X PUT "http://localhost:8000/api/v1/webhooks/wh_123e4567" \
  -H "X-API-Key: your-api-key" \
  -G \
  --data-urlencode "webhook_url=https://new-endpoint.com/webhook"

# Deactivate webhook
curl -X PUT "http://localhost:8000/api/v1/webhooks/wh_123e4567" \
  -H "X-API-Key: your-api-key" \
  -G \
  --data-urlencode "active=false"

# Update multiple fields
curl -X PUT "http://localhost:8000/api/v1/webhooks/wh_123e4567" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://updated.example.com/webhook",
    "active": true,
    "events": ["document.processed", "document.failed"]
  }'
```

**Response** (200 OK):
```json
{
  "webhook_id": "wh_123e4567",
  "message": "Webhook updated successfully"
}
```

#### 7. Delete Webhook
```http
DELETE /api/v1/webhooks/{webhook_id}
```

**CURL Examples**:
```bash
# Delete webhook by ID
curl -X DELETE "http://localhost:8000/api/v1/webhooks/wh_123e4567" \
  -H "X-API-Key: your-api-key"

# Delete with confirmation
curl -X DELETE "http://localhost:8000/api/v1/webhooks/wh_123e4567" \
  -H "X-API-Key: your-api-key" \
  -v

# Delete and verify deletion
WEBHOOK_ID="wh_123e4567"
curl -X DELETE "http://localhost:8000/api/v1/webhooks/$WEBHOOK_ID" \
  -H "X-API-Key: your-api-key" && \
curl -X GET "http://localhost:8000/api/v1/webhooks/list" \
  -H "X-API-Key: your-api-key" | jq ".webhooks[] | select(.id == \"$WEBHOOK_ID\")"
```

**Response** (200 OK):
```json
{
  "message": "Webhook deleted successfully"
}
```

### Health & Monitoring Endpoints

#### 8. Health Check
```http
GET /health
```

**CURL Examples**:
```bash
# Basic health check
curl -X GET "http://localhost:8000/health"

# Health check with response time
curl -X GET "http://localhost:8000/health" -w "\nResponse time: %{time_total}s\n"

# Monitor health status continuously
watch -n 5 'curl -s http://localhost:8000/health | jq .status'

# Check agent health details
curl -X GET "http://localhost:8000/health" | jq '.agents'
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "version": "1.0.0",
  "environment": "development",
  "agents": {
    "orchestrator": "healthy",
    "agents": {
      "classification": {"status": "healthy"},
      "ocr": {"status": "healthy"},
      "analysis": {"status": "healthy"},
      "schema": {"status": "healthy"},
      "validation": {"status": "healthy"}
    }
  }
}
```

#### 9. Metrics
```http
GET /api/v1/metrics
```

**CURL Examples**:
```bash
# Get system metrics
curl -X GET "http://localhost:8000/api/v1/metrics" \
  -H "X-API-Key: your-api-key"

# Monitor processing rate
curl -X GET "http://localhost:8000/api/v1/metrics" \
  -H "X-API-Key: your-api-key" | jq '{
    total: .total_documents,
    success_rate: ((.completed_documents / .total_documents) * 100 | tostring + "%"),
    processing: .processing_documents
  }'

# Export metrics for monitoring
curl -X GET "http://localhost:8000/api/v1/metrics" \
  -H "X-API-Key: your-api-key" \
  -H "Accept: application/json" > metrics_$(date +%Y%m%d_%H%M%S).json
```

**Response** (200 OK):
```json
{
  "total_documents": 150,
  "completed_documents": 145,
  "failed_documents": 3,
  "processing_documents": 2,
  "registered_webhooks": 5,
  "active_jobs": 2,
  "average_processing_time_ms": 2500,
  "success_rate": 96.67
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MISTRAL_API_KEY` | **Required** - Mistral AI API key | - |
| `API_HOST` | API server host | `0.0.0.0` |
| `API_PORT` | API server port | `8000` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://...` |
| `MAX_UPLOAD_SIZE_MB` | Maximum file upload size | `10` |
| `OCR_CONFIDENCE_THRESHOLD` | Minimum OCR confidence | `0.7` |
| `VALIDATION_STRICT_MODE` | Strict validation mode | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 📊 JSON Schema Structure

### Base Schema
```json
{
  "schema_version": "1.0",
  "schema_id": "uuid",
  "document_id": "uuid",
  "document_type": "invoice|receipt|contract|form",
  "timestamp": "2024-01-15T10:00:00Z",
  "confidence_score": 0.92,
  "extracted_data": {
    "metadata": {},
    "fields": {},
    "tables": [],
    "structured": {}
  },
  "processing_metadata": {
    "ocr_confidence": 0.95,
    "processing_time_ms": 1234,
    "page_count": 5
  },
  "automation_triggers": [],
  "validation_status": "passed"
}
```

### Document-Specific Schemas

#### Invoice Schema
```json
{
  "structured": {
    "invoice_details": {
      "number": "string",
      "date": "string",
      "due_date": "string"
    },
    "vendor": {
      "name": "string",
      "tax_id": "string"
    },
    "amounts": {
      "subtotal": "number",
      "tax": "number",
      "total": "number"
    },
    "line_items": []
  }
}
```

## 🔌 Webhook Integration

### Trigger Conditions

Webhooks can be triggered based on conditions:

```json
{
  "condition": {
    "total_amount": {"$gte": 1000},
    "document_type": "invoice",
    "confidence_score": {"$gte": 0.8}
  }
}
```

### Webhook Payload

```json
{
  "event": "document.processed",
  "timestamp": "2024-01-15T10:00:00Z",
  "document_id": "123e4567",
  "document_type": "invoice",
  "data": {
    // Full extracted data structure
  }
}
```

## 🧪 Testing

### Run Tests
```bash
# Test with sample document
./test_pipeline.py

# Test with specific document
./test_pipeline.py path/to/document.pdf
```

### Complete End-to-End Example

**Full workflow from upload to webhook:**

```bash
#!/bin/bash

# Configuration
API_URL="http://localhost:8000"
API_KEY="your-api-key"

# Step 1: Register a webhook
echo "1. Registering webhook..."
WEBHOOK_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/webhooks/register" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://webhook.site/your-unique-url",
    "webhook_name": "Test Processor",
    "events": ["document.processed"]
  }')

WEBHOOK_ID=$(echo $WEBHOOK_RESPONSE | jq -r '.webhook_id')
echo "Webhook registered: $WEBHOOK_ID"

# Step 2: Upload a document
echo -e "\n2. Uploading document..."
UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/documents/upload" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@invoice_sample.pdf")

JOB_ID=$(echo $UPLOAD_RESPONSE | jq -r '.job_id')
DOCUMENT_ID=$(echo $UPLOAD_RESPONSE | jq -r '.document_id')
echo "Document uploaded: $DOCUMENT_ID (Job: $JOB_ID)"

# Step 3: Poll for completion
echo -e "\n3. Processing document..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  STATUS_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/documents/$DOCUMENT_ID/status" \
    -H "X-API-Key: $API_KEY")
  
  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')
  STAGE=$(echo $STATUS_RESPONSE | jq -r '.pipeline_state.stage // "unknown"')
  
  echo "   Status: $STATUS (Stage: $STAGE)"
  
  if [ "$STATUS" = "completed" ]; then
    echo "   ✓ Processing completed!"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "   ✗ Processing failed!"
    ERROR=$(echo $STATUS_RESPONSE | jq -r '.error // "Unknown error"')
    echo "   Error: $ERROR"
    exit 1
  fi
  
  sleep 2
  ATTEMPT=$((ATTEMPT + 1))
done

# Step 4: Retrieve the schema
echo -e "\n4. Retrieving document schema..."
SCHEMA_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/documents/$DOCUMENT_ID/schema" \
  -H "X-API-Key: $API_KEY")

echo "Schema retrieved successfully!"

# Step 5: Display results
echo -e "\n5. Document Processing Results:"
echo "================================"
echo "Document Type: $(echo $SCHEMA_RESPONSE | jq -r '.document_type')"
echo "Confidence: $(echo $SCHEMA_RESPONSE | jq -r '.confidence_score')"
echo "Validation: $(echo $SCHEMA_RESPONSE | jq -r '.validation_status')"

echo -e "\nExtracted Data:"
echo $SCHEMA_RESPONSE | jq '.extracted_data.structured'

echo -e "\nAutomation Triggers:"
echo $SCHEMA_RESPONSE | jq '.automation_triggers[]'

# Step 6: Save results
echo $SCHEMA_RESPONSE > "schema_${DOCUMENT_ID}.json"
echo -e "\n✓ Full schema saved to: schema_${DOCUMENT_ID}.json"

# Step 7: Check metrics
echo -e "\n6. System Metrics:"
METRICS=$(curl -s -X GET "$API_URL/api/v1/metrics" \
  -H "X-API-Key: $API_KEY")

echo "Total Documents: $(echo $METRICS | jq -r '.total_documents')"
echo "Success Rate: $(echo $METRICS | jq -r '.success_rate')%"
echo "Active Webhooks: $(echo $METRICS | jq -r '.registered_webhooks')"
```

### Python Test Script Example

```python
import requests
import time
import json

class DocumentProcessor:
    def __init__(self, api_url="http://localhost:8000", api_key="your-api-key"):
        self.api_url = api_url
        self.headers = {"X-API-Key": api_key}
    
    def upload_document(self, file_path):
        """Upload a document for processing"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.api_url}/api/v1/documents/upload",
                headers=self.headers,
                files=files
            )
        return response.json()
    
    def check_status(self, document_id):
        """Check processing status"""
        response = requests.get(
            f"{self.api_url}/api/v1/documents/{document_id}/status",
            headers=self.headers
        )
        return response.json()
    
    def get_schema(self, document_id):
        """Get processed document schema"""
        response = requests.get(
            f"{self.api_url}/api/v1/documents/{document_id}/schema",
            headers=self.headers
        )
        return response.json()
    
    def process_and_wait(self, file_path, max_wait=60):
        """Complete processing workflow"""
        # Upload
        print(f"Uploading {file_path}...")
        upload_result = self.upload_document(file_path)
        document_id = upload_result['document_id']
        print(f"Document ID: {document_id}")
        
        # Wait for completion
        print("Processing...")
        start_time = time.time()
        while time.time() - start_time < max_wait:
            status = self.check_status(document_id)
            
            if status['status'] == 'completed':
                print("✓ Processing completed!")
                break
            elif status['status'] == 'failed':
                print(f"✗ Processing failed: {status.get('error', 'Unknown')}")
                return None
            
            time.sleep(2)
        
        # Get schema
        schema = self.get_schema(document_id)
        print(f"Document type: {schema['document_type']}")
        print(f"Confidence: {schema['confidence_score']:.2%}")
        
        return schema

# Usage
if __name__ == "__main__":
    processor = DocumentProcessor()
    result = processor.process_and_wait("invoice.pdf")
    
    if result:
        with open("output.json", "w") as f:
            json.dump(result, f, indent=2)
        print("Results saved to output.json")
```

## 🚢 Deployment

### Production Deployment

#### Using Docker

```bash
# Build production image
docker build -t document-agent:latest .

# Run with production settings
docker run -d \
  -p 8000:8000 \
  -e MISTRAL_API_KEY=$MISTRAL_API_KEY \
  -e ENVIRONMENT=production \
  document-agent:latest
```

### Scaling Considerations

- **Horizontal Scaling**: Add more worker nodes for Celery
- **Vertical Scaling**: Increase resources for OCR-heavy workloads
- **Caching**: Implement Redis caching for repeated documents
- **Load Balancing**: Deploy behind nginx or AWS ALB

## 📈 Performance

### Benchmarks

| Document Type | Pages | Processing Time | Accuracy |
|--------------|-------|-----------------|----------|
| Invoice | 1 | ~2s | 92% |
| Receipt | 1 | ~1.5s | 89% |
| Contract | 5 | ~8s | 85% |
| Form | 2 | ~3s | 87% |

## 🔒 Security

### Security Features

- **Input Validation**: File type and size restrictions
- **API Authentication**: API key-based authentication
- **Rate Limiting**: Configurable rate limits per client
- **Input Sanitization**: Prevent injection attacks
- **Secure Storage**: Encryption at rest for sensitive documents
- **Audit Logging**: Comprehensive audit trail

## 🛠️ Troubleshooting

### Common Issues

#### Mistral OCR API Errors
```
Error: Rate limited by Mistral API
Solution: Increase rate_limit_delay in config or upgrade API plan
```

#### Processing Timeout
```
Error: Document processing timeout
Solution: Increase timeout values or optimize document size
```

## 📝 Extensibility

### Adding New Document Types

1. Update `ClassificationAgent` patterns
2. Add extraction logic in `ContentAnalysisAgent`
3. Define schema template in `SchemaGenerationAgent`
4. Add validation rules in `ValidationAgent`

### Custom Agents

Create custom agents by extending `BaseAgent`:

```python
from app.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    async def process(self, input_data, context):
        # Your custom logic here
        return result
```

## 📖 Complete API Reference Summary

### All Available Endpoints

| Endpoint | Method | Description | Authentication |
|----------|---------|-------------|----------------|
| `/api/v1/documents/upload` | POST | Upload document for processing | API Key |
| `/api/v1/documents/{id}/status` | GET | Check processing status | API Key |
| `/api/v1/documents/{id}/schema` | GET | Get generated JSON schema | API Key |
| `/api/v1/webhooks/register` | POST | Register webhook endpoint | API Key |
| `/api/v1/webhooks/list` | GET | List all webhooks | API Key |
| `/api/v1/webhooks/{id}` | PUT | Update webhook configuration | API Key |
| `/api/v1/webhooks/{id}` | DELETE | Delete webhook | API Key |
| `/health` | GET | Health check | None |
| `/api/v1/metrics` | GET | System metrics | API Key |

### Processing Pipeline Stages

1. **RECEIVED** - Document uploaded and stored
2. **CLASSIFICATION** - Document type identified
3. **OCR** - Text extraction via Mistral API
4. **ANALYSIS** - Content parsing and field extraction
5. **SCHEMA_GENERATION** - JSON schema creation
6. **VALIDATION** - Data quality checks
7. **COMPLETED** - Processing finished
8. **FAILED** - Error occurred (check error field)

### Supported Document Types

| Type | Key Fields Extracted | Automation Triggers |
|------|---------------------|-------------------|
| **Invoice** | invoice_number, vendor_name, total_amount, line_items | High-value alerts, payment processing |
| **Receipt** | merchant_name, transaction_date, total_amount, items | Expense tracking, reimbursement |
| **Contract** | party1, party2, effective_date, contract_value | Compliance alerts, renewal reminders |
| **Form** | Dynamic field extraction based on form structure | Custom workflows |

### Error Codes and Troubleshooting

| Error | Cause | Solution |
|-------|--------|----------|
| 400 Bad Request | Invalid file type or size | Check file format and size limits |
| 401 Unauthorized | Invalid API key | Verify X-API-Key header |
| 404 Not Found | Document not found | Check document ID |
| 429 Too Many Requests | Rate limit exceeded | Implement backoff strategy |
| 500 Internal Server Error | Processing failure | Check logs, retry request |

## 🤝 Contributing

We welcome contributions! Please submit pull requests with tests.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- Follow PEP 8 for Python code
- Add type hints to all functions
- Write unit tests for new agents
- Update documentation for API changes
- Ensure all tests pass before submitting PR

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Mistral AI** - OCR API provider
- **FastAPI** - Modern web framework
- **Pydantic** - Data validation
- **Celery** - Distributed task processing

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/document-ingestion-agent/issues)
- **Documentation**: This README contains all documentation
- **API Reference**: Interactive docs at `http://localhost:8000/api/v1/docs`

---

**Document Ingestion Agent v1.0** - Built with ❤️ using FastAPI, Mistral AI, and Python

*Last Updated: 2024*
