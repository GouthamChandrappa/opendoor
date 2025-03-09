# door_installation_assistant/agent_system/agents/door_identifier.py
import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple

from .base_agent import Agent
from ...llm_integration.prompt_templates import PromptBuilder

logger = logging.getLogger(__name__)

class DoorIdentifierAgent(Agent):
    """Agent for identifying door types from user queries."""
    
    @property
    def agent_type(self) -> str:
        return "door_identifier"
    
    @property
    def description(self) -> str:
        return "Identifies door types and categories from user queries"
    
    def process(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Process a query to identify door type and category.
        
        Args:
            query: User query.
            **kwargs: Additional arguments.
            
        Returns:
            Dictionary with identified door type and category.
        """
        try:
            # First try to identify door type and category from the query text directly
            door_info = self._extract_door_info_from_text(query)
            
            # If not found, use LLM to identify
            if door_info["door_category"] == "unknown" or door_info["door_type"] == "unknown":
                llm_door_info = self._identify_with_llm(query)
                
                # Update unknown fields with LLM results
                if door_info["door_category"] == "unknown":
                    door_info["door_category"] = llm_door_info["door_category"]
                
                if door_info["door_type"] == "unknown":
                    door_info["door_type"] = llm_door_info["door_type"]
            
            # Add confidence score based on method used
            door_info["confidence"] = self._calculate_confidence(door_info)
            
            # Log the identification result
            logger.info(f"Identified door: category={door_info['door_category']}, type={door_info['door_type']}, confidence={door_info['confidence']}")
            
            return door_info
        
        except Exception as e:
            logger.error(f"Error identifying door: {str(e)}")
            return {
                "door_category": "unknown",
                "door_type": "unknown",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _extract_door_info_from_text(self, text: str) -> Dict[str, str]:
        """
        Extract door type and category from text using pattern matching.
        
        Args:
            text: Text to extract from.
            
        Returns:
            Dictionary with door_category and door_type.
        """
        text_lower = text.lower()
        
        # Initialize with unknown values
        door_info = {
            "door_category": "unknown",
            "door_type": "unknown"
        }
        
        # Check for door categories
        if "interior" in text_lower:
            door_info["door_category"] = "interior"
        elif "exterior" in text_lower:
            door_info["door_category"] = "exterior"
        
        # Check for interior door types
        if "bifold" in text_lower:
            door_info["door_type"] = "bifold"
            door_info["door_category"] = "interior"  # Bifold is always interior
        elif "prehung" in text_lower and "interior" in text_lower:
            door_info["door_type"] = "prehung"
            door_info["door_category"] = "interior"
        
        # Check for exterior door types
        elif "entry" in text_lower or "front" in text_lower:
            door_info["door_type"] = "entry door"
            door_info["door_category"] = "exterior"  # Entry is always exterior
        elif "patio" in text_lower or "sliding" in text_lower:
            door_info["door_type"] = "patio door"
            door_info["door_category"] = "exterior"  # Patio is always exterior
        elif "dentil" in text_lower or "shelf" in text_lower:
            door_info["door_type"] = "dentil shelf"
            door_info["door_category"] = "exterior"  # Dentil shelf is always exterior
        elif "prehung" in text_lower and "exterior" in text_lower:
            door_info["door_type"] = "entry door"
            door_info["door_category"] = "exterior"
        
        return door_info
    
    def _identify_with_llm(self, query: str) -> Dict[str, str]:
        """
        Identify door type and category using the LLM.
        
        Args:
            query: User query.
            
        Returns:
            Dictionary with door_category and door_type.
        """
        # Build prompt for door identification
        messages = PromptBuilder.build_door_identification_prompt(query)
        
        # Generate response
        response = self._generate_response(messages, temperature=0.1)
        
        # Parse the response
        door_info = self._parse_door_identification_response(response)
        
        return door_info
    
    def _parse_door_identification_response(self, response: str) -> Dict[str, str]:
        """
        Parse the LLM's door identification response.
        
        Args:
            response: LLM response text.
            
        Returns:
            Dictionary with door_category and door_type.
        """
        # Initialize with unknown values
        door_info = {
            "door_category": "unknown",
            "door_type": "unknown"
        }
        
        # Look for door category in the response
        category_match = re.search(r"Door Category:\s*(\w+)", response, re.IGNORECASE)
        if category_match:
            category = category_match.group(1).lower()
            if category in ("interior", "exterior"):
                door_info["door_category"] = category
        
        # Look for door type in the response
        type_match = re.search(r"Door Type:\s*([a-zA-Z\s]+)", response, re.IGNORECASE)
        if type_match:
            door_type = type_match.group(1).strip().lower()
            
            # Map to standardized door types
            if "bifold" in door_type:
                door_info["door_type"] = "bifold"
            elif "prehung" in door_type and door_info["door_category"] == "interior":
                door_info["door_type"] = "prehung"
            elif "entry" in door_type or "front" in door_type:
                door_info["door_type"] = "entry door"
            elif "patio" in door_type or "sliding" in door_type:
                door_info["door_type"] = "patio door"
            elif "dentil" in door_type or "shelf" in door_type:
                door_info["door_type"] = "dentil shelf"
            elif "prehung" in door_type and door_info["door_category"] == "exterior":
                door_info["door_type"] = "entry door"
        
        return door_info
    
    def _calculate_confidence(self, door_info: Dict[str, str]) -> float:
        """
        Calculate confidence score for door identification.
        
        Args:
            door_info: Door identification information.
            
        Returns:
            Confidence score between 0.0 and 1.0.
        """
        # Base confidence
        confidence = 0.5
        
        # Adjust based on door category
        if door_info["door_category"] != "unknown":
            confidence += 0.2
        
        # Adjust based on door type
        if door_info["door_type"] != "unknown":
            confidence += 0.3
        
        # Ensure confidence is between 0.0 and 1.0
        return min(1.0, max(0.0, confidence))