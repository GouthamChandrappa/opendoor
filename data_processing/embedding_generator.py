"""
Embedding generator module for door installation assistant.
Handles creation of vector embeddings for text chunks.
"""

import logging
from typing import List, Dict, Any, Union, Optional
import numpy as np
import time
import os
import importlib
from abc import ABC, abstractmethod

# Import openai conditionally to handle import errors
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not available. Using mock embeddings by default.")

from config.app_config import get_config

logger = logging.getLogger(__name__)

class BaseEmbeddingGenerator(ABC):
    """Base class for embedding generators."""
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for a single text chunk."""
        pass
    
    @abstractmethod
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of text chunks."""
        pass

class EmbeddingGenerator(BaseEmbeddingGenerator):
    """Generates embeddings for text chunks."""
    
    def __init__(self, config=None):
        self.config = config or get_config().embedding
        self.dimension = getattr(self.config, "dimension", 1536)  # Default dimension
        self.provider = None
        self._setup_provider()
    
    def _setup_provider(self):
        """Set up the embedding provider based on configuration."""
        provider_name = self.config.provider.lower()
        
        if provider_name == "openai":
            self._setup_openai()
            self.provider = "openai"
        elif provider_name == "huggingface":
            self._setup_huggingface()
            self.provider = "huggingface"
        elif provider_name == "mock":
            self.provider = "mock"
        else:
            logger.warning(f"Unsupported embedding provider: {provider_name}. Using mock embeddings.")
            self.provider = "mock"
    
    def _setup_openai(self):
        """Set up OpenAI client."""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library is not installed. Install with 'pip install openai'")
            
        api_key = getattr(self.config, "api_key", None) or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key not provided. Either set it in the configuration "
                "or provide it as an environment variable OPENAI_API_KEY"
            )
        
        openai.api_key = api_key
    
    def _setup_huggingface(self):
        """Set up HuggingFace sentence transformers."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.config.model_name)
        except ImportError:
            raise ImportError(
                "Sentence transformers library is not installed. "
                "Install with 'pip install sentence-transformers'"
            )
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for a single text chunk."""
        if not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.dimension
            
        if self.provider == "openai":
            return self._generate_openai_embedding(text)
        elif self.provider == "huggingface":
            return self._generate_huggingface_embedding(text)
        else:
            # Fall back to mock embeddings
            return self._generate_mock_embedding(text)
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of text chunks."""
        if not texts:
            return []
            
        # Filter out empty texts
        filtered_texts = [text.strip() for text in texts]
        filtered_indices = [i for i, text in enumerate(filtered_texts) if text]
        
        if not filtered_indices:
            return [[0.0] * self.dimension] * len(texts)
            
        if self.provider == "openai":
            embeddings = self._generate_openai_embeddings_batch([texts[i] for i in filtered_indices])
        elif self.provider == "huggingface":
            embeddings = self._generate_huggingface_embeddings_batch([texts[i] for i in filtered_indices])
        else:
            embeddings = [self._generate_mock_embedding(texts[i]) for i in filtered_indices]
        
        # Reconstruct the full list with zero vectors for empty texts
        result = [[0.0] * self.dimension] * len(texts)
        for idx, embedding in zip(filtered_indices, embeddings):
            result[idx] = embedding
            
        return result
    
    def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate an embedding using OpenAI."""
        if not OPENAI_AVAILABLE:
            return self._generate_mock_embedding(text)
            
        try:
            # Retry mechanism for API rate limits
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    response = openai.Embedding.create(
                        model=getattr(self.config, "model_name", "text-embedding-3-small"),
                        input=text
                    )
                    
                    # Extract and return the embedding
                    if "data" in response and len(response["data"]) > 0:
                        return response["data"][0]["embedding"]
                    else:
                        logger.error(f"Unexpected OpenAI API response format: {response}")
                        return self._generate_mock_embedding(text)
                        
                except Exception as rate_error:
                    # Check if it's a rate limit error
                    is_rate_error = (
                        hasattr(openai, "error") and 
                        isinstance(rate_error, openai.error.RateLimitError)
                    )
                    
                    if is_rate_error and attempt < max_retries - 1:
                        logger.warning(f"Rate limit hit, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise
        
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {str(e)}")
            # Fall back to mock embedding in case of error
            return self._generate_mock_embedding(text)
    
    def _generate_openai_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts using OpenAI."""
        if not OPENAI_AVAILABLE:
            return [self._generate_mock_embedding(text) for text in texts]
            
        embeddings = []
        batch_size = getattr(self.config, "batch_size", 100)
        
        # Process in batches to avoid API limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            try:
                # Retry mechanism for API rate limits
                max_retries = 3
                retry_delay = 1
                
                for attempt in range(max_retries):
                    try:
                        response = openai.Embedding.create(
                            model=getattr(self.config, "model_name", "text-embedding-3-small"),
                            input=batch
                        )
                        
                        if "data" in response and len(response["data"]) == len(batch):
                            batch_embeddings = [item["embedding"] for item in response["data"]]
                            embeddings.extend(batch_embeddings)
                            break
                        else:
                            logger.error(f"Unexpected OpenAI API response format: {response}")
                            # Fall back to mock embeddings for this batch
                            embeddings.extend([self._generate_mock_embedding(text) for text in batch])
                            break
                            
                    except Exception as rate_error:
                        is_rate_error = (
                            hasattr(openai, "error") and 
                            isinstance(rate_error, openai.error.RateLimitError)
                        )
                        
                        if is_rate_error and attempt < max_retries - 1:
                            logger.warning(f"Rate limit hit, retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            raise
            
            except Exception as e:
                logger.error(f"Error generating OpenAI embeddings batch: {str(e)}")
                # Fall back to mock embeddings for this batch
                embeddings.extend([self._generate_mock_embedding(text) for text in batch])
        
        return embeddings
    
    def _generate_huggingface_embedding(self, text: str) -> List[float]:
        """Generate an embedding using HuggingFace."""
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating HuggingFace embedding: {str(e)}")
            return self._generate_mock_embedding(text)
    
    def _generate_huggingface_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts using HuggingFace."""
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating HuggingFace embeddings batch: {str(e)}")
            return [self._generate_mock_embedding(text) for text in texts]
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate a mock embedding (deterministic pseudo-random vector)."""
        # Generate a deterministic but seemingly random vector based on the text hash
        text_hash = hash(text) % 10000
        np.random.seed(text_hash)
        return np.random.rand(self.dimension).tolist()

class MockEmbeddingGenerator(BaseEmbeddingGenerator):
    """Mock embedding generator for testing and development."""
    
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate a mock embedding (deterministic pseudo-random vector)."""
        if not text.strip():
            return [0.0] * self.dimension
        
        # Generate a deterministic but seemingly random vector based on the text hash
        text_hash = hash(text) % 10000
        np.random.seed(text_hash)
        return np.random.rand(self.dimension).tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for a batch of texts."""
        return [self.generate_embedding(text) for text in texts]

class SimilarityCalculator:
    """Utility class for calculating similarity between embeddings."""
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (between -1 and 1)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    
    @staticmethod
    def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate Euclidean distance between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Euclidean distance (lower is more similar)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        return np.linalg.norm(vec1 - vec2)
    
    @staticmethod
    def dot_product(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate dot product between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Dot product
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        return np.dot(vec1, vec2)
    
    @staticmethod
    def batch_cosine_similarity(query_vec: List[float], doc_vecs: List[List[float]]) -> List[float]:
        """
        Calculate cosine similarity between a query vector and multiple document vectors.
        
        Args:
            query_vec: Query vector
            doc_vecs: List of document vectors
            
        Returns:
            List of similarity scores
        """
        query_vec = np.array(query_vec)
        doc_vecs = np.array(doc_vecs)
        
        # Normalize query vector
        query_norm = np.linalg.norm(query_vec)
        if query_norm > 0:
            query_vec = query_vec / query_norm
        
        # Normalize document vectors
        doc_norms = np.linalg.norm(doc_vecs, axis=1, keepdims=True)
        doc_norms[doc_norms == 0] = 1.0  # Avoid division by zero
        normalized_docs = doc_vecs / doc_norms
        
        # Calculate similarities
        similarities = np.dot(normalized_docs, query_vec)
        
        return similarities.tolist()