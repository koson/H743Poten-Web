"""
Initialization of routes package
"""

from .ai_routes import ai_bp
from .port_routes import port_bp

__all__ = [
    'ai_bp',
    'port_bp'
]
