# door_installation_assistant/api/main.py
import logging
import os
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from ..config.app_config import get_config
from ..config.logging_config import setup_logging
from .routers import chat_router, search_router, feedback_router
from .middleware.auth import get_current_user

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Door Installation Assistant API",
    description="API for Door Installation Assistant",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(search_router)
app.include_router(feedback_router)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request information."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Processing time: {process_time:.3f}s"
    )
    
    return response

# Error handling middleware
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"}
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Door Installation Assistant API",
        "version": "1.0.0",
        "status": "active"
    }

# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": time.time()}

# Version endpoint
@app.get("/version")
async def version():
    """Version endpoint."""
    return {
        "api_version": "1.0.0",
        "system_version": "1.0.0",
        "build_date": "2023-09-01"
    }

# Door types endpoint
@app.get("/door-types")
async def door_types(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get available door types."""
    return {
        "categories": {
            "interior": ["bifold", "prehung"],
            "exterior": ["entry door", "patio door", "dentil shelf"]
        }
    }

def start_api():
    """Start the API server."""
    config = get_config()
    
    # Get host and port from config or environment variables
    host = os.environ.get("API_HOST", config.api_host)
    port = int(os.environ.get("API_PORT", config.api_port))
    
    # Start server
    uvicorn.run(
        "door_installation_assistant.api.main:app",
        host=host,
        port=port,
        reload=config.debug
    )

if __name__ == "__main__":
    start_api()