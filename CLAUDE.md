# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Document Ingestion Agent - An intelligent multi-agent pipeline for processing documents (PDFs, images) through 5 specialized AI agents, extracting structured data, and generating JSON schemas for webhook automation using Mistral AI OCR API.

## Development Commands

### Running the Application

```bash
# Primary development mode (Redis in Docker, app runs locally)
./run_server.sh

# Full Docker mode
docker-compose -f docker-compose.dev.yml up --build

# Run specific services
docker-compose -f docker-compose.dev.yml up redis  # Just Redis
docker-compose -f docker-compose.dev.yml up celery # Just Celery worker
```

### Testing

```bash
# Test the complete pipeline
python test_pipeline.py

# Test with specific document
python test_pipeline.py path/to/document.pdf

# Test specific endpoints
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "X-API-Key: test-key-1" \
  -F "file=@sample.pdf"
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

## Architecture

### Multi-Agent Pipeline

The system processes documents through 5 sequential agents, each inheriting from `BaseAgent`:

1. **ClassificationAgent** → Identifies document type and validates format
2. **MistralOCRAgent** → Extracts text via Mistral AI API (exclusive OCR provider)
3. **ContentAnalysisAgent** → Pattern-based field extraction
4. **SchemaGenerationAgent** → Creates standardized JSON schemas
5. **ValidationAgent** → Business rule validation and quality assessment

Pipeline stages: `RECEIVED → CLASSIFICATION → OCR → ANALYSIS → SCHEMA_GENERATION → VALIDATION → COMPLETED`

### State Management Architecture

The system uses **Redis multi-database architecture** for state management:

- **DB0**: Application state (document metadata, job states) via `RedisStateManager`
- **DB1**: Celery message broker (task queue)
- **DB2**: Celery result backend (task results)
- **DB3**: Rate limiting data (slowapi)

State is shared between FastAPI and Celery workers through Redis, not in-memory dictionaries.

### Key Architectural Decisions

1. **Async Processing**: Documents are processed asynchronously using Celery tasks (`app/tasks.py`)
2. **Shared State**: `RedisStateManager` (app/services/state_manager.py) provides cross-process state sharing
3. **Rate Limiting**: Per-endpoint limits using slowapi with Redis backend (uploads: 5/min, webhooks: 10/min)
4. **Webhook Delivery**: Webhooks stored in Redis, delivered via Celery with proper event filtering
5. **Status Tracking**: Uses Celery's `AsyncResult` for real-time pipeline status updates

### Critical Implementation Details

#### Agent Registration Pattern
Agents must be registered in `startup_event()` in app/main.py:
```python
orchestrator.register_agent("classification", ClassificationAgent())
orchestrator.register_agent("ocr", MistralOCRAgent(api_key=..., api_url=..., rate_limit_delay=...))
# etc.
```

#### Mistral OCR Configuration
- Exclusive OCR provider - no fallback options
- Rate limiting with configurable delay (default 0.1s between requests)
- Retry logic with exponential backoff built into `MistralOCRAgent`
- Uses httpx for async HTTP requests

#### API Authentication
- Fixed header binding: `x_api_key: Optional[str] = Header(None, alias="X-API-Key")`
- Enable with `API_KEY_REQUIRED=true` or `enable_api_key_auth=true`
- API keys must be loaded from environment (currently empty list by default)

#### Webhook JSON Bodies
All webhook endpoints now accept JSON bodies using Pydantic models:
- `WebhookRegistration` for POST /webhooks/register
- `WebhookUpdate` for PUT /webhooks/{id}
- Stored in Redis for Celery worker access

## Configuration

### Required Environment Variables
```bash
MISTRAL_API_KEY=your_key_here  # REQUIRED - Mistral AI API key
```

### Optional Configuration
```bash
REDIS_HOST=localhost           # Redis host (default: localhost)
REDIS_PORT=6379               # Redis port (default: 6379)
DATABASE_URL=postgresql://... # Optional - PostgreSQL URL (Redis used by default)
API_HOST=0.0.0.0             # API server host
API_PORT=8000                # API server port
```

## Common Development Tasks

### Adding a New Agent
1. Create file in `app/agents/` inheriting from `BaseAgent`
2. Implement `async def process()` method
3. Register in `orchestrator` during `startup_event()` in app/main.py

### Modifying Pipeline Flow
1. Update `PipelineStage` enum in `agent_orchestrator.py`
2. Modify `execute_pipeline()` method to add stage
3. Update agent registration in `startup_event()`

### Adding New Document Type
1. Update classification patterns in `ClassificationAgent`
2. Add extraction logic in `ContentAnalysisAgent` 
3. Define schema template in `SchemaGenerationAgent`
4. Add validation rules in `ValidationAgent`

## File Path Considerations

**Important**: In hybrid development mode (FastAPI local, Celery in Docker), file paths may not match between processes. Documents uploaded locally are saved to `settings.upload_directory` but Celery workers in Docker mount `./uploads:/app/uploads`. Consider:
- Using relative filenames in task parameters
- Ensuring consistent UPLOAD_DIRECTORY environment variable
- Or using shared storage (S3, etc.) for production

## API Endpoints

All 9 endpoints are implemented in `app/main.py`:
- `POST /api/v1/documents/upload` - Rate limited 5/min
- `GET /api/v1/documents/{id}/status` - Uses AsyncResult for Celery tracking
- `GET /api/v1/documents/{id}/schema` - Retrieves from Redis task results
- `POST /api/v1/webhooks/register` - JSON body, rate limited 10/min
- `GET /api/v1/webhooks/list` - Fetches from Redis
- `PUT /api/v1/webhooks/{id}` - JSON body for updates
- `DELETE /api/v1/webhooks/{id}` - Removes from Redis
- `GET /health` - Accepts `?verbose=true` for detailed info
- `GET /api/v1/metrics` - Application statistics

## Monitoring & Debugging

### Check Service Health
```bash
# Redis connectivity
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping

# Celery worker status
docker-compose -f docker-compose.dev.yml logs celery

# API health with verbose info
curl "http://localhost:8000/health?verbose=true"
```

### Common Issues

1. **"Module app.celery_app not found"**: Ensure app/celery_app.py exists with proper configuration
2. **Redis memory warning**: Informational in Docker, set `vm.overcommit_memory=1` on host if needed
3. **Rate limiting not working**: Verify SlowAPIMiddleware is added (currently missing)
4. **Webhooks not triggering**: Check Redis connectivity and webhook active status
5. **Status always "processing"**: Verify Celery workers are running and Redis is accessible