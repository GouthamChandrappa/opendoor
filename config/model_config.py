# door_installation_assistant/config/model_config.py
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseSettings, Field, validator
import os

class OpenAIConfig(BaseSettings):
    """OpenAI model configuration."""
    
    api_key: Optional[str] = Field(None, description="OpenAI API key")
    organization_id: Optional[str] = Field(None, description="OpenAI organization ID")
    
    # LLM models
    chat_model: str = Field("gpt-4o", description="OpenAI chat model")
    chat_fallback_model: str = Field("gpt-3.5-turbo", description="Fallback chat model")
    
    # Embedding models
    embedding_model: str = Field(
        "text-embedding-3-large", 
        description="OpenAI embedding model"
    )
    embedding_fallback_model: str = Field(
        "text-embedding-3-small", 
        description="Fallback embedding model"
    )
    
    # Generation parameters
    temperature: float = Field(0.2, description="Temperature for generation")
    max_tokens: int = Field(1000, description="Maximum tokens for generation")
    top_p: float = Field(0.95, description="Top-p for generation")
    frequency_penalty: float = Field(0.0, description="Frequency penalty")
    presence_penalty: float = Field(0.0, description="Presence penalty")
    
    # Rate limiting
    requests_per_minute: int = Field(60, description="API requests per minute")
    tokens_per_minute: int = Field(90000, description="API tokens per minute")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    retry_delay: float = Field(1.0, description="Initial retry delay in seconds")
    
    class Config:
        env_prefix = "OPENAI_"
        env_file = ".env"
    
    @validator("api_key", pre=True, always=True)
    def validate_api_key(cls, v):
        """Validate API key."""
        if v is None:
            v = os.environ.get("OPENAI_API_KEY")
        if v is None:
            raise ValueError("OpenAI API key is required")
        return v

class AnthropicConfig(BaseSettings):
    """Anthropic model configuration."""
    
    api_key: Optional[str] = Field(None, description="Anthropic API key")
    
    # LLM models
    chat_model: str = Field("claude-3-opus-20240229", description="Anthropic chat model")
    chat_fallback_model: str = Field(
        "claude-3-sonnet-20240229", 
        description="Fallback chat model"
    )
    
    # Generation parameters
    temperature: float = Field(0.2, description="Temperature for generation")
    max_tokens: int = Field(1000, description="Maximum tokens for generation")
    top_p: float = Field(0.95, description="Top-p for generation")
    
    # Rate limiting
    requests_per_minute: int = Field(50, description="API requests per minute")
    tokens_per_minute: int = Field(80000, description="API tokens per minute")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    retry_delay: float = Field(1.0, description="Initial retry delay in seconds")
    
    class Config:
        env_prefix = "ANTHROPIC_"
        env_file = ".env"
    
    @validator("api_key", pre=True, always=True)
    def validate_api_key(cls, v):
        """Validate API key."""
        if v is None:
            v = os.environ.get("ANTHROPIC_API_KEY")
        return v

class CohereConfig(BaseSettings):
    """Cohere model configuration."""
    
    api_key: Optional[str] = Field(None, description="Cohere API key")
    
    # Models
    rerank_model: str = Field("rerank-english-v3.0", description="Reranking model")
    embedding_model: str = Field("embed-english-v3.0", description="Embedding model")
    
    # Rate limiting
    requests_per_minute: int = Field(100, description="API requests per minute")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    retry_delay: float = Field(1.0, description="Initial retry delay in seconds")
    
    class Config:
        env_prefix = "COHERE_"
        env_file = ".env"
    
    @validator("api_key", pre=True, always=True)
    def validate_api_key(cls, v):
        """Validate API key."""
        if v is None:
            v = os.environ.get("COHERE_API_KEY")
        return v

class ModelConfig(BaseSettings):
    """Model configuration settings."""
    
    # Primary LLM provider
    primary_llm_provider: str = Field(
        "openai", 
        description="Primary LLM provider (openai, anthropic)"
    )
    
    # Primary embedding provider
    primary_embedding_provider: str = Field(
        "openai", 
        description="Primary embedding provider (openai, cohere)"
    )
    
    # Primary reranking provider
    primary_reranking_provider: str = Field(
        "cohere", 
        description="Primary reranking provider (cohere)"
    )
    
    # Provider configurations
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    anthropic: AnthropicConfig = Field(default_factory=AnthropicConfig)
    cohere: CohereConfig = Field(default_factory=CohereConfig)
    
    # Door type identification models
    door_identification_model: str = Field(
        "openai/gpt-4o", 
        description="Model for door type identification"
    )
    
    # Installation procedure models
    installation_procedure_model: str = Field(
        "openai/gpt-4o", 
        description="Model for installation procedures"
    )
    
    # Troubleshooting models
    troubleshooting_model: str = Field(
        "openai/gpt-4o", 
        description="Model for troubleshooting"
    )
    
    # Response evaluation models
    evaluation_model: str = Field(
        "openai/gpt-4o", 
        description="Model for response evaluation"
    )
    
    # Model context windows (in tokens)
    context_windows: Dict[str, int] = Field(
        default_factory=lambda: {
            "openai/gpt-4o": 32000,
            "openai/gpt-3.5-turbo": 16000,
            "anthropic/claude-3-opus-20240229": 32000,
            "anthropic/claude-3-sonnet-20240229": 28000,
        },
        description="Context window sizes for models"
    )
    
    # Embedding dimensions
    embedding_dimensions: Dict[str, int] = Field(
        default_factory=lambda: {
            "openai/text-embedding-3-large": 3072,
            "openai/text-embedding-3-small": 1536,
            "cohere/embed-english-v3.0": 1024,
        },
        description="Embedding dimensions for models"
    )
    
    # Prompt templates file path
    prompt_templates_file: str = Field(
        "config/prompt_templates.yaml",
        description="Path to prompt templates file"
    )
    
    class Config:
        env_prefix = "MODEL_"
        env_file = ".env"
    
    def get_llm_provider_config(self, provider: Optional[str] = None) -> Union[OpenAIConfig, AnthropicConfig]:
        """
        Get the configuration for a specific LLM provider.
        
        Args:
            provider: Provider name. If None, the primary provider is used.
            
        Returns:
            Provider configuration.
        """
        provider = provider or self.primary_llm_provider
        
        if provider == "openai":
            return self.openai
        elif provider == "anthropic":
            return self.anthropic
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    def get_embedding_provider_config(self, provider: Optional[str] = None) -> Union[OpenAIConfig, CohereConfig]:
        """
        Get the configuration for a specific embedding provider.
        
        Args:
            provider: Provider name. If None, the primary provider is used.
            
        Returns:
            Provider configuration.
        """
        provider = provider or self.primary_embedding_provider
        
        if provider == "openai":
            return self.openai
        elif provider == "cohere":
            return self.cohere
        else:
            raise ValueError(f"Unknown embedding provider: {provider}")
    
    def get_reranking_provider_config(self, provider: Optional[str] = None) -> CohereConfig:
        """
        Get the configuration for a specific reranking provider.
        
        Args:
            provider: Provider name. If None, the primary provider is used.
            
        Returns:
            Provider configuration.
        """
        provider = provider or self.primary_reranking_provider
        
        if provider == "cohere":
            return self.cohere
        else:
            raise ValueError(f"Unknown reranking provider: {provider}")
    
    def get_embedding_dimension(self, model: Optional[str] = None) -> int:
        """
        Get the embedding dimension for a specific model.
        
        Args:
            model: Model name. If None, the primary model is used.
            
        Returns:
            Embedding dimension.
        """
        if model is None:
            provider = self.primary_embedding_provider
            if provider == "openai":
                model = f"{provider}/{self.openai.embedding_model}"
            elif provider == "cohere":
                model = f"{provider}/{self.cohere.embedding_model}"
        
        # If model doesn't have provider prefix, add the primary provider
        if "/" not in model:
            model = f"{self.primary_embedding_provider}/{model}"
        
        if model in self.embedding_dimensions:
            return self.embedding_dimensions[model]
        else:
            # Return a default dimension
            return 1536
    
    def get_context_window(self, model: Optional[str] = None) -> int:
        """
        Get the context window size for a specific model.
        
        Args:
            model: Model name. If None, the primary model is used.
            
        Returns:
            Context window size in tokens.
        """
        if model is None:
            provider = self.primary_llm_provider
            if provider == "openai":
                model = f"{provider}/{self.openai.chat_model}"
            elif provider == "anthropic":
                model = f"{provider}/{self.anthropic.chat_model}"
        
        # If model doesn't have provider prefix, add the primary provider
        if "/" not in model:
            model = f"{self.primary_llm_provider}/{model}"
        
        if model in self.context_windows:
            return self.context_windows[model]
        else:
            # Return a conservative default
            return 16000

def get_model_config() -> ModelConfig:
    """Get the model configuration."""
    return ModelConfig()