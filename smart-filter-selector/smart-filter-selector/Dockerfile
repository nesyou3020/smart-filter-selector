# Dockerfile for Smart Filter Selector Flask App
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app
# Copy chroma_db embeddings
COPY ./data/chroma_db /app/data/chroma_db

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install uv \
    && uv sync

EXPOSE 8000

# Run the Flask app
CMD ["uv", "run", "run.py"]
