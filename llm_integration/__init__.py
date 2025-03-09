# door_installation_assistant/llm_integration/__init__.py
"""
LLM integration package for Door Installation Assistant.

This package provides LLM integration capabilities for the Door Installation Assistant,
including LLM interaction, prompt templates, and response formatting.
"""

from .llm_manager import LLMManager
from .prompt_templates import PromptTemplate, PromptBuilder
from .response_formatter import ResponseFormatter

def get_llm_manager():
    """
    Factory function to get an LLM manager instance.
    
    Returns:
        LLMManager instance.
    """
    return LLMManager()

__all__ = [
    'LLMManager',
    'PromptTemplate',
    'PromptBuilder',
    'ResponseFormatter',
    'get_llm_manager',
]