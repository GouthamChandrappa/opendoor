# door_installation_assistant/agent_system/agents/__init__.py
"""
Agents subpackage for Door Installation Assistant.

This package contains specialized agents for different door-related tasks,
such as door identification, installation procedures, tool recommendations, etc.
"""

from .base_agent import Agent
from .door_identifier import DoorIdentifierAgent
from .procedure_agent import ProcedureAgent
from .tool_agent import ToolAgent
from .troubleshoot_agent import TroubleshootAgent
from .safety_agent import SafetyAgent

# Dictionary mapping agent types to agent classes
AGENT_CLASSES = {
    "door_identifier": DoorIdentifierAgent,
    "procedure": ProcedureAgent,
    "tool": ToolAgent,
    "troubleshooting": TroubleshootAgent,
    "safety": SafetyAgent
}

def get_agent_class(agent_type: str):
    """
    Get the agent class for a specific agent type.
    
    Args:
        agent_type: Type of agent to get.
        
    Returns:
        Agent class.
        
    Raises:
        ValueError: If the agent type is unknown.
    """
    if agent_type not in AGENT_CLASSES:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    return AGENT_CLASSES[agent_type]

__all__ = [
    'Agent',
    'DoorIdentifierAgent',
    'ProcedureAgent',
    'ToolAgent',
    'TroubleshootAgent',
    'SafetyAgent',
    'AGENT_CLASSES',
    'get_agent_class',
]