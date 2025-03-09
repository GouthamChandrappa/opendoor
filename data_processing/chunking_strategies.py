# door_installation_assistant/data_processing/chunking_strategies.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
import nltk
from nltk.tokenize import sent_tokenize
import re

from ..config.app_config import get_config

# Ensure NLTK data is downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

logger = logging.getLogger(__name__)

class ChunkingStrategy(ABC):
    """Base class for document chunking strategies."""
    
    def __init__(self):
        self.config = get_config().document_processing
    
    @abstractmethod
    def create_chunks(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks from a document."""
        pass

class HierarchicalChunkingStrategy(ChunkingStrategy):
    """Hierarchical chunking strategy that preserves document structure."""
    
    def create_chunks(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create hierarchical chunks from a document."""
        chunks = []
        
        # Process installation steps as individual chunks or small related groups
        chunks.extend(self._chunk_installation_steps(document.get("installation_steps", [])))
        
        # Process components and tools sections
        chunks.extend(self._chunk_by_section(document.get("components", []), "component"))
        chunks.extend(self._chunk_by_section(document.get("tools", []), "tool"))
        
        # Process regular paragraphs that weren't included in specialized sections
        chunks.extend(self._chunk_paragraphs(document.get("paragraphs", [])))
        
        # Process tables (each table as a separate chunk)
        for table in document.get("tables", []):
            chunks.append({
                "type": "table",
                "text": table.get("text", ""),
                "metadata": {
                    "page_number": table.get("metadata", {}).get("page_number", 0),
                    "content_type": "table"
                }
            })
        
        # Add document metadata to all chunks
        for chunk in chunks:
            if "metadata" not in chunk:
                chunk["metadata"] = {}
            chunk["metadata"].update(document.get("metadata", {}))
        
        return chunks
    
    def _chunk_installation_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create chunks from installation steps, preserving step integrity."""
        chunks = []
        current_chunk_text = []
        current_chunk_size = 0
        current_step_number = None
        
        for step in steps:
            step_text = step.get("text", "")
            
            # Try to extract step number
            match = re.search(r"step\s+(\d+)", step_text.lower())
            if match:
                step_number = int(match.group(1))
                
                # If we're on a new step and have content, create a chunk
                if current_step_number is not None and current_step_number != step_number and current_chunk_text:
                    chunks.append({
                        "type": "installation_step",
                        "text": "\n".join(current_chunk_text),
                        "metadata": {
                            "step_number": current_step_number,
                            "content_type": "installation_step"
                        }
                    })
                    current_chunk_text = []
                    current_chunk_size = 0
                
                current_step_number = step_number
            
            # If adding this step would exceed the target chunk size and we already have content,
            # create a chunk and start a new one
            step_size = len(step_text)
            if current_chunk_size + step_size > self.config.chunk_size and current_chunk_text:
                chunks.append({
                    "type": "installation_step",
                    "text": "\n".join(current_chunk_text),
                    "metadata": {
                        "step_number": current_step_number,
                        "content_type": "installation_step"
                    }
                })
                current_chunk_text = []
                current_chunk_size = 0
            
            current_chunk_text.append(step_text)
            current_chunk_size += step_size
        
        # Add the last chunk if there's any content left
        if current_chunk_text:
            chunks.append({
                "type": "installation_step",
                "text": "\n".join(current_chunk_text),
                "metadata": {
                    "step_number": current_step_number,
                    "content_type": "installation_step"
                }
            })
        
        return chunks
    
    def _chunk_by_section(self, sections: List[Dict[str, Any]], section_type: str) -> List[Dict[str, Any]]:
        """Create chunks from document sections."""
        chunks = []
        
        for section in sections:
            heading = section.get("heading", "")
            paragraphs = section.get("paragraphs", [])
            
            # Combine paragraphs into a single text
            section_text = heading + "\n\n" + "\n".join([p.get("text", "") for p in paragraphs])
            
            # If section is small enough, keep it as one chunk
            if len(section_text) <= self.config.chunk_size:
                chunks.append({
                    "type": f"{section_type}_section",
                    "text": section_text,
                    "metadata": {
                        "page_number": section.get("page_number", 0),
                        "content_type": section_type,
                        "heading": heading
                    }
                })
            else:
                # Split large sections into smaller chunks
                sentences = sent_tokenize(section_text)
                current_chunk = []
                current_size = 0
                
                for sentence in sentences:
                    sentence_size = len(sentence)
                    
                    if current_size + sentence_size > self.config.chunk_size and current_chunk:
                        chunks.append({
                            "type": f"{section_type}_section",
                            "text": " ".join(current_chunk),
                            "metadata": {
                                "page_number": section.get("page_number", 0),
                                "content_type": section_type,
                                "heading": heading
                            }
                        })
                        current_chunk = []
                        current_size = 0
                    
                    current_chunk.append(sentence)
                    current_size += sentence_size
                
                # Add the last chunk if there's any content left
                if current_chunk:
                    chunks.append({
                        "type": f"{section_type}_section",
                        "text": " ".join(current_chunk),
                        "metadata": {
                            "page_number": section.get("page_number", 0),
                            "content_type": section_type,
                            "heading": heading
                        }
                    })
        
        return chunks
    
    def _chunk_paragraphs(self, paragraphs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create chunks from regular paragraphs."""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            # Skip paragraphs that might have been included in other chunks
            if paragraph.get("processed", False):
                continue
            
            paragraph_text = paragraph.get("text", "")
            paragraph_size = len(paragraph_text)
            
            # If adding this paragraph would exceed the chunk size and we already have content,
            # create a chunk and start a new one
            if current_size + paragraph_size > self.config.chunk_size and current_chunk:
                chunks.append({
                    "type": "paragraph",
                    "text": "\n\n".join(current_chunk),
                    "metadata": {
                        "content_type": "general_info"
                    }
                })
                current_chunk = []
                current_size = 0
            
            current_chunk.append(paragraph_text)
            current_size += paragraph_size
            paragraph["processed"] = True
        
        # Add the last chunk if there's any content left
        if current_chunk:
            chunks.append({
                "type": "paragraph",
                "text": "\n\n".join(current_chunk),
                "metadata": {
                    "content_type": "general_info"
                }
            })
        
        return chunks

class SemanticChunkingStrategy(ChunkingStrategy):
    """Semantic chunking strategy that groups content by meaning."""
    
    def create_chunks(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create semantically coherent chunks from a document."""
        # Extract all text elements
        text_elements = []
        
        # Extract headings and their associated content
        for heading in document.get("headings", []):
            heading_text = heading.get("text", "")
            heading_page = heading.get("metadata", {}).get("page_number", 0)
            
            # Find all paragraphs on the same page that might be under this heading
            associated_paragraphs = [
                p.get("text", "") for p in document.get("paragraphs", [])
                if p.get("metadata", {}).get("page_number", 0) == heading_page
            ]
            
            # Create a semantic unit from the heading and its paragraphs
            if associated_paragraphs:
                text_elements.append({
                    "text": heading_text + "\n\n" + "\n".join(associated_paragraphs),
                    "metadata": {
                        "page_number": heading_page,
                        "heading": heading_text
                    }
                })
        
        # Extract installation steps as semantic units
        for step in document.get("installation_steps", []):
            text_elements.append({
                "text": step.get("text", ""),
                "metadata": {
                    "content_type": "installation_step",
                    "page_number": step.get("original_element", {}).get("metadata", {}).get("page_number", 0)
                }
            })
        
        # Group elements by semantic similarity and create chunks
        chunks = self._group_elements_semantically(text_elements)
        
        # Add document metadata to all chunks
        for chunk in chunks:
            if "metadata" not in chunk:
                chunk["metadata"] = {}
            chunk["metadata"].update(document.get("metadata", {}))
        
        return chunks
    
    def _group_elements_semantically(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group elements by semantic similarity."""
        # Sort elements by page number to maintain document order
        sorted_elements = sorted(elements, key=lambda x: x.get("metadata", {}).get("page_number", 0))
        
        chunks = []
        current_chunk = []
        current_chunk_text = ""
        current_topic = None
        
        for element in sorted_elements:
            element_text = element.get("text", "")
            element_metadata = element.get("metadata", {})
            
            # Determine the topic of this element
            topic = self._determine_topic(element_text)
            
            # If this is a new topic and we have content, create a chunk
            if current_topic is not None and topic != current_topic and current_chunk:
                chunks.append({
                    "type": "semantic_section",
                    "text": current_chunk_text,
                    "metadata": {
                        "content_type": current_topic
                    }
                })
                current_chunk = []
                current_chunk_text = ""
            
            # If adding this element would exceed the chunk size and we already have content,
            # create a chunk and start a new one
            if len(current_chunk_text) + len(element_text) > self.config.chunk_size and current_chunk:
                chunks.append({
                    "type": "semantic_section",
                    "text": current_chunk_text,
                    "metadata": {
                        "content_type": current_topic
                    }
                })
                current_chunk = []
                current_chunk_text = ""
            
            current_chunk.append(element)
            current_chunk_text += (element_text + "\n\n")
            current_topic = topic
        
        # Add the last chunk if there's any content left
        if current_chunk:
            chunks.append({
                "type": "semantic_section",
                "text": current_chunk_text.strip(),
                "metadata": {
                    "content_type": current_topic
                }
            })
        
        return chunks
    
    def _determine_topic(self, text: str) -> str:
        """Determine the topic of a text element."""
        text_lower = text.lower()
        
        # Check for installation steps
        if re.search(r"step\s+\d+", text_lower) or "install" in text_lower:
            return "installation_step"
        
        # Check for tool information
        if "tool" in text_lower or "equipment" in text_lower:
            return "tool"
        
        # Check for component information
        if "component" in text_lower or "part" in text_lower or "hardware" in text_lower:
            return "component"
        
        # Check for door type information
        if "door type" in text_lower or "door model" in text_lower:
            return "door_type"
        
        # Check for safety information
        if "safety" in text_lower or "warning" in text_lower or "caution" in text_lower:
            return "safety"
        
        # Default to general information
        return "general_info"

class FixedSizeChunkingStrategy(ChunkingStrategy):
    """Fixed-size chunking strategy that creates chunks of a specified size."""
    
    def create_chunks(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create fixed-size chunks from a document."""
        # Extract all text from the document
        all_text = ""
        
        # Add headings
        for heading in document.get("headings", []):
            all_text += heading.get("text", "") + "\n\n"
        
        # Add paragraphs
        for paragraph in document.get("paragraphs", []):
            all_text += paragraph.get("text", "") + "\n\n"
        
        # Add installation steps
        for step in document.get("installation_steps", []):
            all_text += step.get("text", "") + "\n\n"
        
        # Create fixed-size chunks
        chunks = []
        sentences = sent_tokenize(all_text)
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.config.chunk_size and current_chunk:
                chunks.append({
                    "type": "fixed_chunk",
                    "text": " ".join(current_chunk),
                    "metadata": {
                        "content_type": "general_info"
                    }
                })
                current_chunk = []
                current_size = 0
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add the last chunk if there's any content left
        if current_chunk:
            chunks.append({
                "type": "fixed_chunk",
                "text": " ".join(current_chunk),
                "metadata": {
                    "content_type": "general_info"
                }
            })
        
        # Add document metadata to all chunks
        for chunk in chunks:
            if "metadata" not in chunk:
                chunk["metadata"] = {}
            chunk["metadata"].update(document.get("metadata", {}))
        
        return chunks

# Factory function to get the appropriate chunking strategy
def get_chunking_strategy(strategy_name: str) -> ChunkingStrategy:
    """Get the appropriate chunking strategy based on the strategy name."""
    strategies = {
        "hierarchical": HierarchicalChunkingStrategy,
        "semantic": SemanticChunkingStrategy,
        "fixed": FixedSizeChunkingStrategy,
    }
    
    if strategy_name not in strategies:
        logger.warning(f"Unknown chunking strategy: {strategy_name}. Using hierarchical strategy.")
        return HierarchicalChunkingStrategy()
    
    return strategies[strategy_name]()