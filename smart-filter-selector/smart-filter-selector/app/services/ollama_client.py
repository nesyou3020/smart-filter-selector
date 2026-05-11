from typing import List

import requests

from app.config import config


class OllamaClient:
    """Client for interacting with Ollama API."""

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for given text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector as list of floats
        """
        url = f"{config.OLLAMA_URL}/api/embeddings"
        payload = {
            "model": config.OLLAMA_EMBEDDING_MODEL,
            "prompt": text,
            "use_gpu": True
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        return response.json()["embedding"]

    def check_connection(self) -> bool:
        """
        Check if Ollama service is accessible.

        Returns:
            True if connected, False otherwise
        """
        try:
            response = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False