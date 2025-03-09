# door_installation_assistant/vector_storage/__init__.py
"""
Vector storage package for Door Installation Assistant.

This package provides vector storage capabilities for the Door Installation Assistant,
including the abstract vector store interface and specific implementations like Qdrant.
"""

from .vector_store import VectorStore
from .qdrant_store import QdrantStore

def get_vector_store(provider: str = "qdrant", **kwargs):
    """
    Factory function to get a vector store instance.
    
    Args:
        provider: Vector store provider name.
        **kwargs: Additional keyword arguments for the vector store.
        
    Returns:
        VectorStore instance.
    """
    if provider.lower() == "qdrant":
        return QdrantStore(**kwargs)
    else:
        raise ValueError(f"Unsupported vector store provider: {provider}")

__all__ = [
    'VectorStore',
    'QdrantStore',
    'get_vector_store',
]