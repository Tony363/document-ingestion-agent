# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Document Ingestion Agent - an intelligent pipeline for processing multi-media documents (PDFs, images) through a series of specialized agents. It extracts, classifies, and transforms documents into structured JSON schemas for webhook and API automation triggers using the Mistral AI OCR API.

## Architecture

### Multi-Agent System
The system uses a **5-Agent Architecture**, each inheriting from `BaseAgent`:
1. **ClassificationAgent** - Identifies document type and validates file format
2. **MistralOCRAgent** - Handles text extraction via Mistral AI OCR API
3. **ContentAnalysisAgent** - Pattern-based field extraction and parsing
4. **SchemaGenerationAgent** - Creates standardized JSON schemas for automation
5. **ValidationAgent** - Business rule validation and data quality assessment

### Pipeline Flow
Documents flow through these stages: `RECEIVED → CLASSIFICATION → OCR → ANALYSIS → SCHEMA_GENERATION → VALIDATION → COMPLETED`

The `AgentOrchestrator` (app/agents/agent_orchestrator.py) manages the pipeline execution and state transitions.

## Development Commands

### Running the Application

```bash
# Local development (requires Redis running)
./run_server.sh

# Docker development (recommended)
docker-compose up --build

# Run specific service
docker-compose up app  # Just the API
docker-compose up celery  # Just the worker
```

### Testing

```bash
# Test the pipeline with sample document
python test_pipeline.py

# Test with specific document
python test_pipeline.py path/to/document.pdf
```

### Code Quality

```bash
# Format code
black app/ --line-length 100

# Lint code
ruff check app/

# Type checking
mypy app/
```

### Testing Individual Components

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_ocr_agent.py -v
```

## Key Implementation Details

### Agent Base Class Pattern
All agents inherit from `BaseAgent` (app/agents/base_agent.py) which provides:
- Async execution with `execute()` method
- Automatic retry logic with exponential backoff
- Health check capabilities
- Standardized error handling
- Metrics collection hooks

### Mistral OCR Integration
The `MistralOCRAgent` (app/agents/mistral_ocr_agent.py) is the exclusive OCR provider:
- Handles rate limiting with configurable delay
- Implements intelligent retry logic
- Supports both PDF and image formats
- Uses httpx for async HTTP requests

### API Authentication
- Uses API key authentication via `X-API-Key` header
- Dependency injection pattern with `verify_api_key` in main.py
- Keys configured via environment variables

### State Management
- In-memory state storage for development (dictionaries in main.py)
- Production should use PostgreSQL (models not yet implemented)
- Pipeline states tracked in `PipelineState` objects

## Environment Variables

Critical environment variables:
- `MISTRAL_API_KEY` (required) - Your Mistral AI API key
- `REDIS_HOST` - Redis server host (default: localhost)
- `DATABASE_URL` - PostgreSQL connection string
- `API_HOST` - API server host (default: 0.0.0.0)
- `API_PORT` - API server port (default: 8000)

## API Endpoints

Main endpoints implemented in `app/main.py`:
- `POST /api/v1/documents/upload` - Upload document for processing
- `GET /api/v1/documents/{id}/status` - Check processing status
- `GET /api/v1/documents/{id}/schema` - Get generated JSON schema
- `POST /api/v1/webhooks/register` - Register webhook endpoint
- `GET /health` - Health check

## File Structure Patterns

- **Agents**: All in `app/agents/` directory, inherit from `base_agent.py`
- **Configuration**: Centralized in `app/config.py` using Pydantic Settings
- **API Routes**: All in `app/main.py` (consider splitting if it grows)
- **Docker**: `docker-compose.yml` for full stack, `Dockerfile` for app image

## Common Development Tasks

### Adding a New Agent
1. Create new file in `app/agents/`
2. Inherit from `BaseAgent`
3. Implement `async def process()` method
4. Register in `AgentOrchestrator` in `app/main.py` startup event

### Modifying Pipeline Flow
1. Update `PipelineStage` enum in `agent_orchestrator.py`
2. Modify `execute_pipeline()` method to add new stage
3. Update agent registration in `startup_event()`

### Adding New Document Type
1. Update classification patterns in `ClassificationAgent`
2. Add extraction logic in `ContentAnalysisAgent`
3. Define schema template in `SchemaGenerationAgent`
4. Add validation rules in `ValidationAgent`