# door_installation_assistant/retrieval/reranker.py
import logging
import os
import re
from typing import List, Dict, Any

from ..config.app_config import get_config

logger = logging.getLogger(__name__)

class Reranker:
    """Reranks documents based on relevance to the query."""
    
    def __init__(self):
        self.config = get_config().retrieval
        self._setup_reranker()
    
    def _setup_reranker(self):
        """Set up the reranker based on configuration."""
        reranker_model = self.config.reranker_model.lower()
        
        try:
            if reranker_model == "cohere":
                import cohere
                from cohere import Client
                
                self.reranker_type = "cohere"
                api_key = os.environ.get("COHERE_API_KEY")
                if not api_key:
                    logger.warning("Cohere API key not found. Reranker will not work.")
                    self.reranker_type = "simple"
                else:
                    self.reranker = Client(api_key)
            else:
                logger.info(f"Using simple reranking (no external reranker)")
                self.reranker_type = "simple"
        
        except ImportError:
            logger.warning(f"Could not import {reranker_model} library. Using simple reranking.")
            self.reranker_type = "simple"
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on relevance to the query.
        
        Args:
            query: Query string.
            documents: Documents to rerank.
            top_k: Number of documents to return after reranking.
            
        Returns:
            List of reranked documents.
        """
        if not documents:
            return []
        
        if self.reranker_type == "cohere":
            return self._rerank_with_cohere(query, documents, top_k)
        else:
            return self._simple_rerank(query, documents, top_k)
    
    def _rerank_with_cohere(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Rerank documents using Cohere's reranking API."""
        try:
            # Extract document texts
            document_texts = [doc["text"] for doc in documents]
            
            # Perform reranking
            response = self.reranker.rerank(
                query=query,
                documents=document_texts,
                top_n=min(top_k, len(documents)),
                model="rerank-english-v2.0"
            )
            
            # Reorder documents based on reranking results
            reranked_documents = []
            
            for result in response.results:
                # Find the original document
                original_document = documents[result.index]
                
                # Create a copy to avoid modifying the original
                reranked_document = original_document.copy()
                
                # Update the relevance score
                reranked_document["original_score"] = reranked_document.get("score", 0.0)
                reranked_document["score"] = result.relevance_score
                reranked_document["rerank_source"] = "cohere"
                
                reranked_documents.append(reranked_document)
            
            return reranked_documents
        
        except Exception as e:
            logger.error(f"Error during Cohere reranking: {str(e)}")
            # Fall back to simple reranking
            return self._simple_rerank(query, documents, top_k)
    
    def _simple_rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Simple document reranking based on query term matching."""
        try:
            # Extract query terms for matching
            query_terms = set(re.findall(r'\b\w+\b', query.lower()))
            
            # Score documents based on term overlap and position
            scored_documents = []
            
            for doc in documents:
                # Create a copy to avoid modifying the original
                scored_doc = doc.copy()
                
                # Get original score and text
                original_score = scored_doc.get("score", 0.0)
                text = scored_doc.get("text", "").lower()
                
                # Count term matches
                term_matches = 0
                term_positions = []
                
                for term in query_terms:
                    matches = list(re.finditer(r'\b' + re.escape(term) + r'\b', text))
                    term_matches += len(matches)
                    
                    # Record positions of matches
                    for match in matches:
                        term_positions.append(match.start())
                
                # Compute position score (earlier matches are better)
                position_score = 0.0
                if term_positions:
                    # Normalize positions by text length
                    normalized_positions = [pos / max(1, len(text)) for pos in term_positions]
                    # Earlier positions get higher scores
                    position_score = sum(1.0 - pos for pos in normalized_positions) / len(term_positions)
                
                # Compute term density score (matches close together are better)
                density_score = 0.0
                if len(term_positions) > 1:
                    # Sort positions
                    term_positions.sort()
                    
                    # Calculate gaps between adjacent positions
                    gaps = [term_positions[i+1] - term_positions[i] for i in range(len(term_positions) - 1)]
                    
                    # Smaller gaps are better
                    avg_gap = sum(gaps) / len(gaps)
                    density_score = 1.0 / (1.0 + (avg_gap / 100.0))  # Normalize to [0, 1]
                
                # Compute installation step/procedure bonus
                content_type_bonus = 0.0
                metadata = scored_doc.get("metadata", {})
                content_type = metadata.get("content_type", "").lower()
                
                if "installation_step" in content_type or "procedure" in content_type:
                    content_type_bonus = 0.2  # Boost installation procedures
                
                # Compute final score
                # Weights for different factors
                term_weight = 0.4
                position_weight = 0.2
                density_weight = 0.1
                original_weight = 0.2
                bonus_weight = 0.1
                
                # Normalize term matches by query length
                normalized_term_matches = min(1.0, term_matches / max(1, len(query_terms)))
                
                final_score = (
                    term_weight * normalized_term_matches +
                    position_weight * position_score +
                    density_weight * density_score +
                    original_weight * original_score +
                    bonus_weight * content_type_bonus
                )
                
                scored_doc["original_score"] = original_score
                scored_doc["score"] = final_score
                scored_doc["rerank_source"] = "simple"
                
                scored_documents.append(scored_doc)
            
            # Sort by score and limit to top_k
            reranked_documents = sorted(scored_documents, key=lambda x: x["score"], reverse=True)[:top_k]
            
            return reranked_documents
        
        except Exception as e:
            logger.error(f"Error during simple reranking: {str(e)}")
            # Return original documents sorted by their original scores
            sorted_documents = sorted(documents, key=lambda x: x.get("score", 0.0), reverse=True)[:top_k]
            return sorted_documents