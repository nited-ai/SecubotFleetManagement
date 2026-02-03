"""
Routes package for Unitree WebRTC Connect.

This package contains all Flask routes organized by functionality:
- views.py: HTML view routes
- api.py: HTTP API routes
- ws.py: WebSocket handlers
"""

from .views import views_bp
from .api import api_bp
from .ws import register_websocket_handlers

__all__ = ['views_bp', 'api_bp', 'register_websocket_handlers']

