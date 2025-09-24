#!/bin/bash

# Document Ingestion Agent - Server Startup Script

echo "Starting Document Ingestion Agent..."

# Check for required environment variables
if [ -z "$MISTRAL_API_KEY" ]; then
    echo "Error: MISTRAL_API_KEY environment variable is not set"
    echo "Please set it using: export MISTRAL_API_KEY='your-api-key'"
    exit 1
fi

# Create necessary directories
mkdir -p uploads
mkdir -p logs

# Check if running with Docker
if [ "$USE_DOCKER" = "true" ]; then
    echo "Starting with Docker Compose..."
    docker-compose up --build
else
    echo "Starting in local development mode..."
    
    # Install dependencies if needed
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi
    
    # Start Redis if not running
    if ! pgrep -x "redis-server" > /dev/null; then
        echo "Starting Redis..."
        redis-server --daemonize yes
    fi
    
    # Start Celery worker in background
    echo "Starting Celery worker..."
    celery -A app.celery_app worker --loglevel=info --detach
    
    # Start FastAPI application
    echo "Starting FastAPI application..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi