
class Config:
    # Ollama Configuration
    OLLAMA_URL = 'http://localhost:11434'
    OLLAMA_EMBEDDING_MODEL = 'mxbai-embed-large'
    OLLAMA_LLM_MODEL = 'llama3.1:8b'

    # Flask Configuration
    FLASK_PORT = 8000
    FLASK_DEBUG = True

    # Application Configuration
    MIN_CONFIDENCE_THRESHOLD = 0.8
    MIN_CONFIDENCE_THRESHOLD_EMBEDDING = 0.54
    TOP_K_SIMILARITY = 20

    # File Paths
    FILTER_CONFIG_PATH = 'data/values_with_context.json'
    EMBEDDINGS_PATH = 'data/embeddings.json'
    PERSIST_DIRECTORY = 'data/chroma_db'
    EMBEDDINGS_COLLECTION_NAME = "filter_embeddings"


config = Config()
