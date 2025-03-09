# door_installation_assistant/agent_system/__init__.py
"""
Agent system package for Door Installation Assistant.

This package provides agent-based interaction capabilities for the Door Installation Assistant,
including specialized agents for different door-related tasks and agent orchestration.
"""

from .agent_factory import AgentFactory
from .agent_orchestrator import AgentOrchestrator
from .agents.base_agent import Agent
from .agents.door_identifier import DoorIdentifierAgent
from .agents.procedure_agent import ProcedureAgent
from .agents.tool_agent import ToolAgent
from .agents.troubleshoot_agent import TroubleshootAgent
from .agents.safety_agent import SafetyAgent
from .memory.conversation_memory import ConversationMemory

def get_agent_orchestrator(**kwargs):
    """
    Factory function to get an agent orchestrator instance.
    
    Args:
        **kwargs: Additional keyword arguments for the agent orchestrator.
        
    Returns:
        AgentOrchestrator instance.
    """
    return AgentOrchestrator(**kwargs)

__all__ = [
    'AgentFactory',
    'AgentOrchestrator',
    'Agent',
    'DoorIdentifierAgent',
    'ProcedureAgent',
    'ToolAgent',
    'TroubleshootAgent',
    'SafetyAgent',
    'ConversationMemory',
    'get_agent_orchestrator',
]