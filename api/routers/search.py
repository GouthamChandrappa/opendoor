# door_installation_assistant/api/routers/search.py
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...retrieval.retrieval_pipeline import RetrievalPipeline
from ...config.app_config import get_config
from ..middleware.auth import get_current_user

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}},
)

# Define request and response models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    filter: Optional[Dict[str, Any]] = Field(None, description="Filter criteria")
    top_k: int = Field(10, description="Number of results to return")

class SearchResult(BaseModel):
    id: str = Field(..., description="Document ID")
    text: str = Field(..., description="Document text")
    score: float = Field(..., description="Relevance score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")

class SearchResponse(BaseModel):
    results: List[SearchResult] = Field(..., description="Search results")
    count: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original query")

# Get dependencies
def get_retrieval_pipeline():
    """Get retrieval pipeline instance."""
    return RetrievalPipeline()

@router.post("", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    retrieval_pipeline: RetrievalPipeline = Depends(get_retrieval_pipeline)
):
    """
    Search for documents.
    
    Args:
        request: The search request.
        user: Current user.
        retrieval_pipeline: Retrieval pipeline instance.
        
    Returns:
        Search results.
    """
    try:
        # Log search query
        logger.info(f"Search query: {request.query}")
        
        # Retrieve documents
        results = retrieval_pipeline.retrieve(
            query=request.query,
            filter_dict=request.filter,
            top_k=request.top_k
        )
        
        # Format results
        search_results = []
        for result in results:
            search_results.append({
                "id": result.get("id", ""),
                "text": result.get("text", ""),
                "score": result.get("score", 0.0),
                "metadata": result.get("metadata", {})
            })
        
        return {
            "results": search_results,
            "count": len(search_results),
            "query": request.query
        }
    
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=SearchResponse)
async def search_documents_get(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(10, description="Number of results to return"),
    door_category: Optional[str] = Query(None, description="Door category filter"),
    door_type: Optional[str] = Query(None, description="Door type filter"),
    content_type: Optional[str] = Query(None, description="Content type filter"),
    user: Dict[str, Any] = Depends(get_current_user),
    retrieval_pipeline: RetrievalPipeline = Depends(get_retrieval_pipeline)
):
    """
    Search for documents using GET parameters.
    
    Args:
        query: Search query.
        top_k: Number of results to return.
        door_category: Door category filter.
        door_type: Door type filter.
        content_type: Content type filter.
        user: Current user.
        retrieval_pipeline: Retrieval pipeline instance.
        
    Returns:
        Search results.
    """
    try:
        # Build filter
        filter_dict = {}
        if door_category:
            filter_dict["door_category"] = door_category
        if door_type:
            filter_dict["door_type"] = door_type
        if content_type:
            filter_dict["content_type"] = content_type
        
        # Log search query
        logger.info(f"GET Search query: {query} with filters: {filter_dict}")
        
        # Retrieve documents
        results = retrieval_pipeline.retrieve(
            query=query,
            filter_dict=filter_dict,
            top_k=top_k
        )
        
        # Format results
        search_results = []
        for result in results:
            search_results.append({
                "id": result.get("id", ""),
                "text": result.get("text", ""),
                "score": result.get("score", 0.0),
                "metadata": result.get("metadata", {})
            })
        
        return {
            "results": search_results,
            "count": len(search_results),
            "query": query
        }
    
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggest")
async def suggest_queries(
    query: str = Query(..., description="Partial query for suggestions"),
    max_suggestions: int = Query(5, description="Maximum number of suggestions"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get query suggestions based on partial input.
    
    Args:
        query: Partial query for suggestions.
        max_suggestions: Maximum number of suggestions.
        user: Current user.
        
    Returns:
        Query suggestions.
    """
    try:
        # This is a simple implementation that could be enhanced with proper query suggestion logic
        
        # Common door installation queries
        common_queries = [
            "How to install a prehung interior door",
            "Measuring for a bifold door installation",
            "Tools needed for door installation",
            "Fixing a door that won't close properly",
            "How to level a door frame",
            "Installing door hinges properly",
            "Shimming a door frame",
            "How to cut a door to fit",
            "Troubleshooting a sticky door",
            "Safety precautions for door installation"
        ]
        
        # Filter suggestions by partial query
        suggestions = [q for q in common_queries if query.lower() in q.lower()]
        
        # Limit suggestions
        suggestions = suggestions[:max_suggestions]
        
        return {"suggestions": suggestions, "query": query}
    
    except Exception as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))