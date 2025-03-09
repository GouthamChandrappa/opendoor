# door_installation_assistant/llm_integration/llm_manager.py
import logging
import os
from typing import List, Dict, Any, Optional, Union
import json
import time
import openai

from ..config.app_config import get_config

logger = logging.getLogger(__name__)

class LLMManager:
    """Manages interactions with language models."""
    
    def __init__(self):
        self.config = get_config().llm
        self._setup_provider()
    
    def _setup_provider(self):
        """Set up the LLM provider based on configuration."""
        provider = self.config.provider.lower()
        
        if provider == "openai":
            self._setup_openai()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def _setup_openai(self):
        """Set up OpenAI client."""
        api_key = self.config.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided.")
        
        # Use the OpenAI API key
        openai.api_key = api_key
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Generate a response from the language model.
        
        Args:
            messages: List of message dictionaries with role and content.
            temperature: Temperature for generation.
            max_tokens: Maximum tokens for response.
            model: Model to use.
            
        Returns:
            Generated response text.
        """
        provider = self.config.provider.lower()
        
        if provider == "openai":
            return self._generate_openai_response(messages, temperature, max_tokens, model)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def _generate_openai_response(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> str:
        """Generate a response using OpenAI."""
        try:
            # Use configured values if not provided
            if temperature is None:
                temperature = self.config.temperature
            
            if max_tokens is None:
                max_tokens = self.config.max_tokens
            
            if model is None:
                model = self.config.model_name
            
            # Retry mechanism for API rate limits
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    response = openai.ChatCompletion.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    # Extract and return the response text
                    return response.choices[0].message.content
                
                except openai.error.RateLimitError:
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limit hit, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise
        
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            return f"I'm sorry, I encountered an error while generating a response. Please try again later."
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a user query to determine intent, door type, etc.
        
        Args:
            query: User query.
            
        Returns:
            Dictionary with analysis results.
        """
        try:
            messages = [
                {"role": "system", "content": (
                    "You are an AI assistant for door installation. "
                    "Analyze the user's query about door installation and extract the following information: "
                    "1. Primary intent (installation, troubleshooting, tool requirements, component identification) "
                    "2. Door category (interior, exterior) if mentioned "
                    "3. Door type (bifold, prehung, entry, patio, dentil shelf) if mentioned "
                    "4. Specific installation step or issue if mentioned "
                    "5. Tool or component mentioned "
                    "Respond with a JSON object containing these fields."
                )},
                {"role": "user", "content": query}
            ]
            
            response = self.generate_response(
                messages=messages,
                temperature=0.0,  # Use low temperature for consistent structured output
                model=self.config.model_name
            )
            
            # Parse the JSON response
            try:
                # Extract JSON if it's embedded in other text
                json_match = re.search(r'({.*})', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    analysis = json.loads(json_str)
                else:
                    analysis = json.loads(response)
                
                return analysis
            
            except (json.JSONDecodeError, AttributeError):
                # If JSON parsing fails, return a basic structure
                logger.warning(f"Failed to parse analysis JSON: {response}")
                return {
                    "primary_intent": "unknown",
                    "door_category": None,
                    "door_type": None,
                    "installation_step": None,
                    "tool_component": None
                }
        
        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}")
            return {
                "primary_intent": "unknown",
                "door_category": None,
                "door_type": None,
                "installation_step": None,
                "tool_component": None
            }
    
    def generate_installation_response(
        self,
        query: str,
        retrieved_documents: List[Dict[str, Any]],
        door_category: Optional[str] = None,
        door_type: Optional[str] = None
    ) -> str:
        """
        Generate a response for an installation query using retrieved documents.
        
        Args:
            query: User query.
            retrieved_documents: List of retrieved documents.
            door_category: Door category (interior, exterior).
            door_type: Door type (bifold, prehung, entry, patio, dentil shelf).
            
        Returns:
            Generated response text.
        """
        try:
            # Prepare the context from retrieved documents
            context = ""
            for i, doc in enumerate(retrieved_documents):
                doc_text = doc.get("text", "")
                context += f"Document {i+1}:\n{doc_text}\n\n"
            
            # Build the system message
            system_message = (
                "You are an AI assistant for door installation, helping junior mechanics in the field. "
                "Use the provided documents to answer the user's query about door installation. "
                "Focus on providing clear, step-by-step instructions that are easy to follow. "
                "If information is missing from the documents, acknowledge that and provide general guidance. "
                "Do not reference document numbers in your response. "
                "Format your response with clear headings, bullet points, and numbered steps where appropriate."
            )
            
            # Add door-specific information if available
            if door_category:
                system_message += f" The user is asking about {door_category} doors."
            
            if door_type:
                system_message += f" Specifically, they are asking about {door_type} doors."
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Documents for reference:\n\n{context}\n\nUser query: {query}"}
            ]
            
            # Generate response
            response = self.generate_response(
                messages=messages,
                temperature=0.3,  # Lower temperature for factual responses
                model=self.config.model_name
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error generating installation response: {str(e)}")
            return (
                "I'm sorry, I encountered an error while generating a response about door installation. "
                "Please try asking a more specific question about the installation process."
            )