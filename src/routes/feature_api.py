"""
Feature toggle API routes for dynamic feature management
"""

from flask import Blueprint, request, jsonify, render_template
import logging
from datetime import datetime

from ..middleware.auth import login_required, admin_required, permission_required, get_current_user
from ..services.feature_service import feature_service

logger = logging.getLogger(__name__)

feature_api_bp = Blueprint('feature_api', __name__, url_prefix='/api/features')

@feature_api_bp.route('/user', methods=['GET'])
@login_required
def get_user_features():
    """Get features available to current user"""
    try:
        username = get_current_user()
        if not username:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 401
        
        if not feature_service:
            # Fallback: return all features as enabled
            return jsonify({
                'success': True,
                'features': {},
                'menu_items': [],
                'permissions': []
            })
        
        user_features = feature_service.get_user_features(username)
        menu_items = feature_service.get_user_menu_items(username)
        
        return jsonify({
            'success': True,
            'features': user_features,
            'menu_items': menu_items,
            'permissions': feature_service.user_service.get_user_features(username).get('permissions', [])
        })
        
    except Exception as e:
        logger.error(f"Failed to get user features: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get user features'
        }), 500

@feature_api_bp.route('/toggle/<feature_name>', methods=['POST'])
@admin_required
def toggle_feature(feature_name):
    """Toggle feature on/off temporarily (admin override)"""
    try:
        if not feature_service:
            return jsonify({
                'success': False,
                'error': 'Feature service not available'
            }), 500
        
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        # Apply override
        feature_service.override_feature(feature_name, {'enabled': enabled})
        
        return jsonify({
            'success': True,
            'message': f'Feature {feature_name} {"enabled" if enabled else "disabled"}'
        })
        
    except Exception as e:
        logger.error(f"Failed to toggle feature: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to toggle feature'
        }), 500

@feature_api_bp.route('/user-group-features/<group_name>', methods=['GET'])
@admin_required
def get_group_features(group_name):
    """Get features for specific user group"""
    try:
        if not feature_service or not feature_service.user_service:
            return jsonify({
                'success': False,
                'error': 'Services not available'
            }), 500
        
        groups = feature_service.user_service.get_all_groups()
        
        if group_name not in groups:
            return jsonify({
                'success': False,
                'error': 'Group not found'
            }), 404
        
        group_info = groups[group_name]
        
        return jsonify({
            'success': True,
            'group': group_info,
            'features': group_info.get('features', {}),
            'permissions': group_info.get('permissions', [])
        })
        
    except Exception as e:
        logger.error(f"Failed to get group features: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get group features'
        }), 500

@feature_api_bp.route('/deployment-config', methods=['GET'])
@admin_required
def get_deployment_config():
    """Get deployment configuration for different user groups"""
    try:
        if not feature_service or not feature_service.user_service:
            return jsonify({
                'success': False,
                'error': 'Services not available'
            }), 500
        
        # Get all groups and their features
        groups = feature_service.user_service.get_all_groups()
        all_features = feature_service.get_all_features()
        
        deployment_config = {
            'groups': {},
            'features': all_features
        }
        
        for group_name, group_info in groups.items():
            # Get effective features for this group
            enabled_features = []
            disabled_features = []
            
            for feature_name, feature_config in all_features.items():
                if group_info.get('features', {}).get(feature_name, False):
                    enabled_features.append({
                        'name': feature_name,
                        'label': feature_config.get('name', feature_name),
                        'category': feature_config.get('category', 'other')
                    })
                else:
                    disabled_features.append({
                        'name': feature_name,
                        'label': feature_config.get('name', feature_name),
                        'category': feature_config.get('category', 'other')
                    })
            
            deployment_config['groups'][group_name] = {
                'info': group_info,
                'enabled_features': enabled_features,
                'disabled_features': disabled_features,
                'feature_count': {
                    'enabled': len(enabled_features),
                    'disabled': len(disabled_features),
                    'total': len(all_features)
                }
            }
        
        return jsonify({
            'success': True,
            'deployment_config': deployment_config
        })
        
    except Exception as e:
        logger.error(f"Failed to get deployment config: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get deployment config'
        }), 500

@feature_api_bp.route('/create-deployment', methods=['POST'])
@admin_required
def create_deployment():
    """Create a custom deployment configuration"""
    try:
        data = request.get_json()
        
        deployment_name = data.get('name', '').strip()
        selected_features = data.get('features', [])
        target_groups = data.get('groups', [])
        
        if not deployment_name:
            return jsonify({
                'success': False,
                'error': 'Deployment name is required'
            }), 400
        
        if not feature_service or not feature_service.user_service:
            return jsonify({
                'success': False,
                'error': 'Services not available'
            }), 500
        
        # Create deployment configuration
        deployment_config = {
            'name': deployment_name,
            'created_by': get_current_user(),
            'features': selected_features,
            'target_groups': target_groups,
            'created_at': datetime.now().isoformat()
        }
        
        # Apply overrides for selected features
        for feature_name in selected_features:
            feature_service.override_feature(feature_name, {
                'enabled': True,
                'deployment': deployment_name
            })
        
        # Log deployment creation
        logger.info(f"Created deployment '{deployment_name}' with features: {selected_features}")
        
        return jsonify({
            'success': True,
            'message': f'Deployment "{deployment_name}" created successfully',
            'deployment': deployment_config
        })
        
    except Exception as e:
        logger.error(f"Failed to create deployment: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create deployment'
        }), 500

@feature_api_bp.route('/simulate-user/<username>', methods=['GET'])
@admin_required
def simulate_user_view(username):
    """Simulate what features a specific user would see"""
    try:
        if not feature_service or not feature_service.user_service:
            return jsonify({
                'success': False,
                'error': 'Services not available'
            }), 500
        
        # Check if user exists
        user_info = feature_service.user_service.get_user_info(username)
        if not user_info:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Get user features and menu items
        user_features = feature_service.get_user_features(username)
        menu_items = feature_service.get_user_menu_items(username)
        routes = feature_service.get_user_routes(username)
        
        return jsonify({
            'success': True,
            'user': user_info,
            'features': user_features,
            'menu_items': menu_items,
            'accessible_routes': routes,
            'feature_summary': {
                'total_features': len(feature_service.get_all_features()),
                'enabled_features': len(user_features),
                'feature_categories': feature_service.get_features_by_category(username)
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to simulate user view: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to simulate user view'
        }), 500

# Feature testing routes
@feature_api_bp.route('/test-access/<feature_name>', methods=['GET'])
@login_required
def test_feature_access(feature_name):
    """Test if current user can access specific feature"""
    try:
        username = get_current_user()
        
        if not feature_service:
            return jsonify({
                'success': True,
                'has_access': True,  # Fallback: allow access
                'reason': 'Feature service not available'
            })
        
        has_access = feature_service.is_feature_enabled_for_user(username, feature_name)
        
        return jsonify({
            'success': True,
            'has_access': has_access,
            'feature_name': feature_name,
            'username': username
        })
        
    except Exception as e:
        logger.error(f"Failed to test feature access: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to test feature access'
        }), 500