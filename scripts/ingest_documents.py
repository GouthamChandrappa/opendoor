#!/usr/bin/env python
"""
Document ingestion script for Door Installation Assistant.

This script processes PDF documents and adds them to the vector store.
Usage: python ingest_documents.py --input-dir /path/to/documents --recursive
"""

import os
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
import time
from tqdm import tqdm

from door_installation_assistant.config.app_config import get_config
from door_installation_assistant.data_processing.document_processor import process_document
from door_installation_assistant.vector_storage.qdrant_store import QdrantStore
from door_installation_assistant.utils.file_utils import list_files_by_extension, get_file_size_human_readable
from door_installation_assistant.utils.logging_utils import setup_logger

logger = setup_logger(name="document_ingestion", log_file="logs/document_ingestion.log")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Ingest documents into the vector store")
    parser.add_argument(
        "--input-dir", 
        type=str, 
        required=True, 
        help="Directory containing documents to ingest"
    )
    parser.add_argument(
        "--recursive", 
        action="store_true", 
        help="Recursively search for documents in subdirectories"
    )
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=10, 
        help="Number of documents to process in a batch"
    )
    parser.add_argument(
        "--skip-existing", 
        action="store_true", 
        help="Skip documents that have already been ingested"
    )
    parser.add_argument(
        "--file-type", 
        type=str, 
        default="pdf", 
        help="File type to ingest (default: pdf)"
    )
    parser.add_argument(
        "--clear-existing", 
        action="store_true", 
        help="Clear existing vector store before ingestion"
    )
    return parser.parse_args()

def find_documents(input_dir: str, file_type: str, recursive: bool) -> List[Path]:
    """
    Find all documents of the specified type in the input directory.
    
    Args:
        input_dir: Directory to search for documents
        file_type: File type to search for (e.g., 'pdf')
        recursive: Whether to search recursively in subdirectories
        
    Returns:
        List of file paths
    """
    input_path = Path(input_dir)
    
    if not input_path.exists() or not input_path.is_dir():
        logger.error(f"Input directory {input_dir} does not exist or is not a directory")
        return []
    
    if recursive:
        # Use Path.glob with recursive pattern
        return [f for f in input_path.glob(f"**/*.{file_type}") if f.is_file()]
    else:
        # Use list_files_by_extension utility
        return list_files_by_extension(input_dir, file_type)

def process_documents(file_paths: List[Path], batch_size: int, skip_existing: bool) -> Dict[str, Any]:
    """
    Process documents and add them to the vector store.
    
    Args:
        file_paths: List of document file paths
        batch_size: Number of documents to process in a batch
        skip_existing: Whether to skip documents that have already been ingested
        
    Returns:
        Dictionary with processing results
    """
    # Initialize vector store
    vector_store = QdrantStore()
    vector_store.initialize()
    
    # Track results
    results = {
        "processed": 0,
        "failed": 0,
        "skipped": 0,
        "chunks_added": 0,
        "document_ids": []
    }
    
    # Get list of existing document IDs if skipping existing
    existing_docs = set()
    if skip_existing:
        try:
            # This assumes you have document metadata in the vector store
            # You may need to adjust this based on your implementation
            all_docs = vector_store.get_all_documents(batch_size=1000)
            for doc in all_docs:
                if "file_path" in doc.get("metadata", {}):
                    existing_docs.add(doc["metadata"]["file_path"])
            
            logger.info(f"Found {len(existing_docs)} existing documents in vector store")
        except Exception as e:
            logger.warning(f"Error getting existing documents: {str(e)}")
    
    # Process documents in batches
    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i+batch_size]
        
        for file_path in tqdm(batch, desc=f"Processing batch {i//batch_size + 1}/{(len(file_paths) + batch_size - 1)//batch_size}"):
            try:
                # Check if document already exists
                if skip_existing and str(file_path) in existing_docs:
                    logger.info(f"Skipping existing document: {file_path}")
                    results["skipped"] += 1
                    continue
                
                # Get file size for logging
                file_size = get_file_size_human_readable(file_path)
                logger.info(f"Processing document: {file_path} ({file_size})")
                
                # Process document into chunks
                start_time = time.time()
                chunks = process_document(file_path)
                processing_time = time.time() - start_time
                logger.info(f"Processed {file_path} into {len(chunks)} chunks in {processing_time:.2f} seconds")
                
                # Add chunks to vector store
                start_time = time.time()
                document_ids = vector_store.add_documents(chunks)
                indexing_time = time.time() - start_time
                logger.info(f"Added {len(document_ids)} chunks to vector store in {indexing_time:.2f} seconds")
                
                # Update results
                results["processed"] += 1
                results["chunks_added"] += len(document_ids)
                results["document_ids"].extend(document_ids)
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                results["failed"] += 1
    
    return results

def main():
    """Main entry point."""
    args = parse_arguments()
    
    logger.info(f"Starting document ingestion from {args.input_dir}")
    start_time = time.time()
    
    # Clear existing vector store if requested
    if args.clear_existing:
        logger.info("Clearing existing vector store")
        vector_store = QdrantStore()
        vector_store.initialize()
        vector_store.delete_collection()
        vector_store.initialize()
        logger.info("Vector store cleared")
    
    # Find documents to process
    file_paths = find_documents(args.input_dir, args.file_type, args.recursive)
    logger.info(f"Found {len(file_paths)} {args.file_type} files to process")
    
    if not file_paths:
        logger.warning(f"No {args.file_type} files found in {args.input_dir}")
        return
    
    # Process documents
    results = process_documents(file_paths, args.batch_size, args.skip_existing)
    
    # Log results
    total_time = time.time() - start_time
    logger.info(f"Document ingestion complete in {total_time:.2f} seconds")
    logger.info(f"Processed: {results['processed']}")
    logger.info(f"Failed: {results['failed']}")
    logger.info(f"Skipped: {results['skipped']}")
    logger.info(f"Total chunks added: {results['chunks_added']}")

if __name__ == "__main__":
    main()