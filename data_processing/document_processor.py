# door_installation_assistant/data_processing/document_processor.py
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from pathlib import Path

from unstructured.partition.pdf import partition_pdf
from unstructured.partition.html import partition_html
from unstructured.staging.base import convert_to_dict

from ..config.app_config import get_config
from .chunking_strategies import get_chunking_strategy
from .embedding_generator import EmbeddingGenerator

logger = logging.getLogger(__name__)

class DocumentProcessor(ABC):
    """Base document processor class."""
    
    def __init__(self):
        self.config = get_config().document_processing
        self.chunking_strategy = get_chunking_strategy(self.config.chunk_strategy)
        self.embedding_generator = EmbeddingGenerator()
    
    @abstractmethod
    def process_document(self, file_path: str) -> List[Dict[str, Any]]:
        """Process a document and return chunks with metadata."""
        pass
    
    def extract_metadata(self, file_path: str, content: Any) -> Dict[str, Any]:
        """Extract metadata from a document."""
        file_name = Path(file_path).name
        file_type = Path(file_path).suffix.lower()
        
        # Determine door category and type from filename or content
        door_category = self._extract_door_category(file_name, content)
        door_type = self._extract_door_type(file_name, content)
        
        return {
            "file_path": file_path,
            "file_name": file_name,
            "file_type": file_type,
            "door_category": door_category,
            "door_type": door_type,
        }
    
    def _extract_door_category(self, file_name: str, content: Any) -> str:
        """Extract door category (interior or exterior) from filename or content."""
        file_name_lower = file_name.lower()
        
        if "interior" in file_name_lower:
            return "interior"
        elif "exterior" in file_name_lower:
            return "exterior"
        
        # If not found in filename, try to find in content
        if isinstance(content, str):
            if "interior" in content.lower():
                return "interior"
            elif "exterior" in content.lower():
                return "exterior"
        
        # Default to unknown if can't determine
        return "unknown"
    
    def _extract_door_type(self, file_name: str, content: Any) -> str:
        """Extract door type from filename or content."""
        file_name_lower = file_name.lower()
        door_types = {
            "interior": ["bifold", "prehung"],
            "exterior": ["dentil shelf", "entry door", "patio door"]
        }
        
        # Check filename for door type
        for category, types in door_types.items():
            for door_type in types:
                if door_type.lower() in file_name_lower:
                    return door_type
        
        # Check content for door type if string
        if isinstance(content, str):
            content_lower = content.lower()
            for category, types in door_types.items():
                for door_type in types:
                    if door_type.lower() in content_lower:
                        return door_type
        
        # Default to unknown if can't determine
        return "unknown"

class PDFDocumentProcessor(DocumentProcessor):
    """Processor for PDF documents."""
    
    def process_document(self, file_path: str) -> List[Dict[str, Any]]:
        """Process a PDF document and return chunks with metadata."""
        logger.info(f"Processing PDF document: {file_path}")
        
        try:
            # Extract elements from PDF using Unstructured
            elements = partition_pdf(
                file_path,
                extract_images=True,
                extract_tables=True,
                infer_table_structure=True,
            )
            
            # Convert elements to dictionary for easier processing
            elements_dict = [convert_to_dict(element) for element in elements]
            
            # Extract text and combine it for metadata extraction
            combined_text = " ".join([e.get("text", "") for e in elements_dict if "text" in e])
            
            # Extract metadata
            metadata = self.extract_metadata(file_path, combined_text)
            
            # Process and categorize elements
            organized_elements = self._organize_elements(elements_dict, metadata)
            
            # Create chunks using the appropriate chunking strategy
            chunks = self.chunking_strategy.create_chunks(organized_elements)
            
            # Enrich chunks with procedural context
            enriched_chunks = self._enrich_chunks_with_context(chunks, metadata)
            
            # Generate embeddings for each chunk
            for chunk in enriched_chunks:
                chunk["embedding"] = self.embedding_generator.generate_embedding(chunk["text"])
            
            logger.info(f"Successfully processed document {file_path} into {len(enriched_chunks)} chunks")
            return enriched_chunks
            
        except Exception as e:
            logger.error(f"Error processing PDF document {file_path}: {str(e)}")
            raise
    
    def _organize_elements(self, elements: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Organize document elements into a structured format."""
        # Group elements by type and position
        paragraphs = []
        headings = []
        tables = []
        images = []
        lists = []
        
        for element in elements:
            element_type = element.get("type", "")
            element_text = element.get("text", "")
            
            # Skip empty elements
            if not element_text and "image" not in element_type.lower():
                continue
            
            # Categorize element by type
            if "title" in element_type.lower() or "heading" in element_type.lower():
                headings.append(element)
            elif "table" in element_type.lower():
                tables.append(element)
            elif "image" in element_type.lower():
                images.append(element)
            elif "list" in element_type.lower():
                lists.append(element)
            else:
                paragraphs.append(element)
        
        # Identify installation steps (usually numbered or in a specific format)
        installation_steps = self._identify_installation_steps(paragraphs, lists)
        
        # Identify components and tools sections
        components_sections = self._identify_component_sections(paragraphs, headings)
        tools_sections = self._identify_tool_sections(paragraphs, headings)
        
        # Organize into a structured document
        organized_doc = {
            "metadata": metadata,
            "headings": headings,
            "installation_steps": installation_steps,
            "components": components_sections,
            "tools": tools_sections,
            "tables": tables,
            "images": images,
            "paragraphs": paragraphs,
        }
        
        return organized_doc
    
    def _identify_installation_steps(self, paragraphs: List[Dict[str, Any]], lists: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify installation steps from paragraphs and lists."""
        installation_steps = []
        
        # Check for numbered paragraphs (Step 1, Step 2, etc.)
        for paragraph in paragraphs:
            text = paragraph.get("text", "")
            if text.strip().lower().startswith("step "):
                installation_steps.append({
                    "type": "installation_step",
                    "text": text,
                    "original_element": paragraph
                })
        
        # Check list items as they often contain installation steps
        for list_item in lists:
            text = list_item.get("text", "")
            # For list items, we assume they might be installation steps if they contain action verbs
            action_verbs = ["install", "place", "position", "secure", "attach", "connect", "align", "adjust"]
            if any(verb in text.lower() for verb in action_verbs):
                installation_steps.append({
                    "type": "installation_step",
                    "text": text,
                    "original_element": list_item
                })
        
        # Sort steps based on their position in the document
        installation_steps.sort(key=lambda x: x["original_element"].get("metadata", {}).get("page_number", 0))
        
        return installation_steps
    
    def _identify_component_sections(self, paragraphs: List[Dict[str, Any]], headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify sections related to door components."""
        component_sections = []
        
        # Check headings for component-related titles
        component_keywords = ["component", "part", "hardware", "material", "item"]
        for heading in headings:
            text = heading.get("text", "").lower()
            if any(keyword in text for keyword in component_keywords):
                # Find paragraphs that might be under this heading
                heading_page = heading.get("metadata", {}).get("page_number", 0)
                related_paragraphs = [p for p in paragraphs if p.get("metadata", {}).get("page_number", 0) == heading_page]
                
                component_sections.append({
                    "type": "component_section",
                    "heading": heading.get("text", ""),
                    "paragraphs": related_paragraphs,
                    "page_number": heading_page
                })
        
        return component_sections
    
    def _identify_tool_sections(self, paragraphs: List[Dict[str, Any]], headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify sections related to tools required for installation."""
        tool_sections = []
        
        # Check headings for tool-related titles
        tool_keywords = ["tool", "equipment", "required", "need"]
        for heading in headings:
            text = heading.get("text", "").lower()
            if any(keyword in text for keyword in tool_keywords):
                # Find paragraphs that might be under this heading
                heading_page = heading.get("metadata", {}).get("page_number", 0)
                related_paragraphs = [p for p in paragraphs if p.get("metadata", {}).get("page_number", 0) == heading_page]
                
                tool_sections.append({
                    "type": "tool_section",
                    "heading": heading.get("text", ""),
                    "paragraphs": related_paragraphs,
                    "page_number": heading_page
                })
        
        return tool_sections
    
    def _enrich_chunks_with_context(self, chunks: List[Dict[str, Any]], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enrich chunks with procedural context and metadata."""
        enriched_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Add document metadata to chunk
            enriched_chunk = {
                **chunk,
                "metadata": {
                    **metadata,
                    "chunk_id": i,
                    "total_chunks": len(chunks)
                }
            }
            
            # Identify if the chunk contains installation steps
            if "installation_step" in chunk.get("type", "").lower() or "step " in chunk.get("text", "").lower():
                enriched_chunk["metadata"]["content_type"] = "installation_step"
                
                # Try to extract step number
                text = chunk.get("text", "")
                step_number = None
                if text.startswith("Step "):
                    try:
                        step_number = int(text.split("Step")[1].split(".")[0].strip())
                    except (ValueError, IndexError):
                        pass
                
                if step_number:
                    enriched_chunk["metadata"]["step_number"] = step_number
            
            # Identify tool and component chunks
            if "tool" in chunk.get("type", "").lower():
                enriched_chunk["metadata"]["content_type"] = "tools"
            elif "component" in chunk.get("type", "").lower():
                enriched_chunk["metadata"]["content_type"] = "components"
            
            enriched_chunks.append(enriched_chunk)
        
        return enriched_chunks

# Factory function to get the appropriate document processor
def get_document_processor(file_type: str) -> DocumentProcessor:
    """Get the appropriate document processor for the given file type."""
    if file_type.lower() == ".pdf":
        return PDFDocumentProcessor()
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

# Main processing function for documents
def process_document(file_path: str) -> List[Dict[str, Any]]:
    """Process a document and return chunks with metadata."""
    file_type = Path(file_path).suffix.lower()
    processor = get_document_processor(file_type)
    return processor.process_document(file_path)