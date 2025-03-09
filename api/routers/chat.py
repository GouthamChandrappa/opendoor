# door_installation_assistant/api/routers/chat.py
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel, Field

from ...agent_system.agent_orchestrator import AgentOrchestrator
from ...config.app_config import get_config
from ..middleware.auth import get_current_user

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

# Define request and response models
class QueryRequest(BaseModel):
    query: str = Field(..., description="User query")
    session_id: Optional[str] = Field(None, description="Session ID")
    door_category: Optional[str] = Field(None, description="Door category (interior, exterior)")
    door_type: Optional[str] = Field(None, description="Door type (e.g., bifold, prehung)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class StreamResponse(BaseModel):
    id: str = Field(..., description="Message ID")
    type: str = Field(..., description="Message type (e.g., 'message', 'error')")
    content: str = Field(..., description="Message content")
    session_id: str = Field(..., description="Session ID")
    created_at: int = Field(..., description="Timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class QueryResponse(BaseModel):
    response: str = Field(..., description="Assistant response")
    session_id: str = Field(..., description="Session ID")
    agent: Optional[str] = Field(None, description="Agent that handled the query")
    door_category: Optional[str] = Field(None, description="Identified door category")
    door_type: Optional[str] = Field(None, description="Identified door type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class HistoryRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")

class HistoryResponse(BaseModel):
    session_id: str = Field(..., description="Session ID")
    messages: List[Dict[str, Any]] = Field(..., description="Conversation messages")

# Get dependencies
def get_agent_orchestrator():
    """Get agent orchestrator instance."""
    return AgentOrchestrator()

@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    user_agent: str = Header(None),
    user: Dict[str, Any] = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Process a user query.
    
    Args:
        request: The query request.
        user_agent: User agent header.
        user: Current user.
        agent_orchestrator: Agent orchestrator instance.
        
    Returns:
        Query response.
    """
    try:
        # Use provided session ID or generate a new one
        session_id = request.session_id or f"session_{user['id']}_{user_agent}"
        
        # Process query
        kwargs = {}
        if request.door_category:
            kwargs["door_category"] = request.door_category
        if request.door_type:
            kwargs["door_type"] = request.door_type
        if request.metadata:
            kwargs.update(request.metadata)
        
        # Log query
        logger.info(f"Processing query: {request.query} (session: {session_id})")
        
        # Process query through agent orchestrator
        response = agent_orchestrator.process_query(request.query, session_id, **kwargs)
        
        # Create response
        query_response = {
            "response": response.get("response", ""),
            "session_id": session_id,
            "agent": response.get("agent"),
            "door_category": response.get("door_category"),
            "door_type": response.get("door_type"),
            "metadata": {
                "processing_time_ms": response.get("processing_time_ms", 0),
                "document_count": response.get("document_count", 0)
            }
        }
        
        return query_response
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=HistoryResponse)
async def get_conversation_history(
    session_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session ID.
        user: Current user.
        agent_orchestrator: Agent orchestrator instance.
        
    Returns:
        Conversation history.
    """
    try:
        # Check if user has access to the session
        if not session_id.startswith(f"session_{user['id']}"):
            logger.warning(f"User {user['id']} attempted to access unauthorized session {session_id}")
            raise HTTPException(status_code=403, detail="You don't have access to this conversation")
        
        # Get conversation history
        history = agent_orchestrator.get_conversation_history(session_id)
        
        return {
            "session_id": session_id,
            "messages": history
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history")
async def clear_conversation_history(
    request: HistoryRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Clear conversation history for a session.
    
    Args:
        request: The history request.
        user: Current user.
        agent_orchestrator: Agent orchestrator instance.
        
    Returns:
        Success message.
    """
    try:
        # Check if user has access to the session
        if not request.session_id.startswith(f"session_{user['id']}"):
            logger.warning(f"User {user['id']} attempted to access unauthorized session {request.session_id}")
            raise HTTPException(status_code=403, detail="You don't have access to this conversation")
        
        # Clear conversation history
        agent_orchestrator.clear_conversation_history(request.session_id)
        
        return {"status": "success", "message": f"Cleared history for session {request.session_id}"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def stream_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    user_agent: str = Header(None),
    user: Dict[str, Any] = Depends(get_current_user),
    agent_orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    """
    Stream a user query response.
    
    Args:
        request: The query request.
        background_tasks: Background tasks.
        user_agent: User agent header.
        user: Current user.
        agent_orchestrator: Agent orchestrator instance.
        
    Returns:
        Streaming response.
    """
    try:
        # This is a placeholder for streaming implementation
        # In a real implementation, this would use Server-Sent Events (SSE) or WebSockets
        
        # Use provided session ID or generate a new one
        session_id = request.session_id or f"session_{user['id']}_{user_agent}"
        
        # Process query in the background (non-streaming for now)
        kwargs = {}
        if request.door_category:
            kwargs["door_category"] = request.door_category
        if request.door_type:
            kwargs["door_type"] = request.door_type
        
        # Process query through agent orchestrator
        response = agent_orchestrator.process_query(request.query, session_id, **kwargs)
        
        # Return non-streaming response for now
        return {
            "id": "msg_" + str(uuid.uuid4()),
            "type": "message",
            "content": response.get("response", ""),
            "session_id": session_id,
            "created_at": int(time.time()),
            "metadata": {
                "agent": response.get("agent"),
                "door_category": response.get("door_category"),
                "door_type": response.get("door_type")
            }
        }
    
    except Exception as e:
        logger.error(f"Error streaming query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))