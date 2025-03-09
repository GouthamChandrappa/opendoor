# door_installation_assistant/api/__init__.py
"""
API package for Door Installation Assistant.

This package provides API endpoints for interacting with the Door Installation Assistant.
"""

from .main import app, start_api

__all__ = [
    'app',
    'start_api',
]