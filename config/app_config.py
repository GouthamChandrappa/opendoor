# door_installation_assistant/config/app_config.py
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseSettings, Field

class VectorStoreConfig(BaseSettings):
    provider: str = Field("qdrant", description="Vector store provider (qdrant, pinecone, weaviate)")
    host: str = Field("localhost", description="Vector store host")
    port: int = Field(6333, description="Vector store port")
    collection_name: str = Field("door_installations", description="Collection name in vector store")
    dimension: int = Field(1536, description="Embedding dimension")
    url: Optional[str] = Field(None, description="URL for cloud-hosted vector stores")
    api_key: Optional[str] = Field(None, description="API key for vector store")
    
    class Config:
        env_prefix = "VECTOR_STORE_"
        env_file = ".env"

class DocumentProcessingConfig(BaseSettings):
    chunk_strategy: str = Field("hierarchical", description="Chunking strategy (hierarchical, semantic, fixed)")
    chunk_size: int = Field(1000, description="Target chunk size for text")
    chunk_overlap: int = Field(200, description="Chunk overlap size")
    max_chunks_per_doc: int = Field(100, description="Maximum chunks per document")
    include_metadata: bool = Field(True, description="Whether to include metadata in chunks")
    
    class Config:
        env_prefix = "DOC_PROC_"
        env_file = ".env"

class LLMConfig(BaseSettings):
    provider: str = Field("openai", description="LLM provider (openai, anthropic, etc)")
    model_name: str = Field("gpt-4o", description="LLM model name")
    temperature: float = Field(0.2, description="Temperature for LLM generation")
    max_tokens: int = Field(1000, description="Maximum tokens for LLM response")
    api_key: Optional[str] = Field(None, description="API key for LLM provider")
    
    class Config:
        env_prefix = "LLM_"
        env_file = ".env"

class EmbeddingConfig(BaseSettings):
    provider: str = Field("openai", description="Embedding provider")
    model_name: str = Field("text-embedding-3-large", description="Embedding model name")
    batch_size: int = Field(100, description="Batch size for embedding generation")
    api_key: Optional[str] = Field(None, description="API key for embedding provider")
    
    class Config:
        env_prefix = "EMBEDDING_"
        env_file = ".env"

class RetrievalConfig(BaseSettings):
    retrieval_type: str = Field("hybrid", description="Retrieval type (hybrid, vector, keyword)")
    top_k: int = Field(10, description="Number of documents to retrieve")
    use_reranking: bool = Field(True, description="Whether to use reranking")
    reranker_model: str = Field("cohere", description="Reranker model to use")
    reranker_top_k: int = Field(5, description="Number of documents after reranking")
    
    class Config:
        env_prefix = "RETRIEVAL_"
        env_file = ".env"

class AgentConfig(BaseSettings):
    framework: str = Field("crewai", description="Agent framework (crewai, langchain)")
    max_iterations: int = Field(10, description="Maximum iterations for agent")
    agent_types: List[str] = Field(
        ["door_identifier", "procedure", "tool", "troubleshooting", "safety"],
        description="Agent types to create"
    )
    
    class Config:
        env_prefix = "AGENT_"
        env_file = ".env"

class AppConfig(BaseSettings):
    app_name: str = Field("Door Installation Assistant", description="Application name")
    debug: bool = Field(False, description="Debug mode")
    log_level: str = Field("INFO", description="Logging level")
    data_dir: str = Field("./data", description="Data directory")
    cache_dir: str = Field("./cache", description="Cache directory")
    api_host: str = Field("0.0.0.0", description="API host")
    api_port: int = Field(8000, description="API port")
    
    # Sub-configurations
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    document_processing: DocumentProcessingConfig = Field(default_factory=DocumentProcessingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    
    class Config:
        env_prefix = "APP_"
        env_file = ".env"

# Create a singleton config instance
config = AppConfig()

def get_config() -> AppConfig:
    """Get the application configuration."""
    return config