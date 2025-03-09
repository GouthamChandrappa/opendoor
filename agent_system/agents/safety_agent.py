# door_installation_assistant/agent_system/agents/safety_agent.py
import logging
from typing import Dict, Any, List, Optional, Tuple
import re

from .base_agent import Agent
from ...llm_integration.prompt_templates import PromptBuilder

logger = logging.getLogger(__name__)

class SafetyAgent(Agent):
    """Agent for providing safety guidance for door installation."""
    
    @property
    def agent_type(self) -> str:
        return "safety"
    
    @property
    def description(self) -> str:
        return "Provides safety guidelines and precautions for door installation"
    
    def process(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Process a query to provide safety guidance.
        
        Args:
            query: User query.
            **kwargs: Additional arguments including door type and category.
            
        Returns:
            Dictionary with safety guidance and relevant information.
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
            
            # Include safety-related terms in the query
            safety_query = f"safety precautions {query}" if "safety" not in query.lower() else query
            
            # Retrieve relevant documents
            documents = self._retrieve_documents(
                query=safety_query,
                filter_dict=filter_dict,
                top_k=5
            )
            
            # Format documents as context
            context = self._format_documents_as_context(documents)
            
            # Check if any safety information was found
            if not self._contains_safety_info(context):
                # Get general safety information if specific info not found
                general_safety = self._get_general_safety_info(door_category, door_type)
                context = context + "\n\n" + general_safety if context else general_safety
            
            # Build prompt for safety guidance
            system_prompt = f"""
You are an AI assistant specializing in door installation safety. Your task is to provide 
comprehensive safety guidance for {door_type} door ({door_category} category) installation.

Based on the provided context, give clear safety precautions and guidelines. Focus on:
1. Personal protective equipment (PPE) requirements
2. Tool safety
3. Safe handling techniques for heavy doors
4. Electrical safety (if applicable)
5. Common safety hazards and how to avoid them

Format your response with clear headings and bullet points. Prioritize the most critical safety 
information first. If the context doesn't contain specific safety information for this door type, 
provide general door installation safety guidelines while acknowledging the limitation.

Remember that your guidance could prevent injuries, so be thorough and emphasize the most 
important precautions.
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context information:\n\n{context}\n\nPlease provide safety guidance for installing a {door_type} door ({door_category} category)."}
            ]
            
            # Generate response
            response = self._generate_response(messages, temperature=0.3)
            
            # Extract safety precautions from response
            safety_precautions = self._extract_safety_precautions(response)
            
            # Return the safety guidance information
            return {
                "safety_guidance": response,
                "safety_precautions": safety_precautions,
                "door_category": door_category,
                "door_type": door_type,
                "document_count": len(documents)
            }
        
        except Exception as e:
            logger.error(f"Error providing safety guidance: {str(e)}")
            return {
                "safety_guidance": "I'm sorry, I encountered an error while generating safety guidance. Please remember to always wear appropriate personal protective equipment and follow manufacturer instructions when installing doors.",
                "safety_precautions": [],
                "door_category": kwargs.get("door_category", "unknown"),
                "door_type": kwargs.get("door_type", "unknown"),
                "error": str(e)
            }
    
    def _contains_safety_info(self, context: str) -> bool:
        """
        Check if the context contains safety information.
        
        Args:
            context: Document context.
            
        Returns:
            True if safety information is present, False otherwise.
        """
        safety_terms = [
            "safety", "precaution", "warning", "caution", "danger", "hazard", 
            "protective", "ppe", "gloves", "goggles", "mask", "helmet",
            "injury", "careful", "protect"
        ]
        
        return any(term in context.lower() for term in safety_terms)
    
    def _get_general_safety_info(self, door_category: str, door_type: str) -> str:
        """
        Get general safety information for door installation.
        
        Args:
            door_category: Door category.
            door_type: Door type.
            
        Returns:
            General safety information.
        """
        # This information is used when no specific safety info is found in the documents
        return f"""
General safety guidelines for door installation:

1. Personal Protective Equipment (PPE):
   - Always wear gloves to protect hands from splinters, sharp edges, and pinch points
   - Safety glasses or goggles should be worn when using power tools
   - Steel-toed boots are recommended when handling heavy doors
   - Dust mask when cutting or sanding door materials

2. Tool Safety:
   - Ensure all tools are in good working condition before use
   - Read and follow manufacturer's instructions for all tools
   - Keep power cords away from cutting areas
   - Disconnect power tools when changing blades or bits
   - Use tools only for their intended purpose

3. Safe Handling:
   - Always have assistance when lifting and positioning heavy doors
   - Use proper lifting technique: bend at the knees, keep back straight
   - Clear the work area of obstacles before moving doors
   - Use door jacks or temporary supports to hold doors during installation

4. General Precautions:
   - Ensure work area is well-lit and ventilated
   - Keep work area clean to prevent trips and falls
   - Keep children and pets away from work area
   - Secure loose clothing and remove jewelry before working
   - Take breaks to avoid fatigue which can lead to accidents

5. Special considerations for {door_type} doors ({door_category} category):
   - Follow specific manufacturer guidelines for this door type
   - Be aware of the door's weight and dimensions for safe handling
   - Use appropriate hardware and fasteners specified for this door type
"""
    
    def _extract_safety_precautions(self, response: str) -> List[str]:
        """
        Extract safety precautions from the response.
        
        Args:
            response: LLM response text.
            
        Returns:
            List of safety precautions.
        """
        safety_precautions = []
        
        # Extract bullet points that contain safety information
        bullet_pattern = r'(?:^|\n)[•\*\-]\s+(.*?)(?=\n[•\*\-]|\n\n|\Z)'
        bullet_matches = re.finditer(bullet_pattern, response)
        
        for match in bullet_matches:
            precaution = match.group(1).strip()
            # Only include if it contains safety-related information
            if any(term in precaution.lower() for term in ["safety", "protect", "hazard", "danger", "careful", "caution", "warning", "avoid", "injury", "risk", "ppe", "glove", "goggle", "mask"]):
                safety_precautions.append(precaution)
        
        # If no bullet points found, try to extract from paragraphs
        if not safety_precautions:
            paragraphs = re.split(r'\n\n+', response)
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                # Check if paragraph contains safety-related information
                if any(term in paragraph.lower() for term in ["safety", "protect", "hazard", "danger", "careful", "caution", "warning", "avoid", "injury", "risk", "ppe", "glove", "goggle", "mask"]):
                    safety_precautions.append(paragraph)
        
        return safety_precautions
    
    def get_ppe_recommendations(self, door_category: str, door_type: str) -> Dict[str, Any]:
        """
        Get personal protective equipment (PPE) recommendations for a specific door type.
        
        Args:
            door_category: Door category.
            door_type: Door type.
            
        Returns:
            Dictionary with PPE recommendations.
        """
        try:
            # Create filter for document retrieval
            filter_dict = {}
            
            if door_category != "unknown":
                filter_dict["door_category"] = door_category
            if door_type != "unknown":
                filter_dict["door_type"] = door_type
            
            # Retrieve relevant documents
            documents = self._retrieve_documents(
                query=f"personal protective equipment PPE safety {door_type} door installation",
                filter_dict=filter_dict,
                top_k=3
            )
            
            # Format documents as context
            context = self._format_documents_as_context(documents)
            
            # Build prompt for PPE recommendations
            system_prompt = f"""
You are an AI assistant specializing in door installation safety. Your task is to provide 
specific personal protective equipment (PPE) recommendations for {door_type} door installation.

Based on the provided context, list all recommended PPE items with a brief explanation of why 
each item is needed. If the context doesn't contain specific PPE information for this door type, 
provide general PPE recommendations for door installation while acknowledging the limitation.

Format your response as a structured list of PPE items. For each item, include:
1. The PPE item name
2. When it should be worn during the installation process
3. What specific hazards it protects against
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context information:\n\n{context}\n\nWhat PPE is recommended for installing a {door_type} door ({door_category} category)?"}
            ]
            
            # Generate response
            response = self._generate_response(messages, temperature=0.2)
            
            # Extract PPE items from response
            ppe_items = self._extract_ppe_items(response)
            
            return {
                "ppe_recommendations": response,
                "ppe_items": ppe_items,
                "found": len(documents) > 0
            }
        
        except Exception as e:
            logger.error(f"Error retrieving PPE recommendations: {str(e)}")
            return {
                "ppe_recommendations": "Unable to retrieve PPE recommendations.",
                "ppe_items": [],
                "found": False,
                "error": str(e)
            }
    
    def _extract_ppe_items(self, response: str) -> List[Dict[str, str]]:
        """
        Extract PPE items from the response.
        
        Args:
            response: LLM response text.
            
        Returns:
            List of PPE items.
        """
        ppe_items = []
        
        # Extract numbered items or bullet points that contain PPE information
        item_pattern = r'(?:^|\n)(?:(\d+)\.|\*|\-|•)\s+(.*?)(?=\n(?:\d+\.|\*|\-|•)|\n\n|\Z)'
        item_matches = re.finditer(item_pattern, response, re.MULTILINE)
        
        for match in item_matches:
            item_text = match.group(2).strip()
            
            # Try to parse item name and description
            item_parts = re.split(r'(?::|–|-)\s+', item_text, 1)
            
            if len(item_parts) > 1:
                item_name = item_parts[0].strip()
                item_description = item_parts[1].strip()
            else:
                # Try to extract item name (usually at the beginning, often in bold or caps)
                name_match = re.match(r'(?:\*\*|__)?([\w\s]+)(?:\*\*|__)?\s*', item_text)
                if name_match:
                    item_name = name_match.group(1).strip()
                    item_description = item_text[len(name_match.group(0)):].strip()
                else:
                    item_name = item_text.split()[0] if item_text.split() else "Unknown PPE"
                    item_description = item_text
            
            ppe_items.append({
                "item": item_name,
                "description": item_description
            })
        
        return ppe_items
    
    def get_safety_checklist(self, door_category: str, door_type: str) -> Dict[str, Any]:
        """
        Get a safety checklist for a specific door installation.
        
        Args:
            door_category: Door category.
            door_type: Door type.
            
        Returns:
            Dictionary with safety checklist.
        """
        try:
            # Create filter for document retrieval
            filter_dict = {}
            
            if door_category != "unknown":
                filter_dict["door_category"] = door_category
            if door_type != "unknown":
                filter_dict["door_type"] = door_type
            
            # Retrieve relevant documents
            documents = self._retrieve_documents(
                query=f"safety checklist {door_type} door installation",
                filter_dict=filter_dict,
                top_k=3
            )
            
            # Format documents as context
            context = self._format_documents_as_context(documents)
            
            # Build prompt for safety checklist
            system_prompt = f"""
You are an AI assistant specializing in door installation safety. Your task is to create 
a comprehensive safety checklist for {door_type} door ({door_category} category) installation.

Based on the provided context, create a checklist that installers should review before, during, 
and after the installation process. Format your response as a three-part checklist with 
clear, actionable items.

For each checklist item:
1. Make it specific and actionable
2. Focus on critical safety issues
3. Use clear, concise language

If the context doesn't contain specific safety information for this door type, 
provide a general door installation safety checklist while acknowledging the limitation.
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context information:\n\n{context}\n\nPlease create a safety checklist for installing a {door_type} door ({door_category} category)."}
            ]
            
            # Generate response
            response = self._generate_response(messages, temperature=0.3)
            
            # Extract checklist items from response
            checklist = self._extract_checklist_items(response)
            
            return {
                "safety_checklist": response,
                "checklist_items": checklist,
                "found": len(documents) > 0
            }
        
        except Exception as e:
            logger.error(f"Error creating safety checklist: {str(e)}")
            return {
                "safety_checklist": "Unable to create safety checklist.",
                "checklist_items": {},
                "found": False,
                "error": str(e)
            }
    
    def _extract_checklist_items(self, response: str) -> Dict[str, List[str]]:
        """
        Extract checklist items from the response.
        
        Args:
            response: LLM response text.
            
        Returns:
            Dictionary with before, during, and after checklist items.
        """
        checklist = {
            "before": [],
            "during": [],
            "after": []
        }
        
        # Extract sections
        before_match = re.search(r'(?:Before Installation|Pre-Installation|Before You Begin):(.*?)(?=(?:During Installation|Installation Process|While Installing):|$)', response, re.DOTALL | re.IGNORECASE)
        during_match = re.search(r'(?:During Installation|Installation Process|While Installing):(.*?)(?=(?:After Installation|Post-Installation|Finishing Up):|$)', response, re.DOTALL | re.IGNORECASE)
        after_match = re.search(r'(?:After Installation|Post-Installation|Finishing Up):(.*?)', response, re.DOTALL | re.IGNORECASE)
        
        # Extract items from each section
        if before_match:
            before_text = before_match.group(1).strip()
            checklist["before"] = self._extract_list_items(before_text)
        
        if during_match:
            during_text = during_match.group(1).strip()
            checklist["during"] = self._extract_list_items(during_text)
        
        if after_match:
            after_text = after_match.group(1).strip()
            checklist["after"] = self._extract_list_items(after_text)
        
        # If no sections found, try to extract all items
        if not any(checklist.values()):
            all_items = self._extract_list_items(response)
            
            # Categorize items based on keywords
            for item in all_items:
                if any(term in item.lower() for term in ["before", "prepare", "check", "ensure", "verify", "prior"]):
                    checklist["before"].append(item)
                elif any(term in item.lower() for term in ["after", "complete", "finish", "once", "final"]):
                    checklist["after"].append(item)
                else:
                    checklist["during"].append(item)
        
        return checklist
    
    def _extract_list_items(self, text: str) -> List[str]:
        """
        Extract list items from text.
        
        Args:
            text: Text containing list items.
            
        Returns:
            List of extracted items.
        """
        items = []
        
        # Extract numbered items or bullet points
        item_pattern = r'(?:^|\n)(?:\d+\.|\*|\-|•)\s+(.*?)(?=\n(?:\d+\.|\*|\-|•)|\n\n|\Z)'
        item_matches = re.finditer(item_pattern, text)
        
        for match in item_matches:
            items.append(match.group(1).strip())
        
        return items