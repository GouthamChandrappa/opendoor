# door_installation_assistant/retrieval/vector_retriever.py
import logging
from typing import List, Dict, Any, Optional

from .bm25_retriever import RetrieverComponent
from ..vector_storage.vector_store import VectorStore
from ..data_processing.embedding_generator import EmbeddingGenerator

logger = logging.getLogger(__name__)

class VectorRetriever(RetrieverComponent):
    """Vector-based dense retrieval component."""
    
    def __init__(self, vector_store: VectorStore, embedding_generator: EmbeddingGenerator):
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
    
    def retrieve(
        self,
        query: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents using vector similarity.
        
        Args:
            query: Query string.
            filter_dict: Filter criteria for retrieval.
            top_k: Number of documents to retrieve.
            **kwargs: Additional keyword arguments.
            
        Returns:
            List of retrieved documents.
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)
        
        # Perform similarity search
        results = self.vector_store.similarity_search(
            embedding=query_embedding,
            filter_dict=filter_dict,
            top_k=top_k
        )
        
        # Add retrieval source information
        for result in results:
            result["retrieval_source"] = "vector"
            result["embedding"] = query_embedding  # Add for potential reranking
        
        return results

class HybridRetriever(RetrieverComponent):
    """Hybrid retrieval component combining BM25 and vector retrieval."""
    
    def __init__(self, vector_store: VectorStore, embedding_generator: EmbeddingGenerator):
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
    
    def retrieve(
        self,
        query: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        alpha: Optional[float] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents using hybrid search (BM25 + vector).
        
        Args:
            query: Query string.
            filter_dict: Filter criteria for retrieval.
            top_k: Number of documents to retrieve.
            alpha: Weight for combining keyword and vector scores (0=keyword only, 1=vector only).
            **kwargs: Additional keyword arguments.
            
        Returns:
            List of retrieved documents.
        """
        # Use configured alpha value if not provided
        if alpha is None:
            alpha = 0.5  # Equal weight by default
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)
        
        # Perform hybrid search
        results = self.vector_store.hybrid_search(
            query=query,
            query_embedding=query_embedding,
            filter_dict=filter_dict,
            top_k=top_k,
            alpha=alpha
        )
        
        # Add retrieval source information
        for result in results:
            result["retrieval_source"] = "hybrid"
            result["embedding"] = query_embedding  # Add for potential reranking
        
        return results