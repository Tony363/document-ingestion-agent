#!/bin/bash

# Start Docker dependencies for local development

echo "Starting Docker dependencies for Document Ingestion Agent..."

# Check Docker availability
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "Error: Docker daemon is not running."
    exit 1
fi

# Start services
echo "Starting Redis..."
docker-compose -f docker-compose.dev.yml up -d redis

# Wait for Redis
echo "Waiting for Redis to be ready..."
for i in {1..30}; do
    if docker-compose -f docker-compose.dev.yml exec -T redis redis-cli ping &> /dev/null; then
        echo "✓ Redis is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ Redis failed to start"
        docker-compose -f docker-compose.dev.yml logs redis
        exit 1
    fi
    sleep 1
done

# Start Celery
echo "Starting Celery worker..."
docker-compose -f docker-compose.dev.yml up -d celery

# Wait a moment for Celery
sleep 3

# Show status
echo ""
echo "=== Docker Services Status ==="
docker-compose -f docker-compose.dev.yml ps
echo ""
echo "Services are ready! You can now run the FastAPI app locally:"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "To stop services, run: ./scripts/stop-docker-deps.sh"