# door_installation_assistant/agent_system/agents/base_agent.py
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union
import uuid

from ...config.app_config import get_config
from ...llm_integration.llm_manager import LLMManager
from ...retrieval.retrieval_pipeline import RetrievalPipeline

logger = logging.getLogger(__name__)

class Agent(ABC):
    """Base class for all agents."""
    
    def __init__(self, **kwargs):
        self.config = get_config().agent
        self.agent_id = str(uuid.uuid4())
        self.llm_manager = LLMManager()
        self.retrieval_pipeline = kwargs.get("retrieval_pipeline")
        if not self.retrieval_pipeline:
            self.retrieval_pipeline = RetrievalPipeline()
        
        # Initialize conversation memory
        self.memory = []
    
    @property
    def agent_type(self) -> str:
        """Get the agent type."""
        return "base"
    
    @property
    def description(self) -> str:
        """Get the agent description."""
        return "Base agent"
    
    @abstractmethod
    def process(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Process a query.
        
        Args:
            query: User query.
            **kwargs: Additional arguments specific to the agent.
            
        Returns:
            Dictionary with the processing results.
        """
        pass
    
    def _add_to_memory(self, role: str, content: str):
        """
        Add a message to the conversation memory.
        
        Args:
            role: Message role (system, user, assistant).
            content: Message content.
        """
        self.memory.append({
            "role": role,
            "content": content
        })
    
    def _get_memory(self) -> List[Dict[str, str]]:
        """
        Get the conversation memory.
        
        Returns:
            List of messages in the conversation memory.
        """
        return self.memory
    
    def _clear_memory(self):
        """Clear the conversation memory."""
        self.memory = []
    
    def _retrieve_documents(
        self,
        query: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: User query.
            filter_dict: Filter criteria for retrieval.
            top_k: Number of documents to retrieve.
            
        Returns:
            List of retrieved documents.
        """
        try:
            documents = self.retrieval_pipeline.retrieve(
                query=query,
                filter_dict=filter_dict,
                top_k=top_k
            )
            
            return documents
        
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []
    
    def _format_documents_as_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents as context for the LLM.
        
        Args:
            documents: List of retrieved documents.
            
        Returns:
            Formatted context string.
        """
        if not documents:
            return "No relevant documents found."
        
        context = ""
        
        for i, doc in enumerate(documents):
            doc_text = doc.get("text", "")
            doc_metadata = doc.get("metadata", {})
            
            # Extract metadata fields
            door_category = doc_metadata.get("door_category", "unknown")
            door_type = doc_metadata.get("door_type", "unknown")
            content_type = doc_metadata.get("content_type", "general")
            
            # Format document with metadata
            context += f"Document {i+1} [{door_category} {door_type}, {content_type}]:\n{doc_text}\n\n"
        
        return context
    
    def _generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of message dictionaries with role and content.
            temperature: Temperature for generation.
            
        Returns:
            Generated response text.
        """
        try:
            response = self.llm_manager.generate_response(
                messages=messages,
                temperature=temperature
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I'm sorry, I encountered an error while generating a response. Please try again."