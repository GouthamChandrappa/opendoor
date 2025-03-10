"""
Document processing module for door installation assistant.
Handles PDF extraction, chunking, and embedding generation.
"""

from data_processing.document_processor import (
    DocumentProcessor,
    PDFDocumentProcessor,
    process_document,
    process_documents_batch,
    get_document_processor
)

from data_processing.chunking_strategies import (
    ChunkingStrategy,
    HierarchicalChunkingStrategy,
    SemanticChunkingStrategy,
    FixedSizeChunkingStrategy,
    get_chunking_strategy
)

from data_processing.embedding_generator import (
    EmbeddingGenerator,
    MockEmbeddingGenerator
)

__all__ = [
    'process_document',
    'process_documents_batch',
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