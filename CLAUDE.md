# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Document Ingestion Agent is a system for extracting structured data from unstructured documents (PDFs, scans, emails) and automating follow-up actions. The project is designed to be extensible with support for multiple document types, output formats, and integration methods.

## Common Development Commands

### Setup and Installation
```bash
# Python development setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"

# Node.js development setup
npm install
npm run build
```

### Running the Application
```bash
# Start the API server
document-agent server start --port 8080

# Process a document via CLI
document-agent process invoice.pdf --output json

# Run in development mode with hot reload
document-agent dev --watch ./documents

# Start with Docker
docker-compose up -d
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=document_ingestion_agent --cov-report=html

# Run specific test category
pytest -m "not slow"  # Skip slow tests
pytest tests/unit  # Unit tests only
pytest tests/integration --integration  # Integration tests

# Run a single test file
pytest tests/test_extraction.py -v

# Node.js testing
npm test
npm run test:coverage
```

### Code Quality
```bash
# Python linting and formatting
black .  # Format code
flake8 .  # Lint code
mypy .  # Type checking
pre-commit run --all-files  # Run all pre-commit hooks

# Node.js linting
npm run lint
npm run lint:fix
```

### Building and Deployment
```bash
# Build Docker image
docker build -t document-ingestion-agent .

# Deploy to Kubernetes
kubectl apply -f kubernetes/

# Package for distribution
python setup.py sdist bdist_wheel
npm run build:dist
```

## High-Level Architecture

### Core Components

1. **Input Layer (`src/input/`)**
   - Document parsers for different formats (PDF, images, emails, Office)
   - Format detection and routing logic
   - Initial document validation

2. **Processing Pipeline (`src/processing/`)**
   - OCR Engine integration (Tesseract, Cloud Vision, Textract)
   - Extraction Engine with rule-based and AI-powered extractors
   - Validation Layer for schema enforcement
   - Plugin system for extensibility

3. **Output Layer (`src/output/`)**
   - Format converters (JSON, CSV, XML)
   - Webhook dispatcher with retry logic
   - Web form population adapters
   - Batch processing coordinator

4. **API Layer (`src/api/`)**
   - RESTful endpoints for document processing
   - Authentication and authorization middleware
   - Rate limiting and request validation
   - WebSocket support for real-time updates

5. **Storage Layer (`src/storage/`)**
   - Document storage abstraction (local, S3, GCS, Azure)
   - Database models for metadata and results
   - Redis integration for caching and queues

### Key Design Patterns

- **Plugin Architecture**: Extensible system for adding new document types and processors
- **Pipeline Pattern**: Modular processing stages that can be composed
- **Strategy Pattern**: Different extraction strategies (rule-based, AI, hybrid)
- **Observer Pattern**: Event-driven architecture for webhooks and notifications
- **Factory Pattern**: Document parser and output format selection

### Configuration System

The application uses a hierarchical configuration system:
1. Default values in code
2. Configuration file (`config.yaml`)
3. Environment variables (prefixed with `DIA_`)
4. Command-line arguments (highest precedence)

### Extension Points

- **Custom Document Types**: Define in `config.yaml` or via API
- **Extraction Rules**: Add patterns via configuration or plugins
- **Output Formats**: Implement new converters in `src/output/converters/`
- **Webhooks**: Configure endpoints and events dynamically
- **Plugins**: Drop Python modules in `plugins/` directory

## Important Considerations

### Performance
- The system is designed for parallel processing - use worker pools for batch operations
- Redis is recommended for production deployments to handle queuing and caching
- OCR operations are CPU/GPU intensive - consider resource allocation

### Security
- Always validate and sanitize file uploads
- Use HMAC signatures for webhook verification
- Implement rate limiting for API endpoints
- Store secrets in environment variables, never in code

### Testing
- Unit tests should mock external dependencies (OCR engines, cloud services)
- Integration tests use Docker containers for dependencies
- E2E tests require sample documents in `tests/fixtures/`
- Always test new extraction rules with multiple document variations

### Error Handling
- The system follows fail-fast principles for invalid configurations
- Extraction failures are logged but don't stop batch processing
- Webhook failures trigger exponential backoff retries
- All errors include correlation IDs for tracing

## Development Workflow

1. **Feature Development**
   - Create feature branch from `main`
   - Write tests first (TDD encouraged)
   - Implement feature with documentation
   - Run full test suite before committing

2. **Adding Document Types**
   - Define schema in `config.yaml`
   - Create sample documents for testing
   - Implement custom extractor if needed
   - Add integration tests

3. **Plugin Development**
   - Inherit from `Plugin` base class
   - Implement required methods (`process`, `validate`)
   - Place in `plugins/` directory
   - Add plugin-specific tests

4. **API Changes**
   - Update OpenAPI specification
   - Implement backwards compatibility
   - Update SDK examples
   - Document migration path

## Debugging Tips

- Enable debug logging: `export DIA_LOG_LEVEL=DEBUG`
- Use `--profile` flag to identify performance bottlenecks
- Check `logs/` directory for detailed error traces
- Use `document-agent config validate` to verify configuration
- Monitor `/api/v1/metrics` endpoint for system metrics