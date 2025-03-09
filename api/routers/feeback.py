# door_installation_assistant/api/routers/feedback.py
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uuid
import time

from ...evaluation.evaluator import Evaluator
from ...config.app_config import get_config
from ..middleware.auth import get_current_user

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/feedback",
    tags=["feedback"],
    responses={404: {"description": "Not found"}},
)

# Define request and response models
class FeedbackRequest(BaseModel):
    query: str = Field(..., description="Original query")
    response: str = Field(..., description="Assistant response")
    session_id: str = Field(..., description="Session ID")
    rating: int = Field(..., description="User rating (1-5)")
    feedback_text: Optional[str] = Field(None, description="Detailed feedback")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class FeedbackResponse(BaseModel):
    id: str = Field(..., description="Feedback ID")
    status: str = Field(..., description="Status")
    created_at: int = Field(..., description="Timestamp")

# Get dependencies
def get_evaluator():
    """Get evaluator instance."""
    return Evaluator()

def process_feedback_async(
    feedback_id: str,
    feedback: FeedbackRequest,
    evaluator: Evaluator
):
    """
    Process feedback asynchronously.
    
    Args:
        feedback_id: Feedback ID.
        feedback: Feedback data.
        evaluator: Evaluator instance.
    """
    try:
        # Log feedback
        logger.info(f"Processing feedback {feedback_id}: Rating {feedback.rating}")
        
        # Evaluate response (for comparison with user feedback)
        evaluation = evaluator.evaluate_response(
            query=feedback.query,
            response=feedback.response
        )
        
        # Store feedback and evaluation (this would be implemented in a real system)
        # For now, just log it
        logger.info(f"Feedback {feedback_id} processed. User rating: {feedback.rating}, System score: {evaluation.get('overall_score', 0)}")
        
        # In a real system, this might update a database or trigger further analysis
    
    except Exception as e:
        logger.error(f"Error processing feedback {feedback_id}: {str(e)}")

@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackRequest,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_current_user),
    evaluator: Evaluator = Depends(get_evaluator)
):
    """
    Submit user feedback for a response.
    
    Args:
        feedback: The feedback request.
        background_tasks: Background tasks.
        user: Current user.
        evaluator: Evaluator instance.
        
    Returns:
        Feedback response.
    """
    try:
        # Generate feedback ID
        feedback_id = str(uuid.uuid4())
        
        # Add to background tasks
        background_tasks.add_task(
            process_feedback_async,
            feedback_id,
            feedback,
            evaluator
        )
        
        return {
            "id": feedback_id,
            "status": "received",
            "created_at": int(time.time())
        }
    
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_feedback_stats(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get feedback statistics.
    
    Args:
        user: Current user.
        
    Returns:
        Feedback statistics.
    """
    try:
        # This is a placeholder - in a real system, this would query a database
        # For now, return mock statistics
        
        # Check if user is admin
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Only admins can access feedback statistics")
        
        return {
            "average_rating": 4.2,
            "total_feedback": 120,
            "rating_distribution": {
                "1": 5,
                "2": 8,
                "3": 15,
                "4": 42,
                "5": 50
            },
            "top_feedback_categories": [
                {"category": "Helpful installation steps", "count": 45},
                {"category": "Clear explanations", "count": 35},
                {"category": "Missing details", "count": 20},
                {"category": "Incorrect information", "count": 10},
                {"category": "Other", "count": 10}
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate")
async def manual_evaluation(
    feedback: FeedbackRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    evaluator: Evaluator = Depends(get_evaluator)
):
    """
    Perform manual evaluation of a response.
    
    Args:
        feedback: The feedback request with response to evaluate.
        user: Current user.
        evaluator: Evaluator instance.
        
    Returns:
        Evaluation results.
    """
    try:
        # Check if user is admin or evaluator
        if user.get("role") not in ["admin", "evaluator"]:
            raise HTTPException(status_code=403, detail="Only admins or evaluators can access this endpoint")
        
        # Evaluate response
        evaluation = evaluator.evaluate_response(
            query=feedback.query,
            response=feedback.response
        )
        
        # Return evaluation results
        return {
            "query": feedback.query,
            "response": feedback.response,
            "evaluation": evaluation,
            "evaluated_at": int(time.time())
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing manual evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))