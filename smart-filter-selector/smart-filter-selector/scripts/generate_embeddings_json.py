import json
import logging
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import config
from app.services.ollama_client import OllamaClient
from app.utils.filter_loader import FilterLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("generate_embeddings")

def generate_embeddings():
    """Generate and save embeddings for all filter values."""

    logger.info("🔄 Generating Embeddings for Filter Values")

    # Initialize services
    filter_loader = FilterLoader(config.FILTER_CONFIG_PATH)
    ollama_client = OllamaClient()

    # Check Ollama connection
    logger.info("1️⃣  Checking Ollama connection...")
    if not ollama_client.check_connection():
        logger.error(f"❌ Cannot connect to Ollama! Make sure Ollama is running at {config.OLLAMA_URL}. Run: ollama serve")
        return
    logger.info(f"✅ Connected to Ollama at {config.OLLAMA_URL}")

    # Load filter data
    logger.info("2️⃣  Loading filter configuration...")
    try:
        flattened_filters = filter_loader.flatten_filter_values()
        logger.info(f"✅ Loaded {len(flattened_filters)} filter values")
    except Exception as e:
        logger.error(f"❌ Error loading filters: {e}")
        return

    # Generate embeddings
    logger.info(f"3️⃣  Generating embeddings using {config.OLLAMA_EMBEDDING_MODEL}...")
    embeddings_data = []
    total = len(flattened_filters)

    for idx, (category, subcategory, value) in enumerate(flattened_filters, 1):
        # Create text for embedding
        name = value.get('name', '')
        description = value.get('description', '')
        text = description.strip()

        if not text or text == '.':
            text = name

        try:
            # Generate embedding
            embedding = ollama_client.generate_embedding(text)

            embeddings_data.append({
                'category': category,
                'subcategory': subcategory,
                'value': value,
                'embedding': embedding
            })

            # Progress indicator
            if idx % 10 == 0 or idx == total:
                progress = (idx / total) * 100
                logger.info(f"Progress: {idx}/{total} ({progress:.1f}%) - Last: {name[:50]}")

        except Exception as e:
            logger.warning(f"⚠️  Error generating embedding for '{name}': {e}")
            continue

    # Save embeddings
    logger.info(f"4️⃣  Saving embeddings to {config.EMBEDDINGS_PATH}...")

    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(config.EMBEDDINGS_PATH), exist_ok=True)

    try:
        with open(config.EMBEDDINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(embeddings_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Saved {len(embeddings_data)} embeddings")
    except Exception as e:
        logger.error(f"❌ Error saving embeddings: {e}")
        return

    # Summary
    logger.info("✅ Embedding Generation Complete!")
    logger.info(f"Total embeddings: {len(embeddings_data)}")
    logger.info(f"Categories processed: {len(set(e['category'] for e in embeddings_data))}")
    logger.info(f"Embedding dimension: {len(embeddings_data[0]['embedding']) if embeddings_data else 'N/A'}")
    logger.info(f"🚀 You can now start the Flask application!")
    logger.info("Run: uv run run.py")

if __name__ == '__main__':
    generate_embeddings()