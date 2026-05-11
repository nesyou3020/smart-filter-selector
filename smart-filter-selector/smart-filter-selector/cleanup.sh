#!/bin/bash

echo "Cleaning up cache and temporary files..."

# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} +

# Remove Python bytecode and log files
find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name "*.log" \) -delete

# Remove virtual environment
echo "Removing virtual environment..."
rm -rf .venv

# Remove generated data files
echo "Removing generated data files 'chroma_db'..."
rm -rf data/chroma_db

# Remove WSL temporary files
echo "Removing WSL temporary files..."
tmp_dir="/mnt/wsl/tmp"
if [ -d "$tmp_dir" ]; then
    echo "Removing WSL temporary files..."
    rm -rf "$tmp_dir"/*
fi

# Clean up uv temporary files
echo "Cleaning up uv temporary files..."
uv clean

# Completion message
echo "Cleanup complete!"