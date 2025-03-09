# door_installation_assistant/agent_system/agents/tool_agent.py
import logging
from typing import Dict, Any, List, Optional, Tuple

from .base_agent import Agent
from ...llm_integration.prompt_templates import PromptBuilder
from ...llm_integration.response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)

class ToolAgent(Agent):
    """Agent for providing tool and component recommendations."""
    
    @property
    def agent_type(self) -> str:
        return "tool"
    
    @property
    def description(self) -> str:
        return "Provides tool and component recommendations for door installation"
    
    def process(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Process a query to provide tool and component recommendations.
        
        Args:
            query: User query.
            **kwargs: Additional arguments including door type and category.
            
        Returns:
            Dictionary with tool recommendations and relevant information.
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
            
            # Add content type filter to prioritize tool information
            filter_dict["content_type"] = ["tool", "component"]
            
            # Retrieve relevant documents
            documents = self._retrieve_documents(
                query=query,
                filter_dict=filter_dict,
                top_k=5
            )
            
            # If no tool information found, try without content type filter
            if not documents:
                if "content_type" in filter_dict:
                    del filter_dict["content_type"]
                
                documents = self._retrieve_documents(
                    query=query,
                    filter_dict=filter_dict,
                    top_k=5
                )
            
            # Format documents as context
            context = self._format_documents_as_context(documents)
            
            # Build prompt for tool/component guidance
            messages = PromptBuilder.build_tool_component_prompt(
                query=query,
                context=context,
                door_type=door_type,
                door_category=door_category
            )
            
            # Generate response
            response = self._generate_response(messages, temperature=0.3)
            
            # Format response to extract structured information
            formatted_response = ResponseFormatter.format_tool_recommendations(response)
            
            # Return the tool/component information
            return {
                "guidance": response,
                "tools": formatted_response.get("tools", []),
                "usage": formatted_response.get("usage", ""),
                "alternatives": formatted_response.get("alternatives", []),
                "door_category": door_category,
                "door_type": door_type,
                "document_count": len(documents)
            }
        
        except Exception as e:
            logger.error(f"Error providing tool recommendations: {str(e)}")
            return {
                "guidance": "I'm sorry, I encountered an error while generating tool recommendations. Please try again with a more specific question.",
                "tools": [],
                "usage": "",
                "alternatives": [],
                "door_category": kwargs.get("door_category", "unknown"),
                "door_type": kwargs.get("door_type", "unknown"),
                "error": str(e)
            }
    
    def get_recommended_tools(self, door_category: str, door_type: str) -> Dict[str, Any]:
        """
        Get recommended tools for a specific door type.
        
        Args:
            door_category: Door category.
            door_type: Door type.
            
        Returns:
            Dictionary with recommended tools and equipment.
        """
        try:
            # Create filter for document retrieval
            filter_dict = {
                "content_type": "tool"
            }
            
            if door_category != "unknown":
                filter_dict["door_category"] = door_category
            if door_type != "unknown":
                filter_dict["door_type"] = door_type
            
            # Retrieve relevant documents
            documents = self._retrieve_documents(
                query=f"What tools do I need for installing a {door_type} {door_category} door?",
                filter_dict=filter_dict,
                top_k=3
            )
            
            # Format documents as context
            context = self._format_documents_as_context(documents)
            
            # Build prompt for tool recommendations
            messages = PromptBuilder.build_tool_component_prompt(
                query=f"What are the essential tools and equipment I need for installing a {door_type} door? Please provide a complete list with brief explanations of what each tool is used for.",
                context=context,
                door_type=door_type,
                door_category=door_category
            )
            
            # Generate response
            response = self._generate_response(messages, temperature=0.2)
            
            # Format response to extract structured tool information
            formatted_response = ResponseFormatter.format_tool_recommendations(response)
            
            return {
                "tool_list": formatted_response.get("tools", []),
                "essential_tools": [tool for tool in formatted_response.get("tools", []) if "optional" not in tool.get("description", "").lower()],
                "optional_tools": [tool for tool in formatted_response.get("tools", []) if "optional" in tool.get("description", "").lower()],
                "raw_response": response,
                "found": len(documents) > 0
            }
        
        except Exception as e:
            logger.error(f"Error retrieving recommended tools: {str(e)}")
            return {
                "tool_list": [],
                "essential_tools": [],
                "optional_tools": [],
                "raw_response": f"Error retrieving tools: {str(e)}",
                "found": False,
                "error": str(e)
            }
    
    def get_component_details(self, component_name: str, door_category: str, door_type: str) -> Dict[str, Any]:
        """
        Get details about a specific door component.
        
        Args:
            component_name: Name of the component.
            door_category: Door category.
            door_type: Door type.
            
        Returns:
            Dictionary with component details.
        """
        try:
            # Create filter for document retrieval
            filter_dict = {
                "content_type": "component"
            }
            
            if door_category != "unknown":
                filter_dict["door_category"] = door_category
            if door_type != "unknown":
                filter_dict["door_type"] = door_type
            
            # Retrieve relevant documents
            documents = self._retrieve_documents(
                query=f"{component_name} {door_type} door component",
                filter_dict=filter_dict,
                top_k=3
            )
            
            # Format documents as context
            context = self._format_documents_as_context(documents)
            
            # Build prompt for component details
            messages = PromptBuilder.build_tool_component_prompt(
                query=f"What is a {component_name} in a {door_type} door? Please describe its purpose, how it's installed, and any common issues with this component.",
                context=context,
                door_type=door_type,
                door_category=door_category
            )
            
            # Generate response
            response = self._generate_response(messages, temperature=0.3)
            
            return {
                "component_name": component_name,
                "description": response,
                "found": len(documents) > 0
            }
        
        except Exception as e:
            logger.error(f"Error retrieving component details: {str(e)}")
            return {
                "component_name": component_name,
                "description": f"I'm sorry, I couldn't find specific information about the {component_name}.",
                "found": False,
                "error": str(e)
            }