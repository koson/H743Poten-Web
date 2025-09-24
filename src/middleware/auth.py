"""
Authentication and authorization decorators and utilities
"""

from functools import wraps
from flask import request, jsonify, session, current_app, g
import logging

logger = logging.getLogger(__name__)

def get_current_user():
    """Get current user from session"""
    user_service = getattr(current_app.config, 'user_service', None)
    if not user_service:
        return None
    
    # Check for session ID in cookie or header
    session_id = request.cookies.get('session_id') or request.headers.get('X-Session-ID')
    if not session_id:
        return None
    
    # Validate session
    session_data = user_service.validate_session(session_id)
    if not session_data:
        return None
    
    return session_data.get('username')

def get_user_from_request():
    """Get user from current request context"""
    return getattr(g, 'current_user', None)

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = get_current_user()
        if not username:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'error_code': 401
            }), 401
        
        # Store user in request context
        g.current_user = username
        return f(*args, **kwargs)
    
    return decorated_function

def permission_required(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            username = get_current_user()
            if not username:
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'error_code': 401
                }), 401
            
            user_service = getattr(current_app.config, 'user_service', None)
            if not user_service:
                return jsonify({
                    'success': False,
                    'error': 'User service not available',
                    'error_code': 500
                }), 500
            
            if not user_service.has_permission(username, permission):
                return jsonify({
                    'success': False,
                    'error': f'Permission "{permission}" required',
                    'error_code': 403
                }), 403
            
            # Store user in request context
            g.current_user = username
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def feature_required(feature_name):
    """Decorator to require specific feature access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            username = get_current_user()
            if not username:
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'error_code': 401
                }), 401
            
            feature_service = getattr(current_app.config, 'feature_service', None)
            if not feature_service:
                # If no feature service, allow access (fallback)
                g.current_user = username
                return f(*args, **kwargs)
            
            if not feature_service.is_feature_enabled_for_user(username, feature_name):
                return jsonify({
                    'success': False,
                    'error': f'Feature "{feature_name}" not available',
                    'error_code': 403
                }), 403
            
            # Store user in request context
            g.current_user = username
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def route_access_required(f):
    """Decorator to check route access permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = get_current_user()
        if not username:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'error_code': 401
            }), 401
        
        feature_service = getattr(current_app.config, 'feature_service', None)
        if not feature_service:
            # If no feature service, allow access (fallback)
            g.current_user = username
            return f(*args, **kwargs)
        
        current_route = request.path
        if not feature_service.can_access_route(username, current_route):
            return jsonify({
                'success': False,
                'error': f'Access denied to route "{current_route}"',
                'error_code': 403
            }), 403
        
        # Store user in request context
        g.current_user = username
        return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    """Decorator to require admin permission"""
    return permission_required('admin')(f)

def optional_auth(f):
    """Decorator for optional authentication (sets user if available)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = get_current_user()
        g.current_user = username  # May be None
        return f(*args, **kwargs)
    
    return decorated_function

class AuthMiddleware:
    """Middleware for handling authentication and authorization"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Process request before route handler"""
        # Skip auth for static files and public endpoints
        if request.endpoint in ['static', 'favicon']:
            return
        
        # Public endpoints that don't require authentication
        public_endpoints = [
            'auth.login',
            'auth.logout', 
            'auth.check_session',
            'index'  # Landing page
        ]
        
        if request.endpoint in public_endpoints:
            return
        
        # Set current user in request context
        username = get_current_user()
        g.current_user = username
        
        # Check if route requires authentication
        if request.path.startswith('/api/') and username is None:
            # API endpoints generally require authentication
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'error_code': 401
            }), 401
    
    def after_request(self, response):
        """Process response after route handler"""
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # CORS headers for API endpoints
        if request.path.startswith('/api/'):
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Session-ID'
        
        return response