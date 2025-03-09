# door_installation_assistant/agent_system/agent_orchestrator.py
import logging
import re
from typing import Dict, Any, List, Optional, Tuple

from ..config.app_config import get_config
from .agent_factory import AgentFactory
from .memory.conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Orchestrates the collaboration between agents."""
    
    def __init__(self):
        self.config = get_config().agent
        self.agent_factory = AgentFactory()
        self.agents = self.agent_factory.create_agents()
        self.memory = ConversationMemory()
    
    def process_query(self, query: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Process a user query by orchestrating agents.
        
        Args:
            query: User query.
            session_id: Session identifier for conversation context.
            
        Returns:
            Dictionary with the processing results.
        """
        try:
            # Add query to conversation memory
            self.memory.add_user_message(session_id, query)
            
            # Analyze query to determine intent
            query_analysis = self._analyze_query(query)
            
            # Log analysis
            logger.info(f"Query analysis: {query_analysis}")
            
            # Determine primary agent based on intent
            primary_agent_type = self._determine_primary_agent(query_analysis)
            
            # Execute agent workflow based on intent
            if primary_agent_type == "door_identifier":
                response = self._handle_door_identification(query, session_id)
            elif primary_agent_type == "procedure":
                response = self._handle_installation_procedure(query, query_analysis, session_id)
            elif primary_agent_type == "tool":
                response = self._handle_tool_guidance(query, query_analysis, session_id)
            elif primary_agent_type == "troubleshooting":
                response = self._handle_troubleshooting(query, query_analysis, session_id)
            elif primary_agent_type == "safety":
                response = self._handle_safety_guidance(query, query_analysis, session_id)
            else:
                response = self._handle_general_query(query, query_analysis, session_id)
            
            # Add response to conversation memory
            self.memory.add_assistant_message(session_id, response["response"])
            
            return response
        
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            error_response = {
                "response": "I'm sorry, I encountered an error while processing your query. Please try again with a more specific question.",
                "error": str(e)
            }
            self.memory.add_assistant_message(session_id, error_response["response"])
            return error_response
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a query to determine intent, door type, etc.
        
        Args:
            query: User query.
            
        Returns:
            Dictionary with analysis results.
        """
        # Use the door identifier agent to determine door type and category
        door_info = self.agents["door_identifier"].process(query)
        
        # Determine primary intent
        intent = self._determine_intent(query)
        
        # Combine door info and intent
        analysis = {
            "intent": intent,
            "door_category": door_info["door_category"],
            "door_type": door_info["door_type"],
            "confidence": door_info["confidence"],
            "query": query
        }
        
        return analysis
    
    def _determine_intent(self, query: str) -> str:
        """
        Determine the primary intent of a query.
        
        Args:
            query: User query.
            
        Returns:
            Intent string.
        """
        query_lower = query.lower()
        
        # Check for installation intent
        if any(keyword in query_lower for keyword in ["install", "installing", "setup", "put together", "assemble", "mounting", "hang"]):
            return "installation"
        
        # Check for troubleshooting intent
        if any(keyword in query_lower for keyword in ["problem", "issue", "doesn't work", "not working", "fix", "repair", "stuck", "won't close", "gap", "troubleshoot"]):
            return "troubleshooting"
        
        # Check for tool/component intent
        if any(keyword in query_lower for keyword in ["tool", "component", "part", "hardware", "equipment", "need to buy", "material", "supplies"]):
            return "tool_component"
        
        # Check for safety intent
        if any(keyword in query_lower for keyword in ["safety", "precaution", "careful", "warning", "danger", "injury", "protect"]):
            return "safety"
        
        # Default to general inquiry about installation
        return "general_installation"
    
    def _determine_primary_agent(self, query_analysis: Dict[str, Any]) -> str:
        """
        Determine the primary agent based on query analysis.
        
        Args:
            query_analysis: Query analysis results.
            
        Returns:
            Primary agent type.
        """
        intent = query_analysis["intent"]
        
        if intent == "installation":
            return "procedure"
        elif intent == "troubleshooting":
            return "troubleshooting"
        elif intent == "tool_component":
            return "tool"
        elif intent == "safety":
            return "safety"
        else:
            # For unknown door type/category, use door identifier
            if query_analysis["door_category"] == "unknown" or query_analysis["door_type"] == "unknown":
                return "door_identifier"
            else:
                return "procedure"  # Default to procedure agent
    
    def _handle_door_identification(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Handle door identification queries.
        
        Args:
            query: User query.
            session_id: Session identifier.
            
        Returns:
            Dictionary with response.
        """
        # Process with door identifier agent
        door_info = self.agents["door_identifier"].process(query)
        
        # Generate response based on identification
        if door_info["door_category"] != "unknown" and door_info["door_type"] != "unknown":
            response = f"I understand you're asking about a {door_info['door_type']} door ({door_info['door_category']} door). How can I help you with this door type?"
        elif door_info["door_category"] != "unknown":
            response = f"I understand you're asking about an {door_info['door_category']} door. Could you please specify which type of {door_info['door_category']} door you're working with?"
        elif door_info["door_type"] != "unknown":
            response = f"I understand you're asking about a {door_info['door_type']} door. How can I help you with this door type?"
        else:
            response = "I'm not sure which type of door you're asking about. Could you please specify whether you're working with an interior door (like a bifold or prehung) or an exterior door (like an entry door, patio door, or dentil shelf)?"
        
        return {
            "response": response,
            "agent": "door_identifier",
            "door_info": door_info
        }
    
    def _handle_installation_procedure(self, query: str, query_analysis: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Handle installation procedure queries.
        
        Args:
            query: User query.
            query_analysis: Query analysis results.
            session_id: Session identifier.
            
        Returns:
            Dictionary with response.
        """
        # Get door information
        door_category = query_analysis["door_category"]
        door_type = query_analysis["door_type"]
        
        # Process with procedure agent
        procedure_result = self.agents["procedure"].process(
            query=query,
            door_category=door_category,
            door_type=door_type
        )
        
        # Get safety considerations if available
        safety_considerations = ""
        if "safety" in self.agents:
            safety_result = self.agents["safety"].process(
                query=f"Safety considerations for installing {door_type} {door_category} door",
                door_category=door_category,
                door_type=door_type
            )
            safety_considerations = safety_result.get("safety_guidance", "")
        
        # Combine procedure and safety considerations if available and not empty
        response = procedure_result["procedure"]
        if safety_considerations and safety_considerations not in response:
            response += f"\n\n## Safety Considerations\n{safety_considerations}"
        
        return {
            "response": response,
            "agent": "procedure",
            "door_category": door_category,
            "door_type": door_type,
            "step_info": procedure_result.get("step_info", {})
        }
    
    def _handle_tool_guidance(self, query: str, query_analysis: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Handle tool/component guidance queries.
        
        Args:
            query: User query.
            query_analysis: Query analysis results.
            session_id: Session identifier.
            
        Returns:
            Dictionary with response.
        """
        # Get door information
        door_category = query_analysis["door_category"]
        door_type = query_analysis["door_type"]
        
        # Process with tool agent
        tool_result = self.agents["tool"].process(
            query=query,
            door_category=door_category,
            door_type=door_type
        )
        
        return {
            "response": tool_result["guidance"],
            "agent": "tool",
            "door_category": door_category,
            "door_type": door_type,
            "tools": tool_result.get("tools", [])
        }
    
    def _handle_troubleshooting(self, query: str, query_analysis: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Handle troubleshooting queries.
        
        Args:
            query: User query.
            query_analysis: Query analysis results.
            session_id: Session identifier.
            
        Returns:
            Dictionary with response.
        """
        # Get door information
        door_category = query_analysis["door_category"]
        door_type = query_analysis["door_type"]
        
        # Process with troubleshooting agent
        troubleshooting_result = self.agents["troubleshooting"].process(
            query=query,
            door_category=door_category,
            door_type=door_type
        )
        
        return {
            "response": troubleshooting_result["solution"],
            "agent": "troubleshooting",
            "door_category": door_category,
            "door_type": door_type,
            "issues": troubleshooting_result.get("issues", [])
        }
    
    def _handle_safety_guidance(self, query: str, query_analysis: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Handle safety guidance queries.
        
        Args:
            query: User query.
            query_analysis: Query analysis results.
            session_id: Session identifier.
            
        Returns:
            Dictionary with response.
        """
        # Get door information
        door_category = query_analysis["door_category"]
        door_type = query_analysis["door_type"]
        
        # Process with safety agent
        safety_result = self.agents["safety"].process(
            query=query,
            door_category=door_category,
            door_type=door_type
        )
        
        return {
            "response": safety_result["safety_guidance"],
            "agent": "safety",
            "door_category": door_category,
            "door_type": door_type
        }
    
    def _handle_general_query(self, query: str, query_analysis: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Handle general queries that don't fit specific categories.
        
        Args:
            query: User query.
            query_analysis: Query analysis results.
            session_id: Session identifier.
            
        Returns:
            Dictionary with response.
        """
        # Get door information
        door_category = query_analysis["door_category"]
        door_type = query_analysis["door_type"]
        
        # Try with procedure agent first
        procedure_result = self.agents["procedure"].process(
            query=query,
            door_category=door_category,
            door_type=door_type
        )
        
        # If procedure agent didn't find much, try troubleshooting
        if procedure_result.get("document_count", 0) < 2:
            troubleshooting_result = self.agents["troubleshooting"].process(
                query=query,
                door_category=door_category,
                door_type=door_type
            )
            
            # Use whichever found more relevant information
            if troubleshooting_result.get("document_count", 0) > procedure_result.get("document_count", 0):
                return {
                    "response": troubleshooting_result["solution"],
                    "agent": "troubleshooting",
                    "door_category": door_category,
                    "door_type": door_type
                }
        
        return {
            "response": procedure_result["procedure"],
            "agent": "procedure",
            "door_category": door_category,
            "door_type": door_type
        }
    
    def get_conversation_history(self, session_id: str = "default") -> List[Dict[str, str]]:
        """
        Get the conversation history for a session.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            List of messages in the conversation history.
        """
        return self.memory.get_messages(session_id)
    
    def clear_conversation_history(self, session_id: str = "default") -> None:
        """
        Clear the conversation history for a session.
        
        Args:
            session_id: Session identifier.
        """
        self.memory.clear_messages(session_id)