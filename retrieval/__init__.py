# door_installation_assistant/retrieval/__init__.py
"""
Retrieval package for Door Installation Assistant.

This package provides retrieval capabilities for the Door Installation Assistant,
including BM25 retrieval, vector retrieval, and reranking functionality.
"""

from .retrieval_pipeline import RetrievalPipeline
from .bm25_retriever import BM25Retriever
from .vector_retriever import VectorRetriever
from .reranker import Reranker

def get_retrieval_pipeline(**kwargs):
    """
    Factory function to get a retrieval pipeline instance.
    
    Args:
        **kwargs: Additional keyword arguments for the retrieval pipeline.
        
    Returns:
        RetrievalPipeline instance.
    """
    return RetrievalPipeline(**kwargs)

__all__ = [
    'RetrievalPipeline',
    'BM25Retriever',
    'VectorRetriever',
    'Reranker',
    'get_retrieval_pipeline',
]