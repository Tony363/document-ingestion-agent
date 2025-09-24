#!/bin/bash

# Document Ingestion Agent v2.0 - Server Startup Script

echo "================================================"
echo "Document Ingestion Agent v2.0 - Starting Server"
echo "================================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your Mistral API key"
    echo "   The server will run in simulation mode without a valid API key"
    echo ""
fi

# Create upload directory if it doesn't exist
mkdir -p /tmp/document-uploads

# Install dependencies if not already installed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Run the server
echo ""
echo "🚀 Starting FastAPI server..."
echo "   API Docs: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================================"

# Run with uvicorn
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000