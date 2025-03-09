# door_installation_assistant/data_processing/embedding_generator.py
import logging
from typing import List, Dict, Any, Union, Optional
import numpy as np
import time
import openai
import os

from ..config.app_config import get_config

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generates embeddings for text chunks."""
    
    def __init__(self):
        self.config = get_config().embedding
        self._setup_provider()
    
    def _setup_provider(self):
        """Set up the embedding provider based on configuration."""
        provider = self.config.provider.lower()
        
        if provider == "openai":
            self._setup_openai()
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
    
    def _setup_openai(self):
        """Set up OpenAI client."""
        api_key = self.config.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided.")
        
        openai.api_key = api_key
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for a single text chunk."""
        provider = self.config.provider.lower()
        
        if provider == "openai":
            return self._generate_openai_embedding(text)
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of text chunks."""
        provider = self.config.provider.lower()
        
        if provider == "openai":
            return self._generate_openai_embeddings_batch(texts)
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
    
    def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate an embedding using OpenAI."""
        try:
            # Retry mechanism for API rate limits
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    response = openai.Embedding.create(
                        model=self.config.model_name,
                        input=text
                    )
                    return response["data"][0]["embedding"]
                except openai.error.RateLimitError:
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limit hit, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise
        
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {str(e)}")
            # Return a zero vector of the expected dimension as a fallback
            return [0.0] * self.config.dimension
    
    def _generate_openai_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts using OpenAI."""
        embeddings = []
        batch_size = self.config.batch_size
        
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
                            model=self.config.model_name,
                            input=batch
                        )
                        batch_embeddings = [item["embedding"] for item in response["data"]]
                        embeddings.extend(batch_embeddings)
                        break
                    except openai.error.RateLimitError:
                        if attempt < max_retries - 1:
                            logger.warning(f"Rate limit hit, retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            raise
            
            except Exception as e:
                logger.error(f"Error generating OpenAI embeddings batch: {str(e)}")
                # Add zero vectors for this batch as a fallback
                for _ in range(len(batch)):
                    embeddings.append([0.0] * self.config.dimension)
        
        return embeddings

class MockEmbeddingGenerator(EmbeddingGenerator):
    """Mock embedding generator for testing purposes."""
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate a mock embedding (random vector)."""
        # Generate a deterministic but seemingly random vector based on the text hash
        text_hash = hash(text) % 10000
        np.random.seed(text_hash)
        return np.random.rand(self.config.dimension).tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for a batch of texts."""
        return [self.generate_embedding(text) for text in texts]