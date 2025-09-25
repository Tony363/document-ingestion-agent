# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Document Ingestion Agent - An intelligent multi-agent pipeline for processing documents through 5 specialized AI agents (Classification → OCR → Analysis → Schema Generation → Validation), extracting structured data and generating JSON schemas using Mistral AI OCR API.

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
# Run all tests
python -m pytest tests/ -v

# Run specific test file
pytest tests/unit/test_agents/test_ocr_agent.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run with markers
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Only integration tests
```

### Code Quality

```bash
# Format code
black app/ --line-length 100

# Lint code  
ruff check app/

# Type checking
mypy app/

# Run all quality checks
make quality
```

## Architecture

### Multi-Agent Pipeline

The system processes documents through 5 sequential agents in `app/agents/`:

1. **ClassificationAgent** → Document type identification and validation
2. **MistralOCRAgent** → Text extraction via Mistral AI API (exclusive provider, no fallback)
3. **ContentAnalysisAgent** → Pattern-based field extraction
4. **SchemaGenerationAgent** → JSON schema creation with webhook triggers
5. **ValidationAgent** → Business rule validation and quality assessment

Pipeline stages: `RECEIVED → CLASSIFICATION → OCR → ANALYSIS → SCHEMA_GENERATION → VALIDATION → COMPLETED`

### State Management Architecture

Redis multi-database architecture for cross-process state sharing:

- **DB0**: Application state (document metadata, job states) via `RedisStateManager`
- **DB1**: Celery message broker (task queue)
- **DB2**: Celery result backend (task results)
- **DB3**: Rate limiting data (slowapi)

State is shared between FastAPI and Celery workers through Redis, not in-memory dictionaries.

### Key Architectural Patterns

#### Agent Registration (app/main.py)
```python
@app.on_event("startup")
async def startup_event():
    orchestrator.register_agent("classification", ClassificationAgent())
    orchestrator.register_agent("ocr", MistralOCRAgent(api_key=..., rate_limit_delay=...))
    # ... register all agents
```

#### Async Task Processing (app/tasks.py)
Documents are processed asynchronously using Celery. The `process_document_task` handles the entire pipeline execution.

#### Worker Signals (app/worker_signals.py)
- Auto-recovery of stuck tasks on worker restart (>5 minutes old)
- Task lifecycle monitoring (failure, retry, success)
- Deferred imports to avoid circular dependencies

## Critical Implementation Details

### Mistral OCR Configuration
- **Exclusive provider** - no fallback OCR options
- Rate limiting with configurable delay (default 0.1s)
- Retry logic with exponential backoff in `MistralOCRAgent`
- Uses httpx for async HTTP requests

### API Authentication
- Header binding: `x_api_key: Optional[str] = Header(None, alias="X-API-Key")`
- Enable with `API_KEY_REQUIRED=true` environment variable
- API keys loaded from environment (empty list by default)

### Webhook System
- Webhooks stored in Redis for Celery worker access
- JSON bodies using Pydantic models (`WebhookRegistration`, `WebhookUpdate`)
- Event-based filtering and retry configuration

### File Path Considerations
In hybrid development mode (FastAPI local, Celery in Docker), file paths may differ:
- Documents saved to `settings.upload_directory` locally
- Celery workers mount `./uploads:/app/uploads`
- Use relative filenames in task parameters for compatibility

## Common Development Tasks

### Adding a New Agent
1. Create file in `app/agents/` inheriting from `BaseAgent`
2. Implement `async def process()` method
3. Register in `orchestrator` during `startup_event()` in app/main.py
4. Update `PipelineStage` enum if adding new pipeline stage

### Modifying Pipeline Flow
1. Update `PipelineStage` enum in `agent_orchestrator.py`
2. Modify `execute_pipeline()` method to add stage
3. Update agent registration order in `startup_event()`

### Debugging Stuck Tasks
```bash
# Check stuck tasks via admin endpoint
curl -X GET "http://localhost:8000/api/v1/admin/stuck-tasks" -H "X-API-Key: ${API_KEY}"

# Manually retry stuck task
curl -X POST "http://localhost:8000/api/v1/admin/retry-task/{document_id}" -H "X-API-Key: ${API_KEY}"

# Monitor Celery workers
docker-compose -f docker-compose.dev.yml logs -f celery
```

## Recent Fixes (v2.1.0)

### Circular Import Resolution
- `worker_signals.py` uses deferred imports (import inside functions)
- Worker signals registered in `celery_app.py` after app creation

### MistralOCRAgent Shutdown
- Removed incorrect `__aexit__` call in shutdown handler
- Mistral client handles cleanup automatically

### Task Recovery
- Tasks stuck in PENDING for >5 minutes auto-retry on worker restart
- Celery configured with 5-minute timeout (`task_time_limit=300`)
- Admin endpoints for manual task management

## Environment Requirements

```bash
# Required
MISTRAL_API_KEY=your_key_here

# Important for development
REDIS_HOST=localhost  # or 'redis' if using Docker
API_KEY_REQUIRED=false  # Set to true for auth testing
CELERY_TASK_TIME_LIMIT=300  # 5-minute timeout
```