# Docker-Based Development Setup

This document explains the hybrid development setup using Docker containers for dependencies while running the FastAPI application locally.

## Overview

The development setup uses:
- **Docker containers** for Redis and Celery (no local installation required)
- **Local Python** for FastAPI application (with hot reload for development)

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Python 3.11+ installed locally
- Git

### Starting the Application

```bash
# Clone the repository
git clone <repository-url>
cd document-ingestion-agent

# Run the server (automatically starts Docker dependencies)
./run_server.sh
```

This script will:
1. Load environment variables from `.env`
2. Start Redis in Docker
3. Start Celery worker in Docker (with your local code mounted)
4. Run FastAPI locally with hot reload

### Stopping the Application

Press `Ctrl+C` to stop. The script automatically cleans up Docker containers.

## Development Modes

### 1. Hybrid Mode (Recommended for Development)
- Redis and Celery run in Docker
- FastAPI runs locally with hot reload
- Best for active development with quick iterations

```bash
./run_server.sh
```

### 2. Full Docker Mode
- Everything runs in Docker containers
- Good for testing production-like environment

```bash
docker-compose up --build
```

### 3. Dependencies Only Mode
- Start only Redis/Celery, run FastAPI manually
- Good for debugging or custom FastAPI startup

```bash
# Start dependencies
./scripts/start-docker-deps.sh

# In another terminal, run FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# When done
./scripts/stop-docker-deps.sh
```

## Docker Files Explained

### docker-compose.dev.yml
- Development-specific Docker configuration
- Minimal services: Redis and Celery
- Mounts local code for hot reload in Celery
- Exposes Redis on localhost:6379

### docker-compose.yml
- Full production-like setup
- Includes all services: app, celery, redis, postgres, monitoring
- Used for `docker-compose up` without `-f` flag

## Service Architecture

```
┌─────────────────────┐
│   Local Machine     │
│                     │
│  ┌───────────────┐  │
│  │  FastAPI App  │  │ ← Hot reload enabled
│  │  (Port 8000)  │  │
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │  Docker       │  │
│  │  ┌─────────┐  │  │
│  │  │  Redis  │  │  │ ← Port 6379 exposed
│  │  └─────────┘  │  │
│  │  ┌─────────┐  │  │
│  │  │ Celery  │  │  │ ← Mounted local code
│  │  └─────────┘  │  │
│  └───────────────┘  │
└─────────────────────┘
```

## Environment Variables

The `.env` file is automatically loaded. Key variables:
- `MISTRAL_API_KEY`: Required for OCR functionality
- `REDIS_HOST`: Set to `localhost` for hybrid mode
- `CELERY_BROKER_URL`: Points to Docker Redis

## Troubleshooting

### Docker not installed
```bash
Error: Docker is not installed. Please install Docker to run dependencies.
```
**Solution**: Install Docker from https://docs.docker.com/get-docker/

### Docker daemon not running
```bash
Error: Docker is not running. Please start Docker daemon.
```
**Solution**: Start Docker Desktop or `sudo systemctl start docker`

### Port already in use
```bash
Error: bind: address already in use
```
**Solution**: Stop conflicting services or change ports in docker-compose.dev.yml

### Redis connection refused
**Solution**: Ensure Redis container is running:
```bash
docker-compose -f docker-compose.dev.yml ps
docker-compose -f docker-compose.dev.yml logs redis
```

## Advanced Usage

### Adding PostgreSQL
Uncomment the postgres service in `docker-compose.dev.yml`:
```yaml
postgres:
  image: postgres:15-alpine
  # ... configuration
```

### Monitoring with Flower
Uncomment the flower service in `docker-compose.dev.yml` to monitor Celery tasks:
```yaml
flower:
  # ... configuration
  ports:
    - "5555:5555"
```
Access at http://localhost:5555

### Custom Redis Configuration
Modify the Redis command in `docker-compose.dev.yml`:
```yaml
redis:
  command: redis-server --appendonly yes --maxmemory 256mb
```

## Benefits of This Setup

1. **No Local Dependencies**: No need to install Redis or Celery locally
2. **Consistent Environment**: Same versions across all developer machines
3. **Hot Reload**: FastAPI changes reflect immediately
4. **Easy Cleanup**: Docker containers are automatically removed
5. **Resource Efficient**: Minimal Docker services for development
6. **Production-Ready Path**: Easy transition to full containerization

## API Endpoints

Once running, the application provides:
- API Documentation: http://localhost:8000/api/v1/docs
- Health Check: http://localhost:8000/health
- Document Upload: POST http://localhost:8000/api/v1/documents/upload

## Next Steps

1. Upload a test document to process
2. Monitor Celery tasks (if Flower is enabled)
3. Check Redis for cached data
4. Review logs for debugging

For production deployment, see the main README.md.