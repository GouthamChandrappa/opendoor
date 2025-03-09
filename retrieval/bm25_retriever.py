# door_installation_assistant/retrieval/bm25_retriever.py
import logging
import re
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from ..vector_storage.vector_store import VectorStore

logger = logging.getLogger(__name__)

class RetrieverComponent(ABC):
    """Abstract base class for retriever components."""
    
    @abstractmethod
    def retrieve(
        self,
        query: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents for a query.
        
        Args:
            query: Query string.
            **kwargs: Additional keyword arguments.
            
        Returns:
            List of retrieved documents.
        """
        pass

class BM25Retriever(RetrieverComponent):
    """BM25 sparse retrieval component."""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
    
    def retrieve(
        self,
        query: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents using BM25 (keyword-based) retrieval.
        
        Args:
            query: Query string.
            filter_dict: Filter criteria for retrieval.
            top_k: Number of documents to retrieve.
            **kwargs: Additional keyword arguments.
            
        Returns:
            List of retrieved documents.
        """
        # Preprocess query to extract important keywords
        keywords = self._extract_keywords(query)
        keyword_query = " ".join(keywords) if keywords else query
        
        # Perform keyword search
        results = self.vector_store.keyword_search(
            query=keyword_query,
            filter_dict=filter_dict,
            top_k=top_k
        )
        
        # Add retrieval source information
        for result in results:
            result["retrieval_source"] = "bm25"
        
        return results
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from a query."""
        # Remove stopwords and keep only important terms
        stopwords = {
            "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
            "be", "been", "being", "in", "on", "at", "to", "for", "with", "about",
            "by", "this", "that", "these", "those", "it", "of", "from", "how",
            "what", "when", "where", "who", "which", "why", "can", "could", "will",
            "would", "shall", "should", "may", "might", "must", "do", "does", "did",
            "have", "has", "had", "having"
        }
        
        # Split query into words
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter out stopwords
        keywords = [word for word in words if word not in stopwords]
        
        # Add domain-specific terms that should always be preserved
        door_terms = {
            "door", "doors", "installation", "install", "step", "steps", "procedure",
            "hardware", "tool", "tools", "component", "components", "hinge", "hinges",
            "frame", "jamb", "threshold", "knob", "handle", "lock", "strike", "plate",
            "gap", "level", "plumb", "square", "shim", "nail", "screw", "drill",
            "measurement", "width", "height", "opening", "rough", "interior", "exterior",
            "prehung", "bifold", "entry", "patio", "dentil", "shelf"
        }
        
        # Ensure door-specific terms are preserved even if they're normally stopwords
        for word in words:
            if word in door_terms and word not in keywords:
                keywords.append(word)
        
        return keywords