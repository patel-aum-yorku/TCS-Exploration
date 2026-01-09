#!/bin/bash
# Quick start script for Financial RAG Assistant

set -e  # Exit on error

echo "=================================================="
echo "  Financial RAG Assistant - Quick Start"
echo "=================================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment not found."
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install/update requirements
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  .env file not found!"
    echo "Please create .env file with your API keys:"
    echo ""
    echo "GOOGLE_API_KEY=your_key_here"
    echo "AWS_ACCESS_KEY_ID=your_key_here"
    echo "AWS_SECRET_ACCESS_KEY=your_secret_here"
    echo "AWS_DEFAULT_REGION=us-east-1"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
fi

# Check PostgreSQL
echo "🔍 Checking PostgreSQL..."
if ! docker ps | grep -q financial-rag-db; then
    echo "⚠️  PostgreSQL container not found."
    echo "Starting PostgreSQL..."
    docker run --name financial-rag-db \
        -e POSTGRES_PASSWORD=root \
        -e POSTGRES_USER=postgres \
        -p 5432:5432 -d pgvector/pgvector:pg17
    echo "✅ PostgreSQL started"
    sleep 3
else
    echo "✅ PostgreSQL is running"
fi

echo ""
echo "=================================================="
echo "  Starting Application..."
echo "=================================================="
echo ""

# Launch the application
python frontend/launcher.py
