# door_installation_assistant/api/middleware/__init__.py
"""
Middleware subpackage for API.

This package contains middleware for the Door Installation Assistant API.
"""

from .auth import AuthMiddleware, get_current_user

__all__ = [
    'AuthMiddleware',
    'get_current_user',
]