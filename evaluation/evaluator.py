# door_installation_assistant/evaluation/evaluator.py
import logging
import json
import os
from typing import Dict, Any, List, Optional, Union
import time
from pathlib import Path
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

from deepeval.dataset import EvaluationDataset
from deepeval.test_case import LLMTestCase
from deepeval.run import evaluate_test_cases

from ..agent_system.agent_orchestrator import AgentOrchestrator
from ..retrieval.retrieval_pipeline import RetrievalPipeline
from .metrics import MetricsCalculator
from .synthetic_scenarios import ScenarioGenerator

logger = logging.getLogger(__name__)

class Evaluator:
    """Evaluates system performance."""
    
    def __init__(self, agent_orchestrator: Optional[AgentOrchestrator] = None, retrieval_pipeline: Optional[RetrievalPipeline] = None):
        """
        Initialize the evaluator.
        
        Args:
            agent_orchestrator: Agent orchestrator instance.
            retrieval_pipeline: Retrieval pipeline instance.
        """
        self.agent_orchestrator = agent_orchestrator or AgentOrchestrator()
        self.retrieval_pipeline = retrieval_pipeline or RetrievalPipeline()
        self.metrics_calculator = MetricsCalculator()
        self.scenario_generator = ScenarioGenerator()
    
    def evaluate_response(self, query: str, response: str, context: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Evaluate a single response.
        
        Args:
            query: User query.
            response: System response.
            context: Retrieved documents used as context.
            
        Returns:
            Dictionary with evaluation results.
        """
        try:
            # Calculate metrics
            metrics_result = self.metrics_calculator.calculate_metrics(
                query=query,
                response=response,
                context=context
            )
            
            # Add basic evaluation for door-specific criteria
            domain_evaluation = self._evaluate_domain_specific(query, response)
            
            # Combine results
            result = {
                "metrics": metrics_result,
                "domain_evaluation": domain_evaluation,
                "overall_score": (metrics_result["overall_score"] + domain_evaluation["overall_score"]) / 2
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error evaluating response: {str(e)}")
            return {
                "metrics": {},
                "domain_evaluation": {},
                "overall_score": 0.0,
                "error": str(e)
            }
    
    def _evaluate_domain_specific(self, query: str, response: str) -> Dict[str, Any]:
        """
        Evaluate domain-specific aspects of a response.
        
        Args:
            query: User query.
            response: System response.
            
        Returns:
            Dictionary with domain-specific evaluation results.
        """
        result = {
            "has_step_by_step": False,
            "has_safety_info": False,
            "has_measurements": False,
            "has_tool_info": False,
            "has_diagrams": False,
            "overall_score": 0.0
        }
        
        # Check for step-by-step instructions
        if any(pattern in response for pattern in ["Step 1", "Step 2", "1.", "2.", "First", "Next"]):
            result["has_step_by_step"] = True
        
        # Check for safety information
        safety_terms = ["safety", "precaution", "warning", "caution", "carefully", "protect"]
        if any(term in response.lower() for term in safety_terms):
            result["has_safety_info"] = True
        
        # Check for measurements
        if any(pattern in response for pattern in ["inch", "\"", "cm", "mm", "feet", "ft"]):
            result["has_measurements"] = True
        
        # Check for tool information
        tool_terms = ["tool", "hammer", "screwdriver", "drill", "level", "saw", "measure"]
        if any(term in response.lower() for term in tool_terms):
            result["has_tool_info"] = True
        
        # Calculate overall score
        score_components = [
            result["has_step_by_step"],
            result["has_safety_info"],
            result["has_measurements"],
            result["has_tool_info"]
        ]
        result["overall_score"] = sum(1.0 for component in score_components if component) / len(score_components)
        
        return result
    
    def evaluate_retrieval(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Evaluate retrieval performance.
        
        Args:
            query: User query.
            top_k: Number of documents to retrieve.
            
        Returns:
            Dictionary with retrieval evaluation results.
        """
        try:
            # Retrieve documents
            documents = self.retrieval_pipeline.retrieve(query, top_k=top_k)
            
            # Calculate basic retrieval metrics
            relevance_scores = []
            for i, doc in enumerate(documents):
                # For now, use a simple relevance estimation (better methods would be implemented in production)
                # Score diminishes with rank position
                relevance_scores.append(doc.get("score", 0) * (top_k - i) / top_k)
            
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
            
            # Use DeepEval's metrics for more sophisticated evaluation
            test_case = LLMTestCase(
                input=query,
                context=[doc.get("text", "") for doc in documents],
                actual_output="",  # No actual output for retrieval evaluation
                expected_output=""  # No expected output for retrieval evaluation
            )
            
            # Calculate RAG metrics
            metrics = [
                self.metrics_calculator.contextual_relevance_metric,
                self.metrics_calculator.contextual_precision_metric,
                self.metrics_calculator.contextual_recall_metric
            ]
            
            metrics_results = {}
            for metric in metrics:
                try:
                    metric.evaluate(test_case)
                    metrics_results[metric.name] = {
                        "score": metric.score,
                        "passed": metric.passed,
                        "reason": metric.reason
                    }
                except Exception as e:
                    logger.error(f"Error calculating metric {metric.name}: {str(e)}")
                    metrics_results[metric.name] = {
                        "score": 0.0,
                        "passed": False,
                        "reason": f"Error: {str(e)}"
                    }
            
            # Calculate average of metric scores
            metric_scores = [result["score"] for result in metrics_results.values()]
            avg_metric_score = sum(metric_scores) / len(metric_scores) if metric_scores else 0
            
            return {
                "documents": documents,
                "avg_relevance": avg_relevance,
                "metrics": metrics_results,
                "overall_score": avg_metric_score
            }
        
        except Exception as e:
            logger.error(f"Error evaluating retrieval: {str(e)}")
            return {
                "documents": [],
                "avg_relevance": 0.0,
                "metrics": {},
                "overall_score": 0.0,
                "error": str(e)
            }
    
    def evaluate_end_to_end(self, query: str, session_id: str = "eval") -> Dict[str, Any]:
        """
        Evaluate end-to-end system performance.
        
        Args:
            query: User query.
            session_id: Session ID for conversation context.
            
        Returns:
            Dictionary with end-to-end evaluation results.
        """
        try:
            # Process query through the agent orchestrator
            start_time = time.time()
            response = self.agent_orchestrator.process_query(query, session_id)
            end_time = time.time()
            
            # Calculate processing time
            processing_time = end_time - start_time
            
            # Get the response text
            response_text = response.get("response", "")
            
            # First evaluate retrieval - get relevant documents 
            # (we'll pass these to evaluate the generation)
            retrieval_evaluation = self.evaluate_retrieval(query)
            retrieved_docs = [doc.get("text", "") for doc in retrieval_evaluation.get("documents", [])]
            
            # Evaluate generation with retrieved docs as context
            generation_evaluation = self.metrics_calculator.calculate_metrics(
                query=query,
                response=response_text,
                context=retrieved_docs
            )
            
            # Calculate overall score combining retrieval and generation
            # Weight: 40% retrieval, 60% generation
            overall_score = (0.4 * retrieval_evaluation.get("overall_score", 0) + 
                             0.6 * generation_evaluation.get("overall_score", 0))
            
            return {
                "query": query,
                "response": response_text,
                "processing_time": processing_time,
                "retrieval_evaluation": retrieval_evaluation,
                "generation_evaluation": generation_evaluation,
                "overall_score": overall_score
            }
        
        except Exception as e:
            logger.error(f"Error evaluating end-to-end: {str(e)}")
            return {
                "query": query,
                "response": "",
                "processing_time": 0.0,
                "retrieval_evaluation": {},
                "generation_evaluation": {},
                "overall_score": 0.0,
                "error": str(e)
            }
    
    def batch_evaluate(self, queries: List[str], session_id: str = "eval_batch") -> Dict[str, Any]:
        """
        Evaluate a batch of queries.
        
        Args:
            queries: List of queries to evaluate.
            session_id: Session ID for conversation context.
            
        Returns:
            Dictionary with batch evaluation results.
        """
        try:
            results = []
            
            for query in queries:
                result = self.evaluate_end_to_end(query, session_id)
                results.append(result)
            
            # Calculate aggregate metrics
            overall_scores = [result["overall_score"] for result in results]
            avg_overall_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0
            
            processing_times = [result["processing_time"] for result in results]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
            
            return {
                "results": results,
                "avg_overall_score": avg_overall_score,
                "avg_processing_time": avg_processing_time,
                "count": len(results)
            }
        
        except Exception as e:
            logger.error(f"Error in batch evaluation: {str(e)}")
            return {
                "results": [],
                "avg_overall_score": 0.0,
                "avg_processing_time": 0.0,
                "count": 0,
                "error": str(e)
            }
    
    def evaluate_with_scenarios(self, scenarios_or_path: Union[List[Dict[str, Any]], str], output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate with synthetic scenarios.
        
        Args:
            scenarios_or_path: List of scenarios or path to scenarios file.
            output_path: Path to save evaluation results.
            
        Returns:
            Dictionary with evaluation results.
        """
        try:
            # Load scenarios if path provided
            if isinstance(scenarios_or_path, str):
                scenarios = self.scenario_generator.load_scenarios(scenarios_or_path)
            else:
                scenarios = scenarios_or_path
            
            # Create session ID for evaluation
            session_id = f"eval_scenarios_{int(time.time())}"
            
            # Evaluate each scenario
            results = []
            
            # Define a function to evaluate a single scenario
            def evaluate_scenario(scenario):
                query = scenario["query"]
                result = self.evaluate_end_to_end(query, session_id)
                
                # Check for expected keywords
                expected_keywords = scenario.get("expected_keywords", [])
                keyword_matches = sum(1 for keyword in expected_keywords if keyword.lower() in result["response"].lower())
                keyword_coverage = keyword_matches / len(expected_keywords) if expected_keywords else 0.0
                
                result["scenario"] = scenario
                result["keyword_coverage"] = keyword_coverage
                
                return result
            
            # Use ThreadPoolExecutor for parallel evaluation
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_scenario = {executor.submit(evaluate_scenario, scenario): scenario for scenario in scenarios}
                for future in as_completed(future_to_scenario):
                    results.append(future.result())
            
            # Calculate aggregate metrics
            overall_scores = [result["overall_score"] for result in results]
            avg_overall_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0
            
            keyword_coverages = [result["keyword_coverage"] for result in results]
            avg_keyword_coverage = sum(keyword_coverages) / len(keyword_coverages) if keyword_coverages else 0.0
            
            # Calculate scores by category and difficulty
            category_scores = {}
            difficulty_scores = {}
            
            for result in results:
                scenario = result["scenario"]
                category = scenario.get("category", "unknown")
                difficulty = scenario.get("difficulty", "unknown")
                
                if category not in category_scores:
                    category_scores[category] = []
                category_scores[category].append(result["overall_score"])
                
                if difficulty not in difficulty_scores:
                    difficulty_scores[difficulty] = []
                difficulty_scores[difficulty].append(result["overall_score"])
            
            # Calculate average scores by category and difficulty
            avg_category_scores = {
                category: sum(scores) / len(scores) if scores else 0.0
                for category, scores in category_scores.items()
            }
            
            avg_difficulty_scores = {
                difficulty: sum(scores) / len(scores) if scores else 0.0
                for difficulty, scores in difficulty_scores.items()
            }
            
            # Compile evaluation summary
            evaluation_summary = {
                "results": results,
                "avg_overall_score": avg_overall_score,
                "avg_keyword_coverage": avg_keyword_coverage,
                "avg_category_scores": avg_category_scores,
                "avg_difficulty_scores": avg_difficulty_scores,
                "count": len(results)
            }
            
            # Save results if output path provided
            if output_path:
                with open(output_path, 'w') as f:
                    json.dump(evaluation_summary, f, indent=2)
            
            return evaluation_summary
        
        except Exception as e:
            logger.error(f"Error evaluating with scenarios: {str(e)}")
            return {
                "results": [],
                "avg_overall_score": 0.0,
                "avg_keyword_coverage": 0.0,
                "avg_category_scores": {},
                "avg_difficulty_scores": {},
                "count": 0,
                "error": str(e)
            }
    
    def evaluate_with_deepeval(self, test_cases: List[LLMTestCase]) -> Dict[str, Any]:
        """
        Evaluate with DeepEval test cases.
        
        Args:
            test_cases: List of DeepEval test cases.
            
        Returns:
            Dictionary with evaluation results.
        """
        try:
            # Run evaluation with DeepEval
            evaluation_results = evaluate_test_cases(test_cases)
            
            # Compile results
            results = {
                "evaluation_results": evaluation_results,
                "metrics": {
                    metric.name: {
                        "average_score": metric.average_score,
                        "num_passed": metric.num_passed,
                        "num_failed": metric.num_failed,
                        "pass_rate": metric.pass_rate
                    }
                    for metric in evaluation_results.metrics
                },
                "overall_pass_rate": evaluation_results.overall_pass_rate,
                "count": len(test_cases)
            }
            
            return results
        
        except Exception as e:
            logger.error(f"Error evaluating with DeepEval: {str(e)}")
            return {
                "evaluation_results": None,
                "metrics": {},
                "overall_pass_rate": 0.0,
                "count": len(test_cases),
                "error": str(e)
            }
    
    def create_deepeval_test_cases(self, scenarios: List[Dict[str, Any]]) -> List[LLMTestCase]:
        """
        Create DeepEval test cases from scenarios.
        
        Args:
            scenarios: List of scenarios.
            
        Returns:
            List of DeepEval test cases.
        """
        test_cases = []
        
        for scenario in scenarios:
            query = scenario["query"]
            
            # Process query through the agent orchestrator
            session_id = f"test_{int(time.time())}_{len(test_cases)}"
            response = self.agent_orchestrator.process_query(query, session_id)
            response_text = response.get("response", "")
            
            # Create test case
            test_case = LLMTestCase(
                input=query,
                actual_output=response_text,
                context=[]  # Not needed for some metrics
            )
            
            test_cases.append(test_case)
        
        return test_cases
    
    def export_results_to_csv(self, results: Dict[str, Any], output_path: str) -> bool:
        """
        Export evaluation results to CSV.
        
        Args:
            results: Evaluation results.
            output_path: Path to save CSV file.
            
        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            # Extract individual results
            individual_results = results.get("results", [])
            
            # Create CSV file
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    "Query", "Response", "Overall Score", "Processing Time",
                    "Keyword Coverage", "Category", "Difficulty"
                ])
                
                # Write rows
                for result in individual_results:
                    writer.writerow([
                        result.get("query", ""),
                        result.get("response", ""),
                        result.get("overall_score", 0.0),
                        result.get("processing_time", 0.0),
                        result.get("keyword_coverage", 0.0),
                        result.get("scenario", {}).get("category", "unknown"),
                        result.get("scenario", {}).get("difficulty", "unknown")
                    ])
            
            logger.info(f"Exported {len(individual_results)} results to {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting results to CSV: {str(e)}")
            return False