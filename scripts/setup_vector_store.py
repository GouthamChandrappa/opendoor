#!/usr/bin/env python
"""
Vector store setup script for Door Installation Assistant.

This script initializes and configures the vector store.
Usage: python setup_vector_store.py --provider qdrant --host localhost --port 6333
"""

import argparse
import logging
import sys
from typing import Dict, Any, Optional

from door_installation_assistant.config.app_config import get_config, AppConfig
from door_installation_assistant.vector_storage.qdrant_store import QdrantStore
from door_installation_assistant.utils.logging_utils import setup_logger

logger = setup_logger(name="vector_store_setup", log_file="logs/vector_store_setup.log")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Set up vector store for Door Installation Assistant")
    parser.add_argument(
        "--provider", 
        type=str, 
        default="qdrant", 
        choices=["qdrant", "pinecone", "weaviate"],
        help="Vector store provider"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        default="localhost", 
        help="Vector store host"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=6333, 
        help="Vector store port (for Qdrant)"
    )
    parser.add_argument(
        "--collection", 
        type=str, 
        default="door_installations", 
        help="Collection name"
    )
    parser.add_argument(
        "--dimension", 
        type=int, 
        default=1536, 
        help="Embedding dimension"
    )
    parser.add_argument(
        "--recreate", 
        action="store_true", 
        help="Recreate the collection if it exists"
    )
    parser.add_argument(
        "--url", 
        type=str, 
        help="URL for cloud-hosted vector stores"
    )
    parser.add_argument(
        "--api-key", 
        type=str, 
        help="API key for the vector store"
    )
    parser.add_argument(
        "--update-config", 
        action="store_true", 
        help="Update the app configuration with these settings"
    )
    return parser.parse_args()

def setup_qdrant(args) -> bool:
    """
    Set up Qdrant vector store.
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Update config with user arguments
        config = get_config()
        config.vector_store.provider = "qdrant"
        config.vector_store.host = args.host
        config.vector_store.port = args.port
        config.vector_store.collection_name = args.collection
        config.vector_store.dimension = args.dimension
        
        if args.url:
            config.vector_store.url = args.url
        
        if args.api_key:
            config.vector_store.api_key = args.api_key
        
        # Initialize vector store
        vector_store = QdrantStore()
        
        # If recreate flag is set, delete existing collection
        if args.recreate:
            logger.info(f"Recreating collection {args.collection}")
            try:
                vector_store.delete_collection()
            except Exception as e:
                logger.warning(f"Error deleting collection: {str(e)}")
        
        # Initialize Qdrant
        success = vector_store.initialize()
        
        if success:
            logger.info("Qdrant vector store initialized successfully")
            
            # Count existing vectors
            vector_count = vector_store.count_documents()
            logger.info(f"Collection contains {vector_count} vectors")
            
            return True
        else:
            logger.error("Failed to initialize Qdrant vector store")
            return False
            
    except Exception as e:
        logger.error(f"Error setting up Qdrant: {str(e)}")
        return False

def setup_vector_store(args) -> bool:
    """
    Set up the vector store based on the specified provider.
    
    Args:
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    if args.provider == "qdrant":
        return setup_qdrant(args)
    elif args.provider == "pinecone":
        logger.error("Pinecone provider not implemented yet")
        return False
    elif args.provider == "weaviate":
        logger.error("Weaviate provider not implemented yet")
        return False
    else:
        logger.error(f"Unknown vector store provider: {args.provider}")
        return False

def update_configuration(args, config: Optional[AppConfig] = None) -> bool:
    """
    Update the application configuration with vector store settings.
    
    Args:
        args: Command line arguments
        config: Optional app configuration to update
        
    Returns:
        True if successful, False otherwise
    """
    if config is None:
        config = get_config()
    
    try:
        # Create .env file with vector store configuration
        env_path = ".env"
        with open(env_path, "a") as f:
            f.write(f"\n# Vector store configuration updated on {get_timestamp()}\n")
            f.write(f"VECTOR_STORE_PROVIDER={args.provider}\n")
            
            if args.provider == "qdrant":
                f.write(f"VECTOR_STORE_HOST={args.host}\n")
                f.write(f"VECTOR_STORE_PORT={args.port}\n")
                
                if args.url:
                    f.write(f"VECTOR_STORE_URL={args.url}\n")
            
            f.write(f"VECTOR_STORE_COLLECTION_NAME={args.collection}\n")
            f.write(f"VECTOR_STORE_DIMENSION={args.dimension}\n")
            
            if args.api_key:
                f.write(f"VECTOR_STORE_API_KEY={args.api_key}\n")
        
        logger.info(f"Updated configuration in {env_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        return False

def get_timestamp() -> str:
    """Get current timestamp string."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    """Main entry point."""
    args = parse_arguments()
    
    logger.info(f"Setting up {args.provider} vector store")
    
    # Set up vector store
    success = setup_vector_store(args)
    
    if not success:
        logger.error("Vector store setup failed")
        sys.exit(1)
    
    # Update configuration if requested
    if args.update_config:
        logger.info("Updating application configuration")
        update_configuration(args)
    
    logger.info("Vector store setup complete")

if __name__ == "__main__":
    main()