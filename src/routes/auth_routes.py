"""
Authentication routes for user management
"""

from flask import Blueprint, request, jsonify, make_response, render_template
from datetime import datetime, timedelta
import logging

from ..middleware.auth import login_required, admin_required, get_current_user
from ..services.user_service import user_service
from ..services.feature_service import feature_service

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Authentication routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication"""
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400
        
        # Authenticate user
        session_data = user_service.authenticate(username, password)
        
        if not session_data:
            logger.warning(f"Failed login attempt for user: {username}")
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401
        
        # Get user features
        user_features = None
        if feature_service:
            user_features = feature_service.get_user_features(username)
        
        # Create response with session cookie
        response = make_response(jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'username': username,
                'session_id': session_data['session_id']
            },
            'features': user_features
        }))
        
        # Set secure session cookie
        response.set_cookie(
            'session_id',
            session_data['session_id'],
            max_age=24*60*60,  # 24 hours
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='Lax'
        )
        
        logger.info(f"User {username} logged in successfully")
        return response
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Login failed due to server error'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        session_id = request.cookies.get('session_id') or request.headers.get('X-Session-ID')
        
        if session_id:
            user_service.logout(session_id)
        
        response = make_response(jsonify({
            'success': True,
            'message': 'Logout successful'
        }))
        
        # Clear session cookie
        response.set_cookie(
            'session_id',
            '',
            expires=0,
            httponly=True,
            secure=False,
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({
            'success': False,
            'error': 'Logout failed'
        }), 500

@auth_bp.route('/check-session', methods=['GET'])
def check_session():
    """Check session validity and return user info"""
    try:
        username = get_current_user()
        
        if not username:
            return jsonify({
                'success': False,
                'authenticated': False
            }), 401
        
        # Get user info
        user_info = user_service.get_user_info(username)
        
        # Get user features
        user_features = None
        menu_items = []
        if feature_service:
            user_features = feature_service.get_user_features(username)
            menu_items = feature_service.get_user_menu_items(username)
        
        return jsonify({
            'success': True,
            'authenticated': True,
            'user': user_info,
            'features': user_features,
            'menu_items': menu_items
        })
        
    except Exception as e:
        logger.error(f"Session check error: {e}")
        return jsonify({
            'success': False,
            'error': 'Session check failed'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user profile"""
    try:
        username = get_current_user()
        user_info = user_service.get_user_info(username)
        
        if not user_info:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'user': user_info
        })
        
    except Exception as e:
        logger.error(f"Profile error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get profile'
        }), 500

# Admin routes
@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users"""
    try:
        users = user_service.get_all_users()
        groups = user_service.get_all_groups()
        
        return jsonify({
            'success': True,
            'users': users,
            'groups': groups
        })
        
    except Exception as e:
        logger.error(f"Get users error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get users'
        }), 500

@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """Create new user"""
    try:
        data = request.get_json()
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        full_name = data.get('full_name', '').strip()
        groups = data.get('groups', ['viewers'])
        
        if not all([username, password, email, full_name]):
            return jsonify({
                'success': False,
                'error': 'All fields are required'
            }), 400
        
        success, message = user_service.create_user(
            username, password, email, full_name, groups
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
    except Exception as e:
        logger.error(f"Create user error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create user'
        }), 500

@admin_bp.route('/users/<username>/groups', methods=['PUT'])
@admin_required
def update_user_groups(username):
    """Update user groups"""
    try:
        data = request.get_json()
        groups = data.get('groups', [])
        
        success, message = user_service.update_user_groups(username, groups)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
    except Exception as e:
        logger.error(f"Update user groups error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update user groups'
        }), 500

@admin_bp.route('/features', methods=['GET'])
@admin_required
def get_features():
    """Get all features configuration"""
    try:
        if not feature_service:
            return jsonify({
                'success': False,
                'error': 'Feature service not available'
            }), 500
        
        features = feature_service.get_all_features()
        categories = feature_service.get_features_by_category()
        
        return jsonify({
            'success': True,
            'features': features,
            'categories': categories
        })
        
    except Exception as e:
        logger.error(f"Get features error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get features'
        }), 500

@admin_bp.route('/features/<feature_name>', methods=['PUT'])
@admin_required
def update_feature(feature_name):
    """Update feature configuration"""
    try:
        if not feature_service:
            return jsonify({
                'success': False,
                'error': 'Feature service not available'
            }), 500
        
        data = request.get_json()
        
        try:
            success, message = feature_service.update_feature_config(feature_name, data)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': message
                })
            else:
                return jsonify({
                    'success': False,
                    'error': message
                }), 400
        except Exception as update_error:
            logger.error(f"Feature update failed: {update_error}")
            return jsonify({
                'success': False,
                'error': 'Failed to update feature'
            }), 500
        
    except Exception as e:
        logger.error(f"Update feature error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update feature'
        }), 500

@admin_bp.route('/features/<feature_name>/override', methods=['POST'])
@admin_required
def override_feature(feature_name):
    """Override feature configuration temporarily"""
    try:
        if not feature_service:
            return jsonify({
                'success': False,
                'error': 'Feature service not available'
            }), 500
        
        data = request.get_json()
        overrides = data.get('overrides', {})
        
        feature_service.override_feature(feature_name, overrides)
        
        return jsonify({
            'success': True,
            'message': f'Feature {feature_name} override applied'
        })
        
    except Exception as e:
        logger.error(f"Override feature error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to override feature'
        }), 500

@admin_bp.route('/sessions', methods=['GET'])
@admin_required
def get_active_sessions():
    """Get active user sessions"""
    try:
        # Clean up expired sessions first
        user_service.cleanup_expired_sessions()
        
        sessions = []
        for session_id, session_data in user_service.active_sessions.items():
            # Don't expose full session ID for security
            safe_session = {
                'session_id': session_id[:8] + '...',
                'username': session_data['username'],
                'created_at': session_data['created_at'],
                'last_activity': session_data['last_activity'],
                'expires_at': session_data['expires_at']
            }
            sessions.append(safe_session)
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'total': len(sessions)
        })
        
    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get sessions'
        }), 500

# Public template routes
@auth_bp.route('/login-page')
def login_page():
    """Login page template"""
    return render_template('auth/login.html')

@admin_bp.route('/users-page')
@admin_required
def users_page():
    """User management page"""
    return render_template('admin/users.html')

@admin_bp.route('/features-page')
@admin_required
def features_page():
    """Feature management page"""
    return render_template('admin/features.html')