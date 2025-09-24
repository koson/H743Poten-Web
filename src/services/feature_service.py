"""
Feature management service for H743Poten Web Interface
Handles feature flags, user permissions, and dynamic feature control
"""

import json
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class FeatureService:
    def __init__(self, config_dir=None, user_service=None):
        """Initialize feature service"""
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / 'config'
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.features_file = self.config_dir / 'features.json'
        self.feature_overrides_file = self.config_dir / 'feature_overrides.json'
        
        self.user_service = user_service
        
        # Initialize features
        self._initialize_features()
        
        # Load feature overrides
        self.feature_overrides = {}
        self._load_feature_overrides()
    
    def _initialize_features(self):
        """Initialize default features configuration"""
        if not self.features_file.exists():
            default_features = {
                "measurements": {
                    "name": "Measurements",
                    "description": "Basic electrochemical measurement functionality (CV, DPV, SWV, CA)",
                    "category": "core",
                    "enabled": True,
                    "requires_permissions": ["read", "write"],
                    "routes": ["/measurements", "/api/measurement/*"],
                    "menu_item": {
                        "label": "Measurements",
                        "icon": "fas fa-chart-line",
                        "order": 1
                    }
                },
                "analysis_workflow": {
                    "name": "Analysis Workflow",
                    "description": "Advanced data analysis and visualization tools",
                    "category": "analysis",
                    "enabled": True,
                    "requires_permissions": ["read", "write"],
                    "routes": ["/workflow", "/api/workflow/*"],
                    "menu_item": {
                        "label": "Analysis Workflow",
                        "icon": "fas fa-project-diagram",
                        "order": 2
                    }
                },
                "ai_dashboard": {
                    "name": "AI Dashboard",
                    "description": "Machine learning-powered analysis tools and predictions",
                    "category": "ai",
                    "enabled": False,
                    "requires_permissions": ["read", "write"],
                    "routes": ["/ai-dashboard", "/api/ai/*"],
                    "menu_item": {
                        "label": "AI Dashboard",
                        "icon": "fas fa-brain",
                        "order": 8
                    }
                },
                "calibration": {
                    "name": "Calibration",
                    "description": "Cross-instrument calibration and validation tools",
                    "category": "calibration",
                    "enabled": True,
                    "requires_permissions": ["read", "write", "configure"],
                    "routes": ["/calibration", "/api/calibration/*"],
                    "menu_item": {
                        "label": "Calibration",
                        "icon": "fas fa-balance-scale",
                        "order": 3
                    }
                },
                "peak_detection": {
                    "name": "Peak Detection",
                    "description": "Automated peak detection and analysis algorithms",
                    "category": "analysis",
                    "enabled": True,
                    "requires_permissions": ["read", "write"],
                    "routes": ["/peak_detection", "/api/peak-detection/*"],
                    "menu_item": {
                        "label": "Peak Detection",
                        "icon": "fas fa-mountain",
                        "order": 4
                    }
                },
                "data_logging": {
                    "name": "Data Logging",
                    "description": "Automated data logging and storage management",
                    "category": "core",
                    "enabled": True,
                    "requires_permissions": ["read", "write"],
                    "routes": ["/data-browser", "/api/data-logging/*"],
                    "menu_item": {
                        "label": "Data Browser",
                        "icon": "fas fa-database",
                        "order": 5
                    }
                },
                "csv_emulation": {
                    "name": "CSV Emulation",
                    "description": "CSV data emulation for testing and development",
                    "category": "development",
                    "enabled": True,
                    "requires_permissions": ["read", "write"],
                    "routes": ["/api/emulation/*"],
                    "menu_item": None  # Hidden menu item
                },
                "hardware_diagnostics": {
                    "name": "Hardware Diagnostics",
                    "description": "Advanced hardware testing and diagnostics tools",
                    "category": "development",
                    "enabled": False,
                    "requires_permissions": ["read", "write", "admin"],
                    "routes": ["/diagnostics", "/api/diagnostics/*"],
                    "menu_item": {
                        "label": "Diagnostics",
                        "icon": "fas fa-stethoscope",
                        "order": 9
                    }
                },
                "user_management": {
                    "name": "User Management",
                    "description": "User account and permission management",
                    "category": "admin",
                    "enabled": True,
                    "requires_permissions": ["admin"],
                    "routes": ["/admin/users", "/api/admin/users/*"],
                    "menu_item": {
                        "label": "User Management",
                        "icon": "fas fa-users",
                        "order": 10
                    }
                },
                "system_settings": {
                    "name": "System Settings",
                    "description": "System configuration and feature management",
                    "category": "admin",
                    "enabled": True,
                    "requires_permissions": ["admin", "configure"],
                    "routes": ["/settings", "/api/settings/*"],
                    "menu_item": {
                        "label": "Settings",
                        "icon": "fas fa-cog",
                        "order": 11
                    }
                },
                "advanced_analysis": {
                    "name": "Advanced Analysis",
                    "description": "Advanced statistical and mathematical analysis tools",
                    "category": "analysis",
                    "enabled": True,
                    "requires_permissions": ["read", "write"],
                    "routes": ["/api/analysis/advanced/*"],
                    "menu_item": None  # Hidden menu item, accessed through workflow
                },
                "data_export": {
                    "name": "Data Export",
                    "description": "Export data in various formats (CSV, JSON, Excel)",
                    "category": "core",
                    "enabled": True,
                    "requires_permissions": ["read"],
                    "routes": ["/api/data/export/*"],
                    "menu_item": None  # Hidden menu item, accessed through buttons
                },
                "device_control": {
                    "name": "Device Control",
                    "description": "Direct device control and SCPI command interface",
                    "category": "core",
                    "enabled": True,
                    "requires_permissions": ["write", "configure"],
                    "routes": ["/api/device/*", "/api/uart/*"],
                    "menu_item": None  # Hidden menu item, accessed through measurement interface
                }
            }
            
            with open(self.features_file, 'w') as f:
                json.dump(default_features, f, indent=2)
            
            logger.info("Initialized default features configuration")
    
    def _load_feature_overrides(self):
        """Load feature overrides from file"""
        if self.feature_overrides_file.exists():
            try:
                with open(self.feature_overrides_file, 'r') as f:
                    self.feature_overrides = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load feature overrides: {e}")
                self.feature_overrides = {}
    
    def _save_feature_overrides(self):
        """Save feature overrides to file"""
        try:
            with open(self.feature_overrides_file, 'w') as f:
                json.dump(self.feature_overrides, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save feature overrides: {e}")
    
    def get_all_features(self):
        """Get all available features"""
        try:
            with open(self.features_file, 'r') as f:
                features = json.load(f)
            
            # Apply overrides
            for feature_name, override_data in self.feature_overrides.items():
                if feature_name in features:
                    features[feature_name].update(override_data)
            
            return features
            
        except Exception as e:
            logger.error(f"Failed to get features: {e}")
            return {}
    
    def get_user_features(self, username):
        """Get features available to specific user"""
        if not self.user_service:
            # Fallback to all features if no user service
            return self.get_all_features()
        
        # Get user's feature permissions
        user_data = self.user_service.get_user_features(username)
        user_feature_flags = user_data.get('features', {})
        user_permissions = set(user_data.get('permissions', []))
        
        # Get all features
        all_features = self.get_all_features()
        
        # Filter features based on user permissions
        user_features = {}
        for feature_name, feature_config in all_features.items():
            # Check if user's group allows this feature
            if not user_feature_flags.get(feature_name, False):
                continue
            
            # Check if user has required permissions
            required_permissions = set(feature_config.get('requires_permissions', []))
            if required_permissions and not required_permissions.intersection(user_permissions):
                continue
            
            user_features[feature_name] = feature_config
        
        return user_features
    
    def is_feature_enabled_for_user(self, username, feature_name):
        """Check if specific feature is enabled for user"""
        user_features = self.get_user_features(username)
        return feature_name in user_features and user_features[feature_name].get('enabled', False)
    
    def get_user_menu_items(self, username):
        """Get menu items available to user"""
        user_features = self.get_user_features(username)
        
        menu_items = []
        for feature_name, feature_config in user_features.items():
            menu_item = feature_config.get('menu_item')
            if menu_item:
                menu_items.append({
                    'feature': feature_name,
                    'label': menu_item['label'],
                    'icon': menu_item['icon'],
                    'order': menu_item.get('order', 999),
                    'category': feature_config.get('category', 'other')
                })
        
        # Sort by order
        menu_items.sort(key=lambda x: x['order'])
        return menu_items
    
    def get_user_routes(self, username):
        """Get routes/endpoints available to user"""
        user_features = self.get_user_features(username)
        
        allowed_routes = set()
        for feature_config in user_features.values():
            routes = feature_config.get('routes', [])
            allowed_routes.update(routes)
        
        return list(allowed_routes)
    
    def can_access_route(self, username, route):
        """Check if user can access specific route"""
        allowed_routes = self.get_user_routes(username)
        
        # Check exact match first
        if route in allowed_routes:
            return True
        
        # Check wildcard matches
        for allowed_route in allowed_routes:
            if allowed_route.endswith('/*'):
                prefix = allowed_route[:-2]  # Remove /*
                if route.startswith(prefix):
                    return True
        
        return False
    
    def override_feature(self, feature_name, overrides):
        """Override feature configuration"""
        self.feature_overrides[feature_name] = {
            **overrides,
            'override_timestamp': datetime.now().isoformat()
        }
        self._save_feature_overrides()
        logger.info(f"Applied override to feature {feature_name}: {overrides}")
    
    def clear_feature_override(self, feature_name):
        """Clear feature override"""
        if feature_name in self.feature_overrides:
            del self.feature_overrides[feature_name]
            self._save_feature_overrides()
            logger.info(f"Cleared override for feature {feature_name}")
    
    def get_features_by_category(self, username=None):
        """Get features grouped by category"""
        if username:
            features = self.get_user_features(username)
        else:
            features = self.get_all_features()
        
        categories = {}
        for feature_name, feature_config in features.items():
            category = feature_config.get('category', 'other')
            if category not in categories:
                categories[category] = []
            
            categories[category].append({
                'name': feature_name,
                'config': feature_config
            })
        
        return categories
    
    def update_feature_config(self, feature_name: str, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Update feature configuration"""
        try:
            with open(self.features_file, 'r') as f:
                features = json.load(f)
            
            if feature_name not in features:
                return False, "Feature not found"
            
            features[feature_name].update(config)
            features[feature_name]['updated_at'] = datetime.now().isoformat()
            
            with open(self.features_file, 'w') as f:
                json.dump(features, f, indent=2)
            
            logger.info(f"Updated feature {feature_name}: {config}")
            return True, "Feature updated successfully"
            
        except Exception as e:
            logger.error(f"Failed to update feature: {e}")
            return False, str(e)
    
    def create_feature(self, feature_name: str, config: Dict[str, Any]) -> Tuple[bool, str]:
        """Create new feature"""
        try:
            with open(self.features_file, 'r') as f:
                features = json.load(f)
            
            if feature_name in features:
                return False, "Feature already exists"
            
            features[feature_name] = {
                **config,
                'created_at': datetime.now().isoformat()
            }
            
            with open(self.features_file, 'w') as f:
                json.dump(features, f, indent=2)
            
            logger.info(f"Created feature {feature_name}")
            return True, "Feature created successfully"
            
        except Exception as e:
            logger.error(f"Failed to create feature: {e}")
            return False, str(e)
    
    def delete_feature(self, feature_name: str) -> Tuple[bool, str]:
        """Delete feature"""
        try:
            with open(self.features_file, 'r') as f:
                features = json.load(f)
            
            if feature_name not in features:
                return False, "Feature not found"
            
            del features[feature_name]
            
            with open(self.features_file, 'w') as f:
                json.dump(features, f, indent=2)
            
            # Also clear any overrides
            self.clear_feature_override(feature_name)
            
            logger.info(f"Deleted feature {feature_name}")
            return True, "Feature deleted successfully"
            
        except Exception as e:
            logger.error(f"Failed to delete feature: {e}")
            return False, str(e)

# Default instance (will be initialized with user service in app.py)
feature_service = None