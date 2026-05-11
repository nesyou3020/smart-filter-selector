import json
import logging
import os
import re
import unicodedata
from typing import Any, Dict, List

import nltk
from chromadb import PersistentClient
from chromadb.config import Settings
from nltk.corpus import stopwords

from app.config import config
from app.services.ollama_client import OllamaClient
from app.utils.similarity import cosine_similarity

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Safe auto-download if missing
try:
    _ = stopwords.words("english")
except LookupError:
    nltk.download("stopwords", quiet=True)

class EmbeddingService:
    """Service for managing embeddings and similarity search."""

    def __init__(self):
        self.ollama_client = OllamaClient()
        self.embeddings_cache = {}
        self.filter_embeddings = []
        self.chroma_client = self._init_chroma()
        self.load_embeddings()

    def is_loaded(self) -> bool:
        """Check if embeddings are loaded."""
        return len(self.filter_embeddings) > 0

    def _init_chroma(self):
        """Initialize ChromaDB client."""
        client = PersistentClient(path=config.PERSIST_DIRECTORY, settings=Settings(anonymized_telemetry=False))
        logger.info("✅ Connected to ChromaDB")
        return client

    def load_embeddings(self):
        """Load pre-computed embeddings from file."""
        if not os.path.exists(config.PERSIST_DIRECTORY):
            logger.warning(f"⚠️  No embeddings directory found at {config.PERSIST_DIRECTORY}")
            logger.warning(f"   Run: python scripts/generate_embeddings.py")
            return

        results = self.chroma_client.get_collection(
            name=config.EMBEDDINGS_COLLECTION_NAME
        ).get(include=["metadatas", "embeddings"])
        self.filter_embeddings = list(
            {
                "category": meta.get("category", ""),
                "subcategory": meta.get("subcategory", ""),
                "name": meta.get("name", ""),
                "description": meta.get("description", ""),
                "embedding": embedding
            }
            for meta, embedding in zip(results["metadatas"], results["embeddings"])
        )

        logger.info(f"✅ Loaded {len(self.filter_embeddings)} pre-computed embeddings")

    def get_query_embedding(self, query: str) -> List[float]:
        """
            Get embedding for query (with caching).

            Args:
                query: User query

            Returns:
                Embedding vector
        """
        if query in self.embeddings_cache:
            return self.embeddings_cache[query]

        embedding = self.ollama_client.generate_embedding(query)
        self.embeddings_cache[query] = embedding
        return embedding

    def clean_query(self, query: str) -> str:
        """
            Clean query by:
            - Lowercasing
            - Removing accents and special characters
            - Removing digits
            - Removing stopwords (supports English, French, Spanish)
            - Keeping only significant words

            Args:
                query: User query

            Returns:
                Cleaned query string
        """
        # Normalize accents (é → e, ñ → n)
        query = unicodedata.normalize("NFKD", query).encode("ascii", "ignore").decode("utf-8", "ignore")

        # Lowercase & Remove special characters and digits
        query = re.sub(r"[^a-z\s]", " ", query.lower())

        # Tokenize & Remove stopwords and very short tokens & Join back to string
        return " ".join(
            w
            for w in query.split()
            if w not in set(stopwords.words("english")) and
            len(w) > 2
        )

    def find_similar_filters(self, query: str) -> Dict[str, List[Dict]]:
        """
            Find most similar filters using embedding similarity.

            Args:
                query: User query

            Returns:
                Dictionary with top similar filters per category
        """
        if not self.filter_embeddings:
            logger.warning("⚠️  No embeddings loaded! Run: uv run scripts/generate_embeddings.py")
            return {}

        # Get query embedding
        query = self.clean_query(query)
        logger.info(f"🔍 Cleaned query for embedding: '{query}'")
        query_embedding = self.get_query_embedding(query)

        # Calculate similarities for all filters
        # grouped_results = {}

        # for filter_data in self.filter_embeddings:
        #     result = {
        #         'category': filter_data['category'],
        #         'subcategory': filter_data['subcategory'],
        #         # 'value': filter_data['value'],
        #         'name': filter_data['name'],
        #         'description': filter_data['description'],

        #         'score': cosine_similarity(
        #             query_embedding,
        #             filter_data['embedding']
        #         )
        #     }

        #     if result['category'] not in grouped_results:
        #         grouped_results[result['category']] = []
        #     grouped_results[result['category']].append(result)

        # # Sort each category by score and take top-K
        # for category in grouped_results:
        #     grouped_results[category] = list(
        #         filter(
        #         lambda x: x['score'] >= 0, #config.MIN_CONFIDENCE_THRESHOLD_EMBEDDING,
        #         sorted(
        #             grouped_results[category],
        #             key=lambda x: x['score'],
        #             reverse=True
        #         )
        #         )
        #     )[:30] #config.TOP_K_SIMILARITY]

        # return grouped_results

        # return list(
        #     filter(
        #         lambda x: x['score'] >= 0.54, #config.MIN_CONFIDENCE_THRESHOLD_EMBEDDING,
        #         sorted(
        #             list(
        #                     {
        #                         'category': filter_data['category'],
        #                         'subcategory': filter_data['subcategory'],
        #                         'name': filter_data['name'],
        #                         'description': filter_data['description'],
        #                         'score': cosine_similarity(
        #                             query_embedding,
        #                             filter_data['embedding']
        #                         )
        #                     }

        #                 for filter_data in self.filter_embeddings
        #             ),
        #             key=lambda x: x['score'],
        #             reverse=True
        #         )
        #     )
        # )

        return sorted(
            list(
                    {
                        'category': filter_data['category'],
                        'subcategory': filter_data['subcategory'],
                        'name': filter_data['name'],
                        'score': cosine_similarity(
                            query_embedding,
                            filter_data['embedding']
                        )
                    }

                for filter_data in self.filter_embeddings
            ),
            key=lambda x: x['score'],
            reverse=True
        )[:config.TOP_K_SIMILARITY]
