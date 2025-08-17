"""
Initialization of routes package
"""

from .ai_routes import ai_bp
from .port_routes import port_bp
from .peak_detection import peak_detection_bp

__all__ = [
    'ai_bp',
    'port_bp',
    'peak_detection_bp'
]
