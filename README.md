# Document Ingestion Agent

[![Build Status](https://img.shields.io/github/actions/workflow/status/yourusername/document-ingestion-agent/ci.yml?branch=main)](https://github.com/yourusername/document-ingestion-agent/actions)
[![Coverage](https://img.shields.io/codecov/c/github/yourusername/document-ingestion-agent)](https://codecov.io/gh/yourusername/document-ingestion-agent)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/docker/v/yourusername/document-ingestion-agent?label=docker)](https://hub.docker.com/r/yourusername/document-ingestion-agent)
[![Documentation](https://img.shields.io/badge/docs-latest-green.svg)](https://yourusername.github.io/document-ingestion-agent)

> Transform unstructured documents into actionable structured data with intelligent extraction and automation capabilities.

The Document Ingestion Agent automates the tedious process of extracting data from unstructured documents (PDFs, scans, emails) and converting them into structured formats that drive business actions. Built for enterprise scalability and developer extensibility.

## Quick Start

Get up and running in under 5 minutes:

### Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/document-ingestion-agent.git
cd document-ingestion-agent

# Start with Docker Compose
docker-compose up -d

# Verify installation
curl http://localhost:8080/health

# Process your first document
curl -X POST http://localhost:8080/api/v1/ingest \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample-invoice.pdf"
```

### Local Installation

```bash
# Python setup
pip install document-ingestion-agent

# Or with Node.js
npm install -g document-ingestion-agent

# Run the agent
document-agent start

# Process a document
document-agent process invoice.pdf --output json
```

## Features

- **Multi-Format Support**: Process PDFs, scanned images, emails, and Office documents
- **Intelligent Extraction**: AI-powered field detection and data extraction
- **Flexible Output**: Generate JSON, CSV, XML, or directly populate web forms
- **Plugin Architecture**: Extend with custom document types and processing rules
- **Webhook Integration**: Real-time notifications and third-party integrations
- **High Performance**: Process hundreds of documents per minute with parallel processing
- **Enterprise Ready**: Built-in security, audit logging, and compliance features

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Document Input Layer                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   PDF    │  │  Images  │  │  Emails  │  │   Office  │  │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘  │
└────────┼─────────────┼─────────────┼─────────────┼────────┘
         │             │             │             │
         └─────────────┴──────┬──────┴─────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing Pipeline                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │   OCR Engine │→ │   Extractor  │→ │   Validator      │ │
│  │   (Optional) │  │   (AI/Rules) │  │   (Schema-based) │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Output Actions                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   JSON   │  │    CSV   │  │ Webhooks │  │ Web Forms│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

- **Input Adapters**: Handle various document formats with format-specific parsers
- **OCR Engine**: Optional Tesseract/Cloud Vision integration for scanned documents
- **Extraction Engine**: Configurable rules engine with AI-powered field detection
- **Validation Layer**: Schema-based validation with business rule enforcement
- **Output Adapters**: Flexible output generation with multiple format support
- **Plugin System**: Extend functionality with custom processors and actions

## Installation

### Prerequisites

- Python 3.8+ or Node.js 14+
- Docker 20.10+ (for containerized deployment)
- 4GB RAM minimum (8GB recommended for production)
- Optional: Tesseract OCR for local OCR processing

### Docker Installation

```bash
# Pull the official image
docker pull yourusername/document-ingestion-agent:latest

# Run with custom configuration
docker run -d \
  --name document-agent \
  -p 8080:8080 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  yourusername/document-ingestion-agent:latest
```

### Python Installation

```bash
# Install from PyPI
pip install document-ingestion-agent

# Install with OCR support
pip install document-ingestion-agent[ocr]

# Install with all optional dependencies
pip install document-ingestion-agent[all]
```

### Node.js Installation

```bash
# Install globally
npm install -g document-ingestion-agent

# Or add to your project
npm install document-ingestion-agent

# With TypeScript support
npm install document-ingestion-agent @types/document-ingestion-agent
```

### Building from Source

```bash
# Clone repository
git clone https://github.com/yourusername/document-ingestion-agent.git
cd document-ingestion-agent

# Python build
pip install -e .

# Node.js build
npm install
npm run build

# Run tests
pytest  # or npm test
```

## Configuration

### Environment Variables

```bash
# Core Settings
DIA_PORT=8080                    # API server port
DIA_HOST=0.0.0.0                # API server host
DIA_LOG_LEVEL=INFO              # Logging level (DEBUG, INFO, WARN, ERROR)
DIA_WORKERS=4                    # Number of worker processes

# Storage Configuration
DIA_STORAGE_TYPE=local          # Storage backend (local, s3, gcs, azure)
DIA_STORAGE_PATH=/app/data      # Local storage path
DIA_S3_BUCKET=my-bucket         # S3 bucket name (if using S3)
DIA_S3_REGION=us-east-1         # S3 region

# OCR Configuration
DIA_OCR_ENGINE=tesseract        # OCR engine (tesseract, cloudvision, textract)
DIA_OCR_LANGUAGES=eng,spa,fra   # Supported OCR languages
DIA_OCR_TIMEOUT=30              # OCR timeout in seconds

# Security
DIA_API_KEY_REQUIRED=true       # Require API key authentication
DIA_WEBHOOK_SECRET=your-secret  # Secret for webhook signatures
DIA_ALLOWED_ORIGINS=*           # CORS allowed origins

# Database (optional)
DIA_DATABASE_URL=postgresql://user:pass@localhost/dia
DIA_REDIS_URL=redis://localhost:6379
```

### Configuration File

Create a `config.yaml` file:

```yaml
# config.yaml
server:
  port: 8080
  host: 0.0.0.0
  workers: 4
  timeout: 30

extraction:
  default_engine: rule_based
  ai_model: gpt-4-vision  # Optional AI model for extraction
  confidence_threshold: 0.85

document_types:
  invoice:
    fields:
      - name: invoice_number
        type: string
        required: true
        pattern: "INV-\\d{6}"
      - name: vendor
        type: string
        required: true
      - name: total_amount
        type: number
        required: true
      - name: line_items
        type: array
        schema:
          - description: string
          - quantity: number
          - unit_price: number
          - total: number
    
  purchase_order:
    fields:
      - name: po_number
        type: string
        required: true
      - name: vendor
        type: string
        required: true
      - name: items
        type: array

output:
  default_format: json
  json:
    pretty_print: true
    include_metadata: true
  csv:
    delimiter: ","
    include_headers: true
  webhooks:
    - url: https://your-system.com/webhook
      events: ["document.processed", "document.failed"]
      retry_attempts: 3
      timeout: 10

plugins:
  enabled: true
  directory: ./plugins
  auto_load: true

security:
  api_key_required: true
  rate_limit:
    enabled: true
    requests_per_minute: 100
  allowed_file_types:
    - .pdf
    - .png
    - .jpg
    - .jpeg
    - .tiff
    - .docx
    - .eml
```

## Usage

### Command Line Interface

```bash
# Process a single document
document-agent process invoice.pdf

# Process with specific output format
document-agent process invoice.pdf --format csv --output results.csv

# Process a directory of documents
document-agent process ./documents --recursive --parallel

# Use a specific document type
document-agent process receipt.jpg --type receipt

# Validate configuration
document-agent config validate

# Start the API server
document-agent server start --port 8080

# Run in watch mode for development
document-agent dev --watch ./documents
```

### API Usage

#### Process Document

```bash
# Basic document processing
curl -X POST http://localhost:8080/api/v1/ingest \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@invoice.pdf" \
  -F "document_type=invoice"

# Response
{
  "id": "doc_123456",
  "status": "completed",
  "document_type": "invoice",
  "extracted_data": {
    "invoice_number": "INV-001234",
    "vendor": "Acme Corp",
    "date": "2024-01-15",
    "total_amount": 1234.56,
    "line_items": [
      {
        "description": "Product A",
        "quantity": 2,
        "unit_price": 500.00,
        "total": 1000.00
      }
    ]
  },
  "metadata": {
    "processing_time": 1.234,
    "confidence_score": 0.95,
    "page_count": 2
  }
}
```

#### Batch Processing

```bash
# Submit batch job
curl -X POST http://localhost:8080/api/v1/batch \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"url": "https://example.com/doc1.pdf", "type": "invoice"},
      {"url": "https://example.com/doc2.pdf", "type": "receipt"}
    ],
    "webhook_url": "https://your-system.com/batch-complete"
  }'

# Check batch status
curl http://localhost:8080/api/v1/batch/batch_789 \
  -H "Authorization: Bearer your-api-key"
```

### Python SDK

```python
from document_ingestion_agent import DocumentAgent, DocumentType

# Initialize the agent
agent = DocumentAgent(config_file="config.yaml")

# Process a single document
result = agent.process_document(
    file_path="invoice.pdf",
    document_type=DocumentType.INVOICE
)

print(f"Extracted data: {result.data}")
print(f"Confidence: {result.confidence}")

# Batch processing
documents = [
    "invoice1.pdf",
    "invoice2.pdf",
    "receipt.jpg"
]

results = agent.process_batch(documents, parallel=True)

for result in results:
    if result.success:
        print(f"Processed {result.filename}: {result.data}")
    else:
        print(f"Failed {result.filename}: {result.error}")

# Custom extraction rules
agent.add_extraction_rule(
    document_type="custom_invoice",
    field_name="special_code",
    pattern=r"CODE-\d{8}",
    required=True
)

# Webhook integration
agent.on("document.processed", lambda event: 
    print(f"Processed: {event.document_id}")
)
```

### Node.js SDK

```javascript
const { DocumentAgent, DocumentType } = require('document-ingestion-agent');

// Initialize the agent
const agent = new DocumentAgent({ configFile: 'config.yaml' });

// Process a document
async function processInvoice() {
  try {
    const result = await agent.processDocument({
      filePath: 'invoice.pdf',
      documentType: DocumentType.INVOICE
    });
    
    console.log('Extracted data:', result.data);
    console.log('Confidence:', result.confidence);
  } catch (error) {
    console.error('Processing failed:', error);
  }
}

// Batch processing with streaming
const stream = agent.processBatchStream(['doc1.pdf', 'doc2.pdf']);

stream.on('data', (result) => {
  console.log(`Processed ${result.filename}`);
});

stream.on('error', (error) => {
  console.error('Stream error:', error);
});

stream.on('end', () => {
  console.log('Batch processing complete');
});

// Express.js integration
const express = require('express');
const app = express();

app.post('/upload', agent.expressMiddleware(), (req, res) => {
  res.json(req.documentResult);
});
```

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ingest` | Process a single document |
| POST | `/api/v1/batch` | Submit batch processing job |
| GET | `/api/v1/batch/{id}` | Get batch job status |
| GET | `/api/v1/document/{id}` | Retrieve processed document |
| DELETE | `/api/v1/document/{id}` | Delete processed document |
| GET | `/api/v1/document-types` | List available document types |
| POST | `/api/v1/document-types` | Create custom document type |
| GET | `/api/v1/health` | Health check endpoint |
| GET | `/api/v1/metrics` | Prometheus metrics |

### Authentication

The API supports multiple authentication methods:

```bash
# API Key (header)
curl -H "Authorization: Bearer your-api-key" http://localhost:8080/api/v1/ingest

# API Key (query parameter)
curl http://localhost:8080/api/v1/ingest?api_key=your-api-key

# Basic Auth
curl -u username:password http://localhost:8080/api/v1/ingest
```

### Error Responses

```json
{
  "error": {
    "code": "INVALID_DOCUMENT_TYPE",
    "message": "Document type 'custom' is not recognized",
    "details": {
      "available_types": ["invoice", "receipt", "purchase_order"],
      "suggestion": "Use 'invoice' for this document"
    }
  },
  "request_id": "req_abc123",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Error codes:
- `INVALID_DOCUMENT_TYPE`: Unknown document type
- `EXTRACTION_FAILED`: Could not extract required fields
- `VALIDATION_ERROR`: Extracted data failed validation
- `OCR_FAILED`: OCR processing failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `UNAUTHORIZED`: Invalid or missing authentication
- `INTERNAL_ERROR`: Server error

## Webhooks

### Configuration

```yaml
webhooks:
  - url: https://your-system.com/webhook
    events: 
      - document.processed
      - document.failed
      - batch.completed
    headers:
      X-Custom-Header: value
    retry:
      attempts: 3
      backoff: exponential
      max_delay: 300
```

### Event Payloads

```json
{
  "event": "document.processed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "document_id": "doc_123",
    "document_type": "invoice",
    "extracted_data": { ... },
    "metadata": { ... }
  },
  "signature": "sha256=..."
}
```

### Signature Verification

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(
        f"sha256={expected}",
        signature
    )
```

## Plugin System

### Creating a Plugin

```python
# plugins/custom_processor.py
from document_ingestion_agent import Plugin, Document

class CustomProcessor(Plugin):
    """Custom document processor plugin"""
    
    def __init__(self):
        super().__init__(
            name="custom_processor",
            version="1.0.0",
            document_types=["custom_invoice"]
        )
    
    def process(self, document: Document) -> dict:
        """Process document and extract data"""
        # Custom extraction logic
        data = {
            "custom_field": self.extract_pattern(
                document.text,
                r"CUSTOM-\d{6}"
            )
        }
        return data
    
    def validate(self, data: dict) -> bool:
        """Validate extracted data"""
        return "custom_field" in data

# Register the plugin
plugin = CustomProcessor()
```

### Plugin Configuration

```yaml
plugins:
  custom_processor:
    enabled: true
    priority: 100
    config:
      custom_setting: value
```

## Testing

### Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=document_ingestion_agent

# Run specific test file
pytest tests/test_extraction.py

# Run with verbose output
pytest -v

# Run only fast tests
pytest -m "not slow"
```

### Integration Tests

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up

# Run integration tests
pytest tests/integration --integration

# Test with real documents
pytest tests/e2e --e2e --documents ./test-documents
```

### Example Test

```python
import pytest
from document_ingestion_agent import DocumentAgent

@pytest.fixture
def agent():
    return DocumentAgent(config_file="test-config.yaml")

def test_invoice_extraction(agent):
    result = agent.process_document(
        file_path="tests/fixtures/invoice.pdf",
        document_type="invoice"
    )
    
    assert result.success
    assert result.data["invoice_number"] == "INV-001234"
    assert result.confidence >= 0.85

def test_invalid_document(agent):
    with pytest.raises(ValueError):
        agent.process_document(
            file_path="tests/fixtures/invalid.txt",
            document_type="invoice"
        )
```

## Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["document-agent", "server", "start"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  document-agent:
    image: yourusername/document-ingestion-agent:latest
    ports:
      - "8080:8080"
    environment:
      - DIA_DATABASE_URL=postgresql://postgres:password@db:5432/dia
      - DIA_REDIS_URL=redis://redis:6379
    volumes:
      - ./config:/app/config
      - ./data:/app/data
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=dia
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Deployment

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-ingestion-agent
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
      - name: agent
        image: yourusername/document-ingestion-agent:latest
        ports:
        - containerPort: 8080
        env:
        - name: DIA_DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
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
    targetPort: 8080
  type: LoadBalancer
```

### AWS Deployment

```bash
# Deploy to AWS ECS
aws ecs create-service \
  --cluster production \
  --service-name document-agent \
  --task-definition document-agent:1 \
  --desired-count 2 \
  --launch-type FARGATE

# Deploy to AWS Lambda
serverless deploy --stage production
```

### Monitoring

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'document-agent'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/api/v1/metrics'
```

## Performance

### Benchmarks

| Document Type | Pages | Processing Time | Accuracy |
|--------------|-------|-----------------|----------|
| Invoice (PDF) | 1 | 0.8s | 96% |
| Invoice (Scan) | 1 | 2.1s | 92% |
| Multi-page PDF | 10 | 4.5s | 94% |
| Email with attachments | - | 1.2s | 95% |

### Optimization Tips

1. **Enable parallel processing** for batch operations
2. **Use Redis** for caching extracted data
3. **Configure worker pools** based on CPU cores
4. **Enable GPU acceleration** for OCR if available
5. **Use webhook queues** for async processing

### Resource Requirements

- **Minimum**: 2 CPU cores, 4GB RAM
- **Recommended**: 4 CPU cores, 8GB RAM
- **Production**: 8+ CPU cores, 16GB+ RAM
- **Storage**: 10GB + document volume

## Security

### Best Practices

1. **Authentication**: Always use API keys in production
2. **Encryption**: Enable TLS for all API endpoints
3. **Input Validation**: Sanitize all user inputs
4. **File Upload**: Restrict file types and sizes
5. **Secrets Management**: Use environment variables or secret managers
6. **Audit Logging**: Enable comprehensive logging
7. **Rate Limiting**: Implement per-user rate limits

### Webhook Security

```python
# Verify webhook signatures
import hmac
import hashlib
from datetime import datetime, timedelta

def verify_webhook(request, secret):
    # Get signature from header
    signature = request.headers.get('X-Signature')
    timestamp = request.headers.get('X-Timestamp')
    
    # Check timestamp (prevent replay attacks)
    if abs(datetime.now() - datetime.fromtimestamp(int(timestamp))) > timedelta(minutes=5):
        return False
    
    # Verify signature
    payload = f"{timestamp}.{request.body}"
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### Compliance

- **GDPR**: Personal data handling and right to deletion
- **HIPAA**: Healthcare document processing compliance
- **SOC2**: Security controls and audit trails
- **PCI DSS**: Credit card data handling

## Troubleshooting

### Common Issues

#### OCR Not Working

```bash
# Check Tesseract installation
tesseract --version

# Install language packs
apt-get install tesseract-ocr-eng tesseract-ocr-spa

# Verify in configuration
document-agent config get ocr.engine
```

#### Slow Processing

1. Check system resources: `htop` or `docker stats`
2. Enable parallel processing: `DIA_WORKERS=8`
3. Use Redis caching: `DIA_REDIS_URL=redis://localhost:6379`
4. Profile processing: `document-agent process --profile invoice.pdf`

#### Extraction Accuracy Issues

1. Verify document quality (300 DPI minimum for scans)
2. Adjust confidence threshold in configuration
3. Train custom models for specific document types
4. Use AI-powered extraction for complex documents

### Debug Mode

```bash
# Enable debug logging
export DIA_LOG_LEVEL=DEBUG

# Run with verbose output
document-agent process invoice.pdf --verbose

# Enable profiling
document-agent process invoice.pdf --profile --profile-output profile.json

# Test configuration
document-agent config test
```

### Logging

```python
import logging
from document_ingestion_agent import configure_logging

# Configure custom logging
configure_logging(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    output_file='document-agent.log'
)
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/document-ingestion-agent.git
cd document-ingestion-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
flake8 .
black .
mypy .
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use ESLint for JavaScript/TypeScript
- Write comprehensive tests for new features
- Add documentation for public APIs
- Include type hints for Python functions

## Roadmap

### Q1 2024
- [ ] Multi-language OCR support
- [ ] Advanced AI extraction models
- [ ] Real-time collaboration features

### Q2 2024
- [ ] Mobile SDK (iOS/Android)
- [ ] Graph-based document relationships
- [ ] AutoML for custom extractors

### Q3 2024
- [ ] Blockchain verification
- [ ] Federated learning support
- [ ] Edge deployment options

### Q4 2024
- [ ] Natural language querying
- [ ] Video document support
- [ ] Advanced analytics dashboard

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [https://docs.example.com](https://docs.example.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/document-ingestion-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/document-ingestion-agent/discussions)
- **Email**: support@example.com
- **Slack**: [Join our Slack](https://slack.example.com)

## Acknowledgments

- Built with passion by the Document Ingestion Agent team
- Powered by open-source technologies
- Special thanks to all contributors

---

Made with ❤️ by the Document Ingestion Agent Team