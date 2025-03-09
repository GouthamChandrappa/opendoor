# door_installation_assistant/api/middleware/auth.py
import logging
from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
import time
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from ...config.app_config import get_config

logger = logging.getLogger(__name__)

# API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# JWT authentication
JWT_SECRET = "your-secret-key"  # In production, this should be securely stored
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthMiddleware:
    """Authentication middleware."""
    
    def __init__(self):
        self.config = get_config()
    
    def verify_api_key(self, api_key: str) -> bool:
        """
        Verify API key.
        
        Args:
            api_key: API key to verify.
            
        Returns:
            True if valid, False otherwise.
        """
        # In a real system, this would validate against a database
        # For development, use a simple check
        valid_keys = ["dev-key-1", "dev-key-2", "test-key"]
        return api_key in valid_keys
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT access token.
        
        Args:
            data: Token data.
            
        Returns:
            JWT token.
        """
        to_encode = data.copy()
        expire = time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token.
        
        Args:
            token: JWT token to verify.
            
        Returns:
            Token payload if valid.
            
        Raises:
            HTTPException: If token is invalid.
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
            return payload
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Authentication dependency
async def get_current_user(
    api_key: Optional[str] = Security(API_KEY_HEADER)
) -> Dict[str, Any]:
    """
    Get current user from API key.
    
    Args:
        api_key: API key from header.
        
    Returns:
        User information.
        
    Raises:
        HTTPException: If authentication fails.
    """
    # For development and demo purposes
    # In production, use a more robust authentication system
    
    # Check authentication
    if api_key is None:
        # For testing, allow unauthorized access with limited permissions
        return {
            "id": "anonymous",
            "role": "guest",
            "permissions": ["read"]
        }
    
    # Verify API key
    auth = AuthMiddleware()
    if not auth.verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # Return user information
    # In a real system, this would retrieve user details from a database
    return {
        "id": "api_user_1",
        "role": "user",
        "permissions": ["read", "write"]
    }