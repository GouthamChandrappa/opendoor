#!/usr/bin/env python
"""
System evaluation script for Door Installation Assistant.

This script evaluates the system using test queries and scenarios.
Usage: python evaluate_system.py --test-file test_queries.json --output-file results.json
"""

import os
import argparse
import json
import logging
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import csv
from datetime import datetime

from door_installation_assistant.config.app_config import get_config
from door_installation_assistant.agent_system.agent_orchestrator import AgentOrchestrator
from door_installation_assistant.evaluation.evaluator import Evaluator
from door_installation_assistant.utils.logging_utils import setup_logger

logger = setup_logger(name="system_evaluation", log_file="logs/system_evaluation.log")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Evaluate Door Installation Assistant system")
    parser.add_argument(
        "--test-file", 
        type=str, 
        required=True, 
        help="JSON file containing test queries or scenarios"
    )
    parser.add_argument(
        "--output-file", 
        type=str, 
        default="evaluation_results.json", 
        help="Output file for evaluation results"
    )
    parser.add_argument(
        "--csv-output", 
        type=str, 
        help="Output CSV file for evaluation results"
    )
    parser.add_argument(
        "--llm-evaluation", 
        action="store_true", 
        help="Use LLM for evaluation"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Print verbose output"
    )
    parser.add_argument(
        "--retrieval-only", 
        action="store_true", 
        help="Evaluate only the retrieval component"
    )
    return parser.parse_args()

def load_test_queries(test_file: str) -> List[Dict[str, Any]]:
    """
    Load test queries from a JSON file.
    
    Args:
        test_file: Path to the JSON file containing test queries
        
    Returns:
        List of test query objects
    """
    try:
        with open(test_file, 'r') as f:
            data = json.load(f)
        
        # If the file contains a simple list of strings, convert to objects
        if isinstance(data, list):
            if all(isinstance(item, str) for item in data):
                return [{"query": item} for item in data]
            return data
            
        # If the file contains a dictionary with a "queries" key, use that
        if isinstance(data, dict) and "queries" in data:
            return data["queries"]
        
        # Otherwise, return the data as is
        return data
        
    except Exception as e:
        logger.error(f"Error loading test queries: {str(e)}")
        return []

def evaluate_system(
    test_queries: List[Dict[str, Any]], 
    use_llm: bool = False,
    retrieval_only: bool = False
) -> Dict[str, Any]:
    """
    Evaluate the system using test queries.
    
    Args:
        test_queries: List of test query objects
        use_llm: Whether to use LLM for evaluation
        retrieval_only: Whether to evaluate only the retrieval component
        
    Returns:
        Dictionary with evaluation results
    """
    # Initialize components
    orchestrator = AgentOrchestrator()
    evaluator = Evaluator()
    
    # Track results
    results = []
    metrics = {
        "total_queries": len(test_queries),
        "successful_queries": 0,
        "failed_queries": 0,
        "average_scores": {
            "relevance": 0.0,
            "helpfulness": 0.0,
            "procedures": 0.0,
            "safety": 0.0,
            "clarity": 0.0,
            "overall": 0.0
        },
        "average_response_time": 0.0,
        "total_time": 0.0
    }
    
    # Start timing
    start_time = time.time()
    
    # Evaluate each query
    for i, query_obj in enumerate(test_queries):
        query = query_obj["query"]
        expected_door_category = query_obj.get("expected_door_category")
        expected_door_type = query_obj.get("expected_door_type")
        
        logger.info(f"Evaluating query {i+1}/{len(test_queries)}: {query}")
        
        try:
            # Create a unique session ID for this query
            session_id = f"eval_{i}_{hash(query)}"
            
            # Process the query
            query_start_time = time.time()
            
            if retrieval_only:
                # Evaluate only the retrieval component
                from door_installation_assistant.retrieval.retrieval_pipeline import RetrievalPipeline
                retrieval_pipeline = RetrievalPipeline()
                retrieved_docs = retrieval_pipeline.retrieve(query=query, top_k=5)
                
                # Fake a response based on retrieved documents
                if retrieved_docs:
                    response = {
                        "response": "Retrieved documents successfully.",
                        "agent": "retrieval",
                        "documents": retrieved_docs
                    }
                else:
                    response = {
                        "response": "No relevant documents found.",
                        "agent": "retrieval",
                        "documents": []
                    }
            else:
                # Use the full system
                response = orchestrator.process_query(query, session_id)
            
            query_time = time.time() - query_start_time
            
            # Evaluate the response
            if use_llm:
                evaluation = evaluator.evaluate_with_llm(query, response["response"])
            else:
                evaluation = evaluator.evaluate_response(query, response["response"])
            
            # Store result
            result = {
                "query": query,
                "response": response["response"],
                "expected_door_category": expected_door_category,
                "expected_door_type": expected_door_type,
                "detected_door_category": response.get("door_category"),
                "detected_door_type": response.get("door_type"),
                "agent": response.get("agent"),
                "response_time": query_time,
                "evaluation": evaluation
            }
            
            # For retrieval-only evaluation, add retrieved documents
            if retrieval_only and "documents" in response:
                result["retrieved_documents"] = [
                    {
                        "text": doc.get("text", "")[:200] + "...",  # Truncate for readability
                        "score": doc.get("score", 0.0),
                        "metadata": doc.get("metadata", {})
                    }
                    for doc in response["documents"]
                ]
            
            results.append(result)
            
            # Update metrics
            metrics["successful_queries"] += 1
            for metric, score in evaluation.items():
                if metric in metrics["average_scores"]:
                    metrics["average_scores"][metric] += score
            
            metrics["average_response_time"] += query_time
            
        except Exception as e:
            logger.error(f"Error evaluating query {query}: {str(e)}")
            results.append({
                "query": query,
                "error": str(e),
                "expected_door_category": expected_door_category,
                "expected_door_type": expected_door_type
            })
            metrics["failed_queries"] += 1
    
    # Calculate final metrics
    metrics["total_time"] = time.time() - start_time
    
    if metrics["successful_queries"] > 0:
        metrics["average_response_time"] /= metrics["successful_queries"]
        for metric in metrics["average_scores"]:
            metrics["average_scores"][metric] /= metrics["successful_queries"]
    
    return {
        "results": results,
        "metrics": metrics,
        "timestamp": datetime.now().isoformat(),
        "config": {
            "use_llm": use_llm,
            "retrieval_only": retrieval_only
        }
    }

def save_results(results: Dict[str, Any], output_file: str, csv_output: Optional[str] = None):
    """
    Save evaluation results to a JSON file and optionally a CSV file.
    
    Args:
        results: Evaluation results
        output_file: Path to the output JSON file
        csv_output: Optional path to the output CSV file
    """
    # Save JSON results
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved evaluation results to {output_file}")
    except Exception as e:
        logger.error(f"Error saving results to {output_file}: {str(e)}")
    
    # Save CSV results
    if csv_output:
        try:
            with open(csv_output, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    "Query", "Response", "Expected Category", "Expected Type",
                    "Detected Category", "Detected Type", "Agent",
                    "Response Time", "Relevance", "Helpfulness", "Procedures",
                    "Safety", "Clarity", "Overall"
                ])
                
                # Write data
                for result in results["results"]:
                    if "error" in result:
                        writer.writerow([
                            result["query"], "ERROR", 
                            result.get("expected_door_category", "N/A"),
                            result.get("expected_door_type", "N/A"),
                            "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"
                        ])
                    else:
                        evaluation = result.get("evaluation", {})
                        writer.writerow([
                            result["query"], 
                            result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"],
                            result.get("expected_door_category", "N/A"),
                            result.get("expected_door_type", "N/A"),
                            result.get("detected_door_category", "N/A"),
                            result.get("detected_door_type", "N/A"),
                            result.get("agent", "N/A"),
                            f"{result.get('response_time', 0):.2f}",
                            f"{evaluation.get('relevance', 0):.2f}",
                            f"{evaluation.get('helpfulness', 0):.2f}",
                            f"{evaluation.get('procedures', 0):.2f}",
                            f"{evaluation.get('safety', 0):.2f}",
                            f"{evaluation.get('clarity', 0):.2f}",
                            f"{evaluation.get('overall', 0):.2f}"
                        ])
            
            logger.info(f"Saved CSV results to {csv_output}")
        except Exception as e:
            logger.error(f"Error saving CSV results to {csv_output}: {str(e)}")

def print_results_summary(results: Dict[str, Any], verbose: bool = False):
    """
    Print a summary of the evaluation results.
    
    Args:
        results: Evaluation results
        verbose: Whether to print verbose output
    """
    metrics = results["metrics"]
    
    print("\n" + "="*80)
    print(f"DOOR INSTALLATION ASSISTANT EVALUATION SUMMARY")
    print("="*80)
    print(f"Total queries: {metrics['total_queries']}")
    print(f"Successful queries: {metrics['successful_queries']}")
    print(f"Failed queries: {metrics['failed_queries']}")
    print(f"Average response time: {metrics['average_response_time']:.2f}s")
    print(f"Total evaluation time: {metrics['total_time']:.2f}s")
    print("\nAverage scores:")
    for metric, score in metrics["average_scores"].items():
        print(f"  {metric.capitalize()}: {score:.2f}")
    
    print("\nOverall score: {:.2f}".format(metrics["average_scores"]["overall"]))
    
    if verbose:
        print("\n" + "="*80)
        print("QUERY DETAILS")
        print("="*80)
        
        for i, result in enumerate(results["results"]):
            print(f"\nQuery {i+1}: {result['query']}")
            
            if "error" in result:
                print(f"  Error: {result['error']}")
                continue
            
            print(f"  Response time: {result.get('response_time', 0):.2f}s")
            print(f"  Expected door: {result.get('expected_door_category', 'N/A')} {result.get('expected_door_type', 'N/A')}")
            print(f"  Detected door: {result.get('detected_door_category', 'N/A')} {result.get('detected_door_type', 'N/A')}")
            print(f"  Processing agent: {result.get('agent', 'N/A')}")
            
            print("  Scores:")
            for metric, score in result["evaluation"].items():
                if isinstance(score, (int, float)):
                    print(f"    {metric.capitalize()}: {score:.2f}")
            
            print(f"\n  Response: {result['response'][:200]}...")

def main():
    """Main entry point."""
    args = parse_arguments()
    
    logger.info(f"Starting system evaluation with test file: {args.test_file}")
    
    # Load test queries
    test_queries = load_test_queries(args.test_file)
    
    if not test_queries:
        logger.error("No test queries found")
        return
    
    logger.info(f"Loaded {len(test_queries)} test queries")
    
    # Evaluate system
    results = evaluate_system(
        test_queries, 
        use_llm=args.llm_evaluation,
        retrieval_only=args.retrieval_only
    )
    
    # Save results
    save_results(results, args.output_file, args.csv_output)
    
    # Print results summary
    print_results_summary(results, args.verbose)

if __name__ == "__main__":
    main()