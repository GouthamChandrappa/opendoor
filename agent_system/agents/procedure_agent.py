# door_installation_assistant/agent_system/agents/procedure_agent.py
import logging
from typing import Dict, Any, List, Optional, Tuple

from .base_agent import Agent
from ...llm_integration.prompt_templates import PromptBuilder

logger = logging.getLogger(__name__)

class ProcedureAgent(Agent):
    """Agent for providing door installation procedures."""
    
    @property
    def agent_type(self) -> str:
        return "procedure"
    
    @property
    def description(self) -> str:
        return "Provides step-by-step door installation procedures"
    
    def process(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Process a query to provide installation procedures.
        
        Args:
            query: User query.
            **kwargs: Additional arguments including door type and category.
            
        Returns:
            Dictionary with the procedure and relevant information.
        """
        try:
            # Extract door information from kwargs
            door_category = kwargs.get("door_category", "unknown")
            door_type = kwargs.get("door_type", "unknown")
            
            # Create filter for document retrieval
            filter_dict = {}
            if door_category != "unknown":
                filter_dict["door_category"] = door_category
            if door_type != "unknown":
                filter_dict["door_type"] = door_type
            
            # Add content type filter to prioritize installation steps
            filter_dict["content_type"] = "installation_step"
            
            # Retrieve relevant documents
            documents = self._retrieve_documents(
                query=query,
                filter_dict=filter_dict,
                top_k=7  # Get more documents for installation procedures
            )
            
            # If no installation steps found, try without content type filter
            if not documents:
                if "content_type" in filter_dict:
                    del filter_dict["content_type"]
                
                documents = self._retrieve_documents(
                    query=query,
                    filter_dict=filter_dict,
                    top_k=7
                )
            
            # Format documents as context
            context = self._format_documents_as_context(documents)
            
            # Build prompt for installation procedure
            messages = PromptBuilder.build_installation_prompt(
                query=query,
                context=context,
                door_type=door_type,
                door_category=door_category
            )
            
            # Generate response
            response = self._generate_response(messages, temperature=0.3)
            
            # Extract step information if possible
            step_info = self._extract_step_info(documents)
            
            # Return the procedure information
            return {
                "procedure": response,
                "door_category": door_category,
                "door_type": door_type,
                "step_info": step_info,
                "document_count": len(documents)
            }
        
        except Exception as e:
            logger.error(f"Error providing installation procedure: {str(e)}")
            return {
                "procedure": "I'm sorry, I encountered an error while generating the installation procedure. Please try again with a more specific question.",
                "door_category": kwargs.get("door_category", "unknown"),
                "door_type": kwargs.get("door_type", "unknown"),
                "error": str(e)
            }
    
    def _extract_step_info(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract step information from retrieved documents.
        
        Args:
            documents: List of retrieved documents.
            
        Returns:
            Dictionary with step information.
        """
        step_info = {
            "total_steps": 0,
            "current_step": None,
            "has_sequential_steps": False
        }
        
        step_numbers = []
        
        for doc in documents:
            metadata = doc.get("metadata", {})
            
            # Check if document contains step information
            if "step_number" in metadata:
                step_number = metadata["step_number"]
                step_numbers.append(step_number)
        
        if step_numbers:
            step_numbers.sort()
            step_info["total_steps"] = max(step_numbers)
            
            # Check if we have sequential steps
            if len(step_numbers) > 1:
                # Check if steps are sequential (allowing for some gaps)
                sequential_count = 0
                for i in range(len(step_numbers) - 1):
                    if step_numbers[i + 1] - step_numbers[i] <= 2:  # Allow gap of at most 1 step
                        sequential_count += 1
                
                step_info["has_sequential_steps"] = sequential_count >= len(step_numbers) // 2
        
        return step_info
    
    def get_specific_step(self, step_number: int, door_category: str, door_type: str) -> Dict[str, Any]:
        """
        Get a specific installation step.
        
        Args:
            step_number: Step number to retrieve.
            door_category: Door category.
            door_type: Door type.
            
        Returns:
            Dictionary with the step information.
        """
        try:
            # Create filter for document retrieval
            filter_dict = {
                "content_type": "installation_step",
                "step_number": step_number
            }
            
            if door_category != "unknown":
                filter_dict["door_category"] = door_category
            if door_type != "unknown":
                filter_dict["door_type"] = door_type
            
            # Retrieve relevant documents
            documents = self._retrieve_documents(
                query=f"Step {step_number} for {door_type} {door_category} door installation",
                filter_dict=filter_dict,
                top_k=3
            )
            
            if not documents:
                return {
                    "found": False,
                    "step_number": step_number,
                    "step_content": f"I couldn't find specific information for Step {step_number} of the {door_type} door installation."
                }
            
            # Format documents as context
            context = self._format_documents_as_context(documents)
            
            # Build prompt for specific step
            messages = PromptBuilder.build_installation_prompt(
                query=f"Explain in detail Step {step_number} for installing a {door_type} door.",
                context=context,
                door_type=door_type,
                door_category=door_category
            )
            
            # Generate response
            response = self._generate_response(messages, temperature=0.2)
            
            return {
                "found": True,
                "step_number": step_number,
                "step_content": response,
                "document_count": len(documents)
            }
        
        except Exception as e:
            logger.error(f"Error retrieving specific step: {str(e)}")
            return {
                "found": False,
                "step_number": step_number,
                "step_content": f"I encountered an error while retrieving Step {step_number}.",
                "error": str(e)
            }