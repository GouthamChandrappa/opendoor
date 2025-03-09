# door_installation_assistant/evaluation/metrics.py
import logging
from typing import Dict, Any, List, Optional, Union
import numpy as np

from deepeval.metrics import (
    ContextualRelevanceMetric, 
    ContextualPrecisionMetric, 
    ContextualRecallMetric,
    RelevanceMetric,
    FaithfulnessMetric
)
from deepeval.metrics.base_metric import BaseMetric
from deepeval.test_case import LLMTestCase

logger = logging.getLogger(__name__)

class MetricsCalculator:
    """Calculates evaluation metrics using DeepEval."""
    
    def __init__(self):
        self._setup_metrics()
    
    def _setup_metrics(self):
        """Set up evaluation metrics."""
        try:
            # Core RAG metrics
            self.contextual_relevance_metric = ContextualRelevanceMetric(threshold=0.7)
            self.contextual_precision_metric = ContextualPrecisionMetric(threshold=0.7)
            self.contextual_recall_metric = ContextualRecallMetric(threshold=0.7)
            self.relevance_metric = RelevanceMetric(threshold=0.7)
            self.faithfulness_metric = FaithfulnessMetric(threshold=0.7)
            
            # Group metrics
            self.all_metrics = [
                self.contextual_relevance_metric,
                self.contextual_precision_metric,
                self.contextual_recall_metric,
                self.relevance_metric,
                self.faithfulness_metric
            ]
            
        except Exception as e:
            logger.error(f"Error setting up metrics: {str(e)}")
    
    def calculate_metrics(
        self, 
        query: str, 
        response: str, 
        context: List[str] = None,
        expected_output: str = None
    ) -> Dict[str, Any]:
        """
        Calculate evaluation metrics for a response.
        
        Args:
            query: User query.
            response: System response.
            context: Retrieved documents used as context.
            expected_output: Expected/reference response if available.
            
        Returns:
            Dictionary with metric results.
        """
        try:
            # Create DeepEval test case
            test_case = LLMTestCase(
                input=query,
                actual_output=response,
                expected_output=expected_output if expected_output else "",
                context=context if context else []
            )
            
            # Run metrics
            results = {}
            for metric in self.all_metrics:
                try:
                    metric.evaluate(test_case)
                    results[metric.name] = {
                        "score": metric.score,
                        "passed": metric.passed,
                        "reason": metric.reason
                    }
                except Exception as e:
                    logger.error(f"Error calculating metric {metric.name}: {str(e)}")
                    results[metric.name] = {
                        "score": 0.0,
                        "passed": False,
                        "reason": f"Error: {str(e)}"
                    }
            
            # Calculate overall score as average of all metrics
            scores = [result.get("score", 0) for result in results.values()]
            overall_score = sum(scores) / len(scores) if scores else 0.0
            
            return {
                "metrics": results,
                "overall_score": overall_score
            }
        
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {
                "metrics": {},
                "overall_score": 0.0,
                "error": str(e)
            }