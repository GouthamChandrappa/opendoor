# door_installation_assistant/agent_system/agent_factory.py
import logging
from typing import Dict, Any, List, Optional, Type

from ..config.app_config import get_config
from .agents.base_agent import Agent
from .agents.door_identifier import DoorIdentifierAgent
from .agents.procedure_agent import ProcedureAgent
from .agents.tool_agent import ToolAgent
from .agents.troubleshoot_agent import TroubleshootAgent
from .agents.safety_agent import SafetyAgent

logger = logging.getLogger(__name__)

class AgentFactory:
    """Factory for creating agents."""
    
    def __init__(self):
        self.config = get_config().agent
        self._agent_classes = self._register_agent_classes()
    
    def _register_agent_classes(self) -> Dict[str, Type[Agent]]:
        """Register agent classes."""
        return {
            "door_identifier": DoorIdentifierAgent,
            "procedure": ProcedureAgent,
            "tool": ToolAgent,
            "troubleshooting": TroubleshootAgent,
            "safety": SafetyAgent
        }
    
    def create_agent(self, agent_type: str, **kwargs) -> Optional[Agent]:
        """
        Create an agent of the specified type.
        
        Args:
            agent_type: Type of agent to create.
            **kwargs: Additional arguments to pass to the agent constructor.
            
        Returns:
            Instance of the specified agent type, or None if the type is invalid.
        """
        try:
            if agent_type not in self._agent_classes:
                logger.warning(f"Unknown agent type: {agent_type}")
                return None
            
            agent_class = self._agent_classes[agent_type]
            agent = agent_class(**kwargs)
            logger.info(f"Created agent of type {agent_type}")
            return agent
        
        except Exception as e:
            logger.error(f"Error creating agent of type {agent_type}: {str(e)}")
            return None
    
    def create_agents(self, agent_types: Optional[List[str]] = None, **kwargs) -> Dict[str, Agent]:
        """
        Create multiple agents.
        
        Args:
            agent_types: List of agent types to create. If None, uses the configured types.
            **kwargs: Additional arguments to pass to the agent constructors.
            
        Returns:
            Dictionary mapping agent types to agent instances.
        """
        if agent_types is None:
            agent_types = self.config.agent_types
        
        agents = {}
        
        for agent_type in agent_types:
            agent = self.create_agent(agent_type, **kwargs)
            if agent:
                agents[agent_type] = agent
        
        return agents