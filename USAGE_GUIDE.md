# Document Ingestion Agent v2.0 - Usage Guide

## Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd document-ingestion-agent

# Copy environment configuration
cp .env.example .env

# Edit .env and add your Mistral API key
# MISTRAL_API_KEY=your_actual_mistral_api_key_here
```

### 2. Running the Application

#### Option A: Using the startup script
```bash
./run_server.sh
```

#### Option B: Using Docker Compose
```bash
docker-compose up
```

#### Option C: Manual setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Testing the Pipeline

### Run the Test Script
```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Run the test pipeline
python test_pipeline.py
```

This will:
1. Check server health
2. Create a test invoice PDF
3. Upload and process the document
4. Monitor processing progress
5. Retrieve extracted content
6. Get the generated JSON schema

## API Endpoints

### Document Upload
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@invoice.pdf" \
  -F "document_type=invoice"
```

Response:
```json
{
  "document_id": "uuid-here",
  "status": "received",
  "message": "Document uploaded successfully. Processing started."
}
```

### Check Processing Status
```bash
curl "http://localhost:8000/documents/{document_id}/status"
```

Response:
```json
{
  "document_id": "uuid-here",
  "status": "processing",
  "progress": 0.6,
  "processing_stage": "content_analysis",
  "created_at": "2025-01-24T10:00:00Z",
  "updated_at": "2025-01-24T10:00:15Z"
}
```

### Get Extracted Content
```bash
curl "http://localhost:8000/documents/{document_id}/content"
```

Response:
```json
{
  "document_id": "uuid-here",
  "document_type": "invoice",
  "raw_text": "Full OCR text here...",
  "structured_content": {
    "invoice_number": "INV-2025-001",
    "date": "2025-01-24",
    "vendor_name": "ABC Company",
    "total_amount": "1650.00"
  },
  "confidence_score": 0.95,
  "metadata": {
    "processing_time": 3.5,
    "pages": 1,
    "language": "en"
  }
}
```

### Get JSON Schema
```bash
curl "http://localhost:8000/documents/{document_id}/schema"
```

Response:
```json
{
  "document_id": "uuid-here",
  "document_type": "invoice",
  "schema_version": "1.0",
  "schema": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
      "invoice_number": {"type": "string"},
      "date": {"type": "string", "format": "date"},
      "vendor_info": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "address": {"type": "string"}
        }
      },
      "total_amount": {"type": "number"}
    }
  },
  "extraction_confidence": 0.95,
  "webhook_ready": true,
  "created_at": "2025-01-24T10:00:20Z"
}
```

## Supported Document Types

- **Invoice**: Vendor info, invoice number, dates, line items, totals
- **Receipt**: Merchant info, transaction details, items, payment method
- **Contract**: Parties, terms, dates, signatures
- **Form**: Field names and values, checkboxes, signatures

## Agent Pipeline Stages

1. **Validation Agent**: File validation, security scanning, format checking
2. **Classification Agent**: Document type detection and complexity assessment
3. **Mistral OCR Agent**: Text extraction using Mistral OCR API
4. **Content Analysis Agent**: Field extraction and data structuring
5. **Schema Generation Agent**: Dynamic JSON schema creation

## Running in Different Modes

### Development Mode (with auto-reload)
```bash
uvicorn app.main:app --reload
```

### Production Mode
```bash
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Simulation Mode (without Mistral API)
The application automatically runs in simulation mode when no valid Mistral API key is provided. This is useful for development and testing.

## Configuration Options

Edit the `.env` file to configure:

- `MISTRAL_API_KEY`: Your Mistral OCR API key (required for production)
- `MAX_FILE_SIZE`: Maximum upload file size (default: 50MB)
- `SUPPORTED_FILE_TYPES`: Comma-separated list of supported extensions
- `MAX_CONCURRENT_DOCUMENTS`: Number of documents to process in parallel
- `PROCESSING_TIMEOUT`: Timeout for document processing (seconds)

## Troubleshooting

### Server not starting
- Check Python version (3.8+ required)
- Verify all dependencies are installed
- Check port 8000 is not in use

### Processing fails
- Verify Mistral API key is valid
- Check file format is supported
- Ensure file size is within limits

### Slow processing
- OCR processing can take 10-30 seconds per page
- Complex documents may require more time
- Consider adjusting `MAX_CONCURRENT_DOCUMENTS`

## Cost Optimization

The system automatically detects native PDF text to avoid unnecessary OCR:
- Native PDF text extraction: ~90% cost savings
- Only images and scanned PDFs use Mistral OCR
- Cost: $0.001 per page for OCR processing

## Webhook Integration

When a document is marked as `webhook_ready`:
1. The JSON schema is validated and complete
2. All required fields have been extracted
3. Confidence score meets threshold (>0.7)
4. Ready for automated webhook delivery

Configure webhook endpoints in future versions by setting:
- `WEBHOOK_URL`: Target webhook endpoint
- `WEBHOOK_SECRET`: Signing secret for webhook payloads
- `WEBHOOK_RETRY_ATTEMPTS`: Number of retry attempts

## API Rate Limits

- Mistral OCR API: 60 requests per minute
- Document upload: 100 documents per minute
- Status checks: No limit

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black app/
flake8 app/
mypy app/
```

### Adding New Document Types

1. Update `ClassificationAgent` with new patterns
2. Add extraction patterns in `ContentAnalysisAgent`
3. Create schema template in `SchemaGenerationAgent`
4. Update documentation

## Support

For issues or questions:
1. Check the logs: `tail -f uvicorn.log`
2. Review API documentation: http://localhost:8000/docs
3. Test with the provided test script
4. Check environment configuration in `.env`

## License

[Your License Here]