import numpy as np
from typing import List

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec_a: First vector
        vec_b: Second vector

    Returns:
        Cosine similarity score (0 to 1)
    """
    a = np.array(vec_a)
    b = np.array(vec_b)

    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    similarity = dot_product / (norm_a * norm_b)
    return float(similarity)

def batch_cosine_similarity(query_vec: List[float], vectors: List[List[float]]) -> List[float]:
    """
    Calculate cosine similarity between a query vector and multiple vectors.

    Args:
        query_vec: Query vector
        vectors: List of vectors to compare against

    Returns:
        List of similarity scores
    """
    query = np.array(query_vec)
    matrix = np.array(vectors)

    dot_products = np.dot(matrix, query)
    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query)

    # Avoid division by zero
    norms = np.where(norms == 0, 1e-10, norms)

    similarities = dot_products / norms
    return similarities.tolist()