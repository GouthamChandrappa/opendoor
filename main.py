# door_installation_assistant/main.py
import os
import logging
import argparse
from typing import Dict, Any, List, Optional
import uuid
import json
from pathlib import Path

from config.app_config import get_config
from data_processing.document_processor import process_document
from vector_storage.qdrant_store import QdrantStore
from retrieval.retrieval_pipeline import RetrievalPipeline
from agent_system.agent_orchestrator import AgentOrchestrator
from evaluation.evaluator import Evaluator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("door_assistant.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DoorInstallationAssistant:
    """Main application class for Door Installation Assistant."""
    
    def __init__(self):
        self.config = get_config()
        self.vector_store = QdrantStore()
        self.retrieval_pipeline = RetrievalPipeline()
        self.agent_orchestrator = AgentOrchestrator()
        self.evaluator = Evaluator()
        
        # Initialize vector store
        self.vector_store.initialize()
    
    def ingest_documents(self, directory_path: str) -> Dict[str, Any]:
        """
        Ingest documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents.
            
        Returns:
            Dictionary with ingestion results.
        """
        try:
            logger.info(f"Ingesting documents from {directory_path}")
            
            # Create data directory if it doesn't exist
            data_dir = Path(self.config.data_dir)
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Get all PDF files in the directory
            pdf_files = []
            for root, _, files in os.walk(directory_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(root, file))
            
            logger.info(f"Found {len(pdf_files)} PDF files")
            
            # Process each document
            results = {
                "processed": 0,
                "failed": 0,
                "document_ids": []
            }
            
            for file_path in pdf_files:
                try:
                    # Process document
                    chunks = process_document(file_path)
                    logger.info(f"Processed {file_path} into {len(chunks)} chunks")
                    
                    # Add chunks to vector store
                    document_ids = self.vector_store.add_documents(chunks)
                    logger.info(f"Added {len(document_ids)} chunks to vector store")
                    
                    # Update results
                    results["processed"] += 1
                    results["document_ids"].extend(document_ids)
                
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {str(e)}")
                    results["failed"] += 1
            
            logger.info(f"Ingestion complete: {results['processed']} documents processed, {results['failed']} failed")
            return results
        
        except Exception as e:
            logger.error(f"Error ingesting documents: {str(e)}")
            return {
                "processed": 0,
                "failed": 0,
                "document_ids": [],
                "error": str(e)
            }
    
    def process_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user query.
        
        Args:
            query: User query.
            session_id: Session identifier. If None, a new session is created.
            
        Returns:
            Dictionary with response.
        """
        try:
            # Create session ID if not provided
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            # Process query with agent orchestrator
            response = self.agent_orchestrator.process_query(query, session_id)
            
            # Add session ID to response
            response["session_id"] = session_id
            
            # Evaluate response if needed
            if self.config.app_name.lower() == "debug":
                evaluation = self.evaluator.evaluate_response(query, response["response"])
                response["evaluation"] = evaluation
            
            return response
        
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "response": "I'm sorry, I encountered an error while processing your query. Please try again.",
                "session_id": session_id,
                "error": str(e)
            }
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            List of messages in the conversation history.
        """
        return self.agent_orchestrator.get_conversation_history(session_id)
    
    def clear_conversation_history(self, session_id: str) -> None:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session identifier.
        """
        self.agent_orchestrator.clear_conversation_history(session_id)
    
    def evaluate_system(self, test_queries: List[str]) -> Dict[str, Any]:
        """
        Evaluate the system using test queries.
        
        Args:
            test_queries: List of test queries.
            
        Returns:
            Dictionary with evaluation results.
        """
        try:
            # Create a new session for evaluation
            session_id = f"eval_{str(uuid.uuid4())}"
            
            # Process each test query
            results = []
            
            for query in test_queries:
                response = self.process_query(query, session_id)
                
                # Evaluate response
                evaluation = self.evaluator.evaluate_response(query, response["response"])
                
                results.append({
                    "query": query,
                    "response": response["response"],
                    "evaluation": evaluation
                })
            
            # Calculate overall metrics
            overall_metrics = self.evaluator.calculate_overall_metrics(results)
            
            return {
                "results": results,
                "overall_metrics": overall_metrics
            }
        
        except Exception as e:
            logger.error(f"Error evaluating system: {str(e)}")
            return {
                "results": [],
                "overall_metrics": {},
                "error": str(e)
            }
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents using the retrieval pipeline.
        
        Args:
            query: Search query.
            top_k: Number of results to return.
            
        Returns:
            List of retrieved documents.
        """
        try:
            # Perform search
            results = self.retrieval_pipeline.retrieve(query, top_k=top_k)
            return results
        
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Door Installation Assistant")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Ingest documents command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents")
    ingest_parser.add_argument("directory", help="Directory containing documents")
    
    # Process query command
    query_parser = subparsers.add_parser("query", help="Process a query")
    query_parser.add_argument("query", help="Query to process")
    query_parser.add_argument("--session", help="Session ID")
    
    # Search documents command
    search_parser = subparsers.add_parser("search", help="Search documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top_k", type=int, default=5, help="Number of results to return")
    
    # Evaluate system command
    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate system")
    evaluate_parser.add_argument("queries_file", help="File containing test queries (JSON list)")
    
    args = parser.parse_args()
    
    # Create assistant
    assistant = DoorInstallationAssistant()
    
    if args.command == "ingest":
        results = assistant.ingest_documents(args.directory)
        print(json.dumps(results, indent=2))
    
    elif args.command == "query":
        response = assistant.process_query(args.query, args.session)
        print(json.dumps(response, indent=2))
    
    elif args.command == "search":
        results = assistant.search_documents(args.query, args.top_k)
        print(json.dumps(results, indent=2))
    
    elif args.command == "evaluate":
        # Load test queries from file
        with open(args.queries_file, 'r') as f:
            test_queries = json.load(f)
        
        results = assistant.evaluate_system(test_queries)
        print(json.dumps(results, indent=2))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()