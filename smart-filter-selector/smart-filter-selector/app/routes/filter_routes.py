import logging

import chromadb
from chromadb.config import Settings
from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.config import config
from app.models.request_models import FilterQueryRequest
from app.services.hybrid_selector import HybridFilterSelector
from app.services.ollama_client import OllamaClient

logger = logging.getLogger("smart-filter-selector")
filter_bp = Blueprint('filter', __name__)

# Initialize services
hybrid_selector = HybridFilterSelector()
ollama_client = OllamaClient()
client_db = chromadb.PersistentClient(
    path=config.PERSIST_DIRECTORY,
    settings=Settings(anonymized_telemetry=False)
)

@filter_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    ollama_connected = ollama_client.check_connection()
    embeddings_loaded = hybrid_selector.is_ready()

    status = "healthy" if (ollama_connected and embeddings_loaded) else "unhealthy"

    return jsonify({
        'status': status,
        'ollama_connected': ollama_connected,
        'embeddings_loaded': embeddings_loaded
    })

@filter_bp.route('/api/filter/analyze-query', methods=['POST'])
def analyze_query():
    """Analyze query and return reduced filter subset."""
    try:
        # Parse request
        data = request.get_json()
        logger.info(f"🔍 Received query analysis request: {data}")

        # Validate with Pydantic
        try:
            query_request = FilterQueryRequest(**data)
        except ValidationError as e:
            return jsonify({'error': 'Invalid request', 'details': e.errors()}), 422

        # Check if service is ready
        if not hybrid_selector.is_ready():
            return jsonify(
                {
                    'error': 'Service not ready',
                    'message': 'Embeddings not loaded. Please run: python scripts/generate_embeddings.py'
                }
            ), 503

        # Process query
        result = hybrid_selector.select_filters(
            query=query_request.query,
            max_filters=query_request.options.maxFiltersPerCategory,
            min_confidence=query_request.options.minConfidence
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"❌ Error processing query: {e}")
        return jsonify({'error': str(e)}), 500

@filter_bp.route('/api/filter/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint."""
    return jsonify({
        'message': 'Filter service is running!',
        'service_ready': hybrid_selector.is_ready()
    })

@filter_bp.route('/api/filter/embeddings', methods=['GET'])
def list_embeddings():
    data = request.get_json()
    logger.info(f"🔍 Received request to list embeddings: {data}")
    # Retrieve embeddings from ChromaDB
    results = client_db.get_collection(
        config.EMBEDDINGS_COLLECTION_NAME).get(
            include=["metadatas", "embeddings"],
            limit=data.get("limit", 10)
    )
    # Return embeddings
    return jsonify(list(
        {
            "id": i,
            "metadata": meta,
            "embeddings": embedding.tolist() if hasattr(embedding, "tolist") else embedding
        }
        for i, meta, embedding in zip(results["ids"], results["metadatas"], results["embeddings"])
    ))
