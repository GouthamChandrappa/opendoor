# door_installation_assistant/retrieval/retrieval_pipeline.py
import logging
import re
from typing import Dict, Any, List, Optional, Tuple

from ..config.app_config import get_config
from ..data_processing.embedding_generator import EmbeddingGenerator
from ..vector_storage.qdrant_store import QdrantStore
from .bm25_retriever import BM25Retriever 
from .vector_retriever import VectorRetriever, HybridRetriever
from .reranker import Reranker

logger = logging.getLogger(__name__)

class RetrievalPipeline:
    """Orchestrates the retrieval process."""
    
    def __init__(self):
        self.config = get_config().retrieval
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = QdrantStore()
        self.vector_store.initialize()
        
        # Create retrievers
        self.bm25_retriever = BM25Retriever(self.vector_store)
        self.vector_retriever = VectorRetriever(self.vector_store, self.embedding_generator)
        self.hybrid_retriever = HybridRetriever(self.vector_store, self.embedding_generator)
        
        # Create reranker if enabled
        self.reranker = Reranker() if self.config.use_reranking else None
    
    def retrieve(
        self,
        query: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        retrieval_type: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents for a query.
        
        Args:
            query: Query string.
            filter_dict: Filter criteria for retrieval.
            retrieval_type: Type of retrieval to use (hybrid, vector, keyword).
            top_k: Number of documents to retrieve.
            
        Returns:
            List of retrieved documents.
        """
        # Use configured values if not provided
        if retrieval_type is None:
            retrieval_type = self.config.retrieval_type
        
        if top_k is None:
            top_k = self.config.top_k
        
        # Preprocess query
        processed_query = self._preprocess_query(query)
        
        # Extract door-specific information for better filtering
        door_filter = self._extract_door_filter(processed_query, filter_dict)
        
        # Perform initial retrieval
        if retrieval_type == "hybrid":
            results = self.hybrid_retriever.retrieve(
                query=processed_query,
                filter_dict=door_filter,
                top_k=top_k * 2  # Retrieve more for reranking
            )
        elif retrieval_type == "vector":
            results = self.vector_retriever.retrieve(
                query=processed_query,
                filter_dict=door_filter,
                top_k=top_k * 2  # Retrieve more for reranking
            )
        elif retrieval_type == "keyword":
            results = self.bm25_retriever.retrieve(
                query=processed_query,
                filter_dict=door_filter,
                top_k=top_k * 2  # Retrieve more for reranking
            )
        else:
            # Default to hybrid
            results = self.hybrid_retriever.retrieve(
                query=processed_query,
                filter_dict=door_filter,
                top_k=top_k * 2  # Retrieve more for reranking
            )
        
        # Rerank results if enabled
        if self.reranker and self.config.use_reranking:
            reranked_results = self.reranker.rerank(
                query=processed_query,
                documents=results,
                top_k=min(top_k, self.config.reranker_top_k)
            )
            return reranked_results
        
        # Otherwise, just return top results
        return results[:top_k]
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess query for retrieval."""
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    def _extract_door_filter(
        self,
        query: str,
        user_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract door-specific filters from query."""
        # Start with user-provided filter
        door_filter = user_filter.copy() if user_filter else {}
        
        # Look for door type mentions
        query_lower = query.lower()
        
        # Door categories
        if "interior" in query_lower and "door_category" not in door_filter:
            door_filter["door_category"] = "interior"
        elif "exterior" in query_lower and "door_category" not in door_filter:
            door_filter["door_category"] = "exterior"
        
        # Interior door types
        if "bifold" in query_lower and "door_type" not in door_filter:
            door_filter["door_type"] = "bifold"
        elif "prehung" in query_lower and "door_type" not in door_filter:
            door_filter["door_type"] = "prehung"
        
        # Exterior door types
        elif "dentil shelf" in query_lower and "door_type" not in door_filter:
            door_filter["door_type"] = "dentil shelf"
        elif "entry door" in query_lower and "door_type" not in door_filter:
            door_filter["door_type"] = "entry door"
        elif "patio door" in query_lower and "door_type" not in door_filter:
            door_filter["door_type"] = "patio door"
        
        # Look for installation step mentions
        if ("step" in query_lower or "install" in query_lower) and "content_type" not in door_filter:
            door_filter["content_type"] = "installation_step"
        
        # Look for tool mentions
        if "tool" in query_lower and "content_type" not in door_filter:
            door_filter["content_type"] = "tool"
        
        # Look for component mentions
        if ("component" in query_lower or "part" in query_lower) and "content_type" not in door_filter:
            door_filter["content_type"] = "component"
        
        return door_filter