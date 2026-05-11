#!/bin/bash

echo "🚀 Smart Filter Selector - Quick Start"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed!"
    echo "   Please install from: https://ollama.com"
    exit 1
fi

echo "✅ Ollama is installed"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "⚠️  Ollama is not running. Starting Ollama..."
    ollama serve &
    OLLAMA_PID=$!
    sleep 3
else
    echo "✅ Ollama is running"
fi

# Pull required models
echo ""
echo "📥 Pulling required models..."
echo "   This may take a few minutes..."

if ! ollama list | grep -q "mxbai-embed-large"; then
    # echo "   Pulling nomic-embed-text..."
    # ollama pull nomic-embed-text
    echo "   Pulling mxbai-embed-large..."
    ollama pull mxbai-embed-large
else
    echo "   ✅ mxbai-embed-large already available"
fi

if ! ollama list | grep -q "llama3.1:8b"; then
    echo "   Pulling llama3.1:8b..."
    ollama pull llama3.1:8b
else
    echo "   ✅ llama3.1:8b already available"
fi

# Check Python virtual environment
echo ""
echo "🐍 Setting up Python environment..."

if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    uv sync
fi

echo "   Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "   Installing dependencies..."
uv sync

# Generate embeddings if not exists
if [ ! -d "data/chroma_db" ]; then
    echo "📊 Generating embeddings..."
    echo "   This will take 2-3 minutes..."
    uv run scripts/generate_embeddings.py
else
    echo ""
    echo "✅ Embeddings already exist"
fi

# Start the application
echo ""
echo "🎉 Starting Flask Application..."

uv run run.py