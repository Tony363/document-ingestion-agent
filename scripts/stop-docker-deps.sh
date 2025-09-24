#!/bin/bash

# Stop Docker dependencies for local development

echo "Stopping Docker dependencies..."

# Check Docker availability
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    exit 1
fi

# Stop and remove containers
docker-compose -f docker-compose.dev.yml down

echo "✓ Docker services stopped"