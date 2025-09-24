#!/bin/bash

# Document Ingestion Agent - Server Startup Script

echo "Starting Document Ingestion Agent..."

# Cleanup function to stop Docker services on exit
cleanup() {
    echo ""
    echo "Stopping Docker services..."
    docker-compose -f docker-compose.dev.yml down
    echo "Cleanup complete."
    exit 0
}

# Set up trap to call cleanup function on script exit
trap cleanup EXIT INT TERM

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    # Export variables from .env file, ignoring comments and empty lines
    set -a
    source <(grep -v '^#' .env | grep -v '^$' | sed 's/\r$//')
    set +a
fi

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
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed. Please install Docker to run dependencies."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "Error: Docker is not running. Please start Docker daemon."
        exit 1
    fi
    
    # Start Redis and Celery using Docker Compose
    echo "Starting Redis in Docker..."
    docker-compose -f docker-compose.dev.yml up -d redis
    
    # Wait for Redis to be healthy
    echo "Waiting for Redis to be ready..."
    for i in {1..30}; do
        if docker-compose -f docker-compose.dev.yml exec -T redis redis-cli ping &> /dev/null; then
            echo "Redis is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "Error: Redis failed to start within 30 seconds"
            docker-compose -f docker-compose.dev.yml logs redis
            exit 1
        fi
        sleep 1
    done
    
    # Start Celery worker in Docker
    echo "Starting Celery worker in Docker..."
    docker-compose -f docker-compose.dev.yml up -d celery
    
    # Wait for Celery to be ready
    echo "Waiting for Celery worker to start..."
    sleep 3
    
    # Show running services
    echo ""
    echo "Docker services status:"
    docker-compose -f docker-compose.dev.yml ps
    echo ""
    
    # Start FastAPI application
    echo "Starting FastAPI application..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi