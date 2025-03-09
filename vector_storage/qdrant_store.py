# door_installation_assistant/vector_storage/qdrant_store.py
import logging
import uuid
from typing import List, Dict, Any, Optional, Union, Tuple
import os

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import (
        CollectionStatus, Distance, VectorParams, PointStruct, Filter, 
        FieldCondition, Range, MatchValue, MatchText
    )
except ImportError:
    logging.error("Qdrant client not installed. Please install it with 'pip install qdrant-client'.")
    raise

from .vector_store import VectorStore
from ..config.app_config import get_config
from ..data_processing.embedding_generator import EmbeddingGenerator

logger = logging.getLogger(__name__)

class QdrantStore(VectorStore):
    """Qdrant implementation of the vector store."""
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.collection_name = self.config.collection_name
        self.dimension = self.config.dimension
        self.embedding_generator = EmbeddingGenerator()
    
    def initialize(self):
        """Initialize the Qdrant client and ensure the collection exists."""
        try:
            # Initialize client based on configuration
            if self.config.url:
                self.client = QdrantClient(url=self.config.url, api_key=self.config.api_key)
            else:
                self.client = QdrantClient(host=self.config.host, port=self.config.port)
            
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection '{self.collection_name}'")
                self._create_collection()
            else:
                # Verify collection is ready
                collection_info = self.client.get_collection(self.collection_name)
                if collection_info.status != CollectionStatus.GREEN:
                    logger.warning(f"Collection '{self.collection_name}' is not ready (status: {collection_info.status})")
                else:
                    logger.info(f"Collection '{self.collection_name}' is ready")
            
            # Create payload indexes for efficient filtering
            self._create_payload_indexes()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {str(e)}")
            return False
    
    def _create_collection(self):
        """Create a new collection in Qdrant."""
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.dimension,
                    distance=models.Distance.COSINE
                ),
                optimizers_config=models.OptimizersConfigDiff(
                    indexing_threshold=10000  # Start indexing after this many vectors
                )
            )
            logger.info(f"Created collection '{self.collection_name}'")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            return False
    
    def _create_payload_indexes(self):
        """Create payload indexes for efficient filtering."""
        try:
            # Create payload indexes for common filtering fields
            payload_indexes = [
                ("door_category", "keyword"),
                ("door_type", "keyword"),
                ("content_type", "keyword"),
                ("step_number", "integer"),
                ("file_name", "keyword")
            ]
            
            for field_name, field_type in payload_indexes:
                try:
                    field_schema = models.PayloadSchemaType.KEYWORD if field_type == "keyword" else models.PayloadSchemaType.INTEGER
                    
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field_name,
                        field_schema=field_schema
                    )
                    logger.info(f"Created payload index for field '{field_name}' ({field_type})")
                
                except Exception as e:
                    # Index might already exist, which is fine
                    if "already exists" not in str(e).lower():
                        logger.warning(f"Failed to create payload index for field '{field_name}': {str(e)}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to create payload indexes: {str(e)}")
            return False
    
    def _convert_metadata_for_qdrant(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Convert metadata to a format suitable for Qdrant."""
        # Make a copy to avoid modifying the original
        metadata_copy = metadata.copy() if metadata else {}
        
        # Convert nested dictionaries to dot notation
        flattened_metadata = {}
        for key, value in metadata_copy.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flattened_metadata[f"{key}.{sub_key}"] = sub_value
            else:
                flattened_metadata[key] = value
        
        return flattened_metadata
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add documents to the vector store."""
        try:
            points = []
            document_ids = []
            
            for doc in documents:
                # Generate a unique ID for the document
                doc_id = str(uuid.uuid4())
                document_ids.append(doc_id)
                
                # Extract or generate embedding
                embedding = doc.get("embedding")
                if embedding is None:
                    text = doc.get("text", "")
                    if not text:
                        logger.warning(f"Document has no text content, skipping: {doc}")
                        continue
                    embedding = self.embedding_generator.generate_embedding(text)
                
                # Extract and process metadata
                metadata = self._convert_metadata_for_qdrant(doc.get("metadata", {}))
                
                # Create point
                point = PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload={
                        "text": doc.get("text", ""),
                        "type": doc.get("type", "unknown"),
                        **metadata
                    }
                )
                
                points.append(point)
            
            # Add points to collection in batches
            if points:
                batch_size = 100
                for i in range(0, len(points), batch_size):
                    batch_points = points[i:i+batch_size]
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=batch_points
                    )
                    logger.info(f"Added batch of {len(batch_points)} documents to collection")
            
            return document_ids
        
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            return []
    
    def _create_filter_from_dict(self, filter_dict: Dict[str, Any]) -> Optional[Filter]:
        """Create a Qdrant filter from a dictionary."""
        if not filter_dict:
            return None
        
        must_conditions = []
        
        for key, value in filter_dict.items():
            if isinstance(value, list):
                # Handle list values (match any of the values)
                should_conditions = []
                for item in value:
                    should_conditions.append(FieldCondition(
                        key=key,
                        match=MatchValue(value=item)
                    ))
                must_conditions.append(Filter(should=should_conditions))
            elif isinstance(value, dict):
                # Handle range queries
                range_conditions = {}
                if "gt" in value:
                    range_conditions["gt"] = value["gt"]
                if "gte" in value:
                    range_conditions["gte"] = value["gte"]
                if "lt" in value:
                    range_conditions["lt"] = value["lt"]
                if "lte" in value:
                    range_conditions["lte"] = value["lte"]
                
                if range_conditions:
                    must_conditions.append(FieldCondition(
                        key=key,
                        range=Range(**range_conditions)
                    ))
            else:
                # Handle exact match
                must_conditions.append(FieldCondition(
                    key=key,
                    match=MatchValue(value=value)
                ))
        
        if not must_conditions:
            return None
        
        return Filter(must=must_conditions)
    
    def search(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for documents in the vector store."""
        # By default, use vector search
        return self.similarity_search(
            embedding=query_embedding or self.embedding_generator.generate_embedding(query),
            filter_dict=filter_dict,
            top_k=top_k
        )
    
    def hybrid_search(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search (keyword + vector) in the vector store."""
        try:
            # Get query embedding if not provided
            if query_embedding is None:
                query_embedding = self.embedding_generator.generate_embedding(query)
            
            # Create filter
            search_filter = self._create_filter_from_dict(filter_dict)
            
            # Perform hybrid search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
                append_payload=True,
                search_params=models.SearchParams(
                    hnsw_ef=128,
                    exact=False
                ),
                score_threshold=0.0  # No minimum score threshold
            )
            
            # Process search results
            results = []
            for scored_point in search_result:
                # Extract payload
                payload = scored_point.payload or {}
                
                # Create result document
                result = {
                    "id": scored_point.id,
                    "text": payload.get("text", ""),
                    "metadata": {k: v for k, v in payload.items() if k != "text"},
                    "score": scored_point.score,
                    "vector_score": scored_point.score
                }
                
                results.append(result)
            
            # If alpha is not 0, perform text search and combine results
            if alpha < 1.0:
                keyword_results = self.keyword_search(query, filter_dict, top_k * 2)
                
                # Create a map of ID to document for efficient lookup
                vector_results_map = {doc["id"]: doc for doc in results}
                keyword_results_map = {doc["id"]: doc for doc in keyword_results}
                
                # Combine results
                combined_results = {}
                
                # Add all vector results with combined scores
                for doc_id, doc in vector_results_map.items():
                    if doc_id in keyword_results_map:
                        # Document exists in both result sets
                        keyword_score = keyword_results_map[doc_id]["score"]
                        vector_score = doc["score"]
                        
                        # Combine scores using weighted average
                        combined_score = (alpha * vector_score) + ((1 - alpha) * keyword_score)
                        
                        doc["score"] = combined_score
                        doc["keyword_score"] = keyword_score
                    
                    combined_results[doc_id] = doc
                
                # Add keyword results that aren't in vector results
                for doc_id, doc in keyword_results_map.items():
                    if doc_id not in combined_results:
                        # Adjust score based on alpha
                        doc["score"] = (1 - alpha) * doc["score"]
                        doc["vector_score"] = 0.0
                        combined_results[doc_id] = doc
                
                # Sort by combined score and limit to top_k
                results = sorted(combined_results.values(), key=lambda x: x["score"], reverse=True)[:top_k]
            
            return results
        
        except Exception as e:
            logger.error(f"Failed to perform hybrid search: {str(e)}")
            return []
    
    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from the vector store."""
        try:
            # Delete points in batches
            batch_size = 100
            for i in range(0, len(document_ids), batch_size):
                batch_ids = document_ids[i:i+batch_size]
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.PointIdsList(
                        points=batch_ids
                    )
                )
                logger.info(f"Deleted batch of {len(batch_ids)} documents from collection")
        
        except Exception as e:
            logger.error(f"Failed to delete documents: {str(e)}")
    
    def delete_collection(self) -> None:
        """Delete the entire collection."""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted collection '{self.collection_name}'")
        
        except Exception as e:
            logger.error(f"Failed to delete collection: {str(e)}")
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        try:
            # Get point by ID
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[document_id],
                with_payload=True,
                with_vectors=False
            )
            
            if not points:
                return None
            
            # Extract payload
            point = points[0]
            payload = point.payload or {}
            
            # Create document
            document = {
                "id": point.id,
                "text": payload.get("text", ""),
                "metadata": {k: v for k, v in payload.items() if k != "text"}
            }
            
            return document
        
        except Exception as e:
            logger.error(f"Failed to get document: {str(e)}")
            return None
    
    def update_document(self, document_id: str, document: Dict[str, Any]) -> None:
        """Update a document in the vector store."""
        try:
            # Extract or generate embedding
            embedding = document.get("embedding")
            if embedding is None:
                text = document.get("text", "")
                if not text:
                    logger.warning(f"Document has no text content, cannot update: {document}")
                    return
                embedding = self.embedding_generator.generate_embedding(text)
            
            # Extract and process metadata
            metadata = self._convert_metadata_for_qdrant(document.get("metadata", {}))
            
            # Create point
            point = PointStruct(
                id=document_id,
                vector=embedding,
                payload={
                    "text": document.get("text", ""),
                    "type": document.get("type", "unknown"),
                    **metadata
                }
            )
            
            # Update point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            logger.info(f"Updated document {document_id}")
        
        except Exception as e:
            logger.error(f"Failed to update document: {str(e)}")
    
    def count_documents(self) -> int:
        """Count the number of documents in the vector store."""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return collection_info.vectors_count
        
        except Exception as e:
            logger.error(f"Failed to count documents: {str(e)}")
            return 0
    
    def get_all_documents(self, batch_size: int = 100) -> List[Dict[str, Any]]:
        """Get all documents in the vector store."""
        try:
            documents = []
            offset = 0
            
            while True:
                # Scroll through points
                response = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                points = response[0]
                
                if not points:
                    break
                
                # Process points
                for point in points:
                    payload = point.payload or {}
                    
                    document = {
                        "id": point.id,
                        "text": payload.get("text", ""),
                        "metadata": {k: v for k, v in payload.items() if k != "text"}
                    }
                    
                    documents.append(document)
                
                # Update offset
                offset += len(points)
                
                if len(points) < batch_size:
                    break
            
            return documents
        
        except Exception as e:
            logger.error(f"Failed to get all documents: {str(e)}")
            return []
    
    def similarity_search(
        self,
        embedding: List[float],
        filter_dict: Optional[Dict[str, Any]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for documents by embedding similarity."""
        try:
            # Create filter
            search_filter = self._create_filter_from_dict(filter_dict)
            
            # Perform vector search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                query_filter=search_filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
                append_payload=True,
                search_params=models.SearchParams(
                    hnsw_ef=128,
                    exact=False
                ),
                score_threshold=0.0  # No minimum score threshold
            )
            
            # Process search results
            results = []
            for scored_point in search_result:
                # Extract payload
                payload = scored_point.payload or {}
                
                # Create result document
                result = {
                    "id": scored_point.id,
                    "text": payload.get("text", ""),
                    "metadata": {k: v for k, v in payload.items() if k != "text"},
                    "score": scored_point.score
                }
                
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {str(e)}")
            return []
    
    def keyword_search(
        self,
        query: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for documents by keyword."""
        try:
            # Create base filter from filter_dict
            base_filter = self._create_filter_from_dict(filter_dict)
            
            # Create text condition
            text_condition = FieldCondition(
                key="text",
                match=MatchText(text=query)
            )
            
            # Combine filters
            search_filter = None
            if base_filter:
                if base_filter.must:
                    search_filter = Filter(
                        must=[*base_filter.must, text_condition]
                    )
                else:
                    search_filter = Filter(
                        must=[text_condition]
                    )
            else:
                search_filter = Filter(
                    must=[text_condition]
                )
            
            # Perform keyword search
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=top_k,
                with_payload=True,
                with_vectors=False,
                filter=search_filter
            )[0]
            
            # Process search results
            results = []
            for point in search_result:
                # Extract payload
                payload = point.payload or {}
                
                # Simple relevance score (to be improved)
                text = payload.get("text", "")
                # Basic keyword matching score
                score = 0.0
                if text:
                    query_terms = query.lower().split()
                    text_lower = text.lower()
                    
                    # Count term occurrences
                    term_counts = [text_lower.count(term) for term in query_terms]
                    if any(term_counts):
                        # Normalize by text length
                        score = sum(term_counts) / len(text_lower)
                
                # Create result document
                result = {
                    "id": point.id,
                    "text": text,
                    "metadata": {k: v for k, v in payload.items() if k != "text"},
                    "score": score
                }
                
                results.append(result)
            
            # Sort by score
            results = sorted(results, key=lambda x: x["score"], reverse=True)
            
            return results
        
        except Exception as e:
            logger.error(f"Failed to perform keyword search: {str(e)}")
            return []