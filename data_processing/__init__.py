# door_installation_assistant/data_processing/__init__.py
"""
Data processing package for Door Installation Assistant.

This package provides document processing, chunking, and embedding generation
capabilities for the Door Installation Assistant.
"""

from .document_processor import process_document, DocumentProcessor, PDFDocumentProcessor
from .chunking_strategies import (
    ChunkingStrategy, 
    HierarchicalChunkingStrategy, 
    SemanticChunkingStrategy,
    FixedSizeChunkingStrategy,
    get_chunking_strategy
)
from .embedding_generator import EmbeddingGenerator, MockEmbeddingGenerator

def get_document_processor(file_type: str):
    """
    Factory function to get a document processor instance.
    
    Args:
        file_type: File type (extension) to process.
        
    Returns:
        DocumentProcessor instance.
    """
    from .document_processor import get_document_processor as get_processor
    return get_processor(file_type)

__all__ = [
    'process_document',
    'DocumentProcessor',
    'PDFDocumentProcessor',
    'ChunkingStrategy',
    'HierarchicalChunkingStrategy',
    'SemanticChunkingStrategy',
    'FixedSizeChunkingStrategy',
    'get_chunking_strategy',
    'EmbeddingGenerator',
    'MockEmbeddingGenerator',
    'get_document_processor',
]