# door_installation_assistant/evaluation/__init__.py
"""
Evaluation package for Door Installation Assistant.

This package provides evaluation capabilities for the Door Installation Assistant,
including metrics, test case generation, and evaluation orchestration.
"""

from .evaluator import Evaluator
from .metrics import MetricsCalculator
from .synthetic_scenarios import ScenarioGenerator

def get_evaluator(**kwargs):
    """
    Factory function to get an evaluator instance.
    
    Args:
        **kwargs: Additional keyword arguments for the evaluator.
        
    Returns:
        Evaluator instance.
    """
    return Evaluator(**kwargs)

__all__ = [
    'Evaluator',
    'MetricsCalculator',
    'ScenarioGenerator',
    'get_evaluator',
]