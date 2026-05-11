import logging
import os
import sys
import uuid

import chromadb
from chromadb.config import Settings
from tqdm import tqdm

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
    """Generate and store embeddings for all filter values in ChromaDB."""

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

    # Initialize Chroma client
    logger.info("3️⃣  Initializing ChromaDB client...")
    os.makedirs(config.PERSIST_DIRECTORY, exist_ok=True)

    client = chromadb.PersistentClient(
        path=config.PERSIST_DIRECTORY,
        settings=Settings(anonymized_telemetry=False)
    )
    collection = client.get_or_create_collection(name=config.EMBEDDINGS_COLLECTION_NAME)

    # Generate embeddings
    logger.info(f"4️⃣  Generating embeddings using {config.OLLAMA_EMBEDDING_MODEL}...")

    for filter_value in tqdm(flattened_filters, desc="Generating Embeddings", total=len(flattened_filters)):

        name = filter_value.get('name', '')
        description = filter_value.get('description', '').strip()
        category = filter_value.get('category', '')
        subcategory = filter_value.get('subcategory', '')

        try:
            embedding = ollama_client.generate_embedding(
                f"Item: {name}"
                + f"\nCategory: {category}"
                + (f"\nSubcategory: {subcategory}" if subcategory else "")
                + f"\nDescription: {description}"
            )

            # Ensure all metadata values are safe (convert None → "")
            metadata = {
                "name": str(name),
                "description": str(description),
                "category": str(category),
                "subcategory": str(subcategory)
            }
            # Store in ChromaDB
            collection.add(
                ids=[str(uuid.uuid4())],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[description]
            )

        except Exception as e:
            logger.warning(f"⚠️  Error generating embedding for '{name}': {e}")
            continue

    # Persist and summarize
    logger.info("✅ Embeddings successfully stored in ChromaDB!")
    logger.info(f"Total embeddings: {len(flattened_filters)}")
    logger.info(f"Database path: {config.PERSIST_DIRECTORY}")
    logger.info(f"Collection name: {config.EMBEDDINGS_COLLECTION_NAME}")
    logger.info("🚀 You can now query the embeddings from ChromaDB!")

if __name__ == '__main__':
    generate_embeddings()
