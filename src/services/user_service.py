"""
User management service for H743Poten Web Interface
Handles user authentication, roles, and feature permissions
"""

import json
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, config_dir=None):
        """Initialize user service with configuration directory"""
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / 'config'
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.users_file = self.config_dir / 'users.json'
        self.groups_file = self.config_dir / 'user_groups.json'
        self.sessions_file = self.config_dir / 'sessions.json'
        
        # Initialize default data
        self._initialize_default_users()
        self._initialize_default_groups()
        
        # Session management
        self.active_sessions = {}
        self._load_sessions()
    
    def _initialize_default_users(self):
        """Initialize default users if users file doesn't exist"""
        if not self.users_file.exists():
            default_users = {
                "admin": {
                    "username": "admin",
                    "password_hash": self._hash_password("admin123"),
                    "email": "admin@h743poten.local",
                    "full_name": "System Administrator",
                    "groups": ["administrators"],
                    "created_at": datetime.now().isoformat(),
                    "active": True,
                    "last_login": None
                },
                "operator": {
                    "username": "operator",
                    "password_hash": self._hash_password("operator123"),
                    "email": "operator@h743poten.local",
                    "full_name": "System Operator",
                    "groups": ["operators"],
                    "created_at": datetime.now().isoformat(),
                    "active": True,
                    "last_login": None
                },
                "researcher": {
                    "username": "researcher",
                    "password_hash": self._hash_password("research123"),
                    "email": "researcher@h743poten.local",
                    "full_name": "Researcher",
                    "groups": ["researchers"],
                    "created_at": datetime.now().isoformat(),
                    "active": True,
                    "last_login": None
                },
                "viewer": {
                    "username": "viewer",
                    "password_hash": self._hash_password("viewer123"),
                    "email": "viewer@h743poten.local",
                    "full_name": "Data Viewer",
                    "groups": ["viewers"],
                    "created_at": datetime.now().isoformat(),
                    "active": True,
                    "last_login": None
                }
            }
            
            with open(self.users_file, 'w') as f:
                json.dump(default_users, f, indent=2)
            
            logger.info("Initialized default users")
    
    def _initialize_default_groups(self):
        """Initialize default user groups and their feature permissions"""
        if not self.groups_file.exists():
            default_groups = {
                "administrators": {
                    "name": "Administrators",
                    "description": "Full system access with all features",
                    "features": {
                        "measurements": True,
                        "analysis_workflow": True,
                        "ai_dashboard": True,
                        "calibration": True,
                        "peak_detection": True,
                        "data_logging": True,
                        "csv_emulation": True,
                        "hardware_diagnostics": True,
                        "user_management": True,
                        "system_settings": True,
                        "advanced_analysis": True,
                        "data_export": True,
                        "device_control": True
                    },
                    "permissions": [
                        "read", "write", "delete", "admin", "configure"
                    ]
                },
                "operators": {
                    "name": "Operators",
                    "description": "Standard measurement and analysis operations",
                    "features": {
                        "measurements": True,
                        "analysis_workflow": True,
                        "ai_dashboard": False,
                        "calibration": True,
                        "peak_detection": True,
                        "data_logging": True,
                        "csv_emulation": True,
                        "hardware_diagnostics": False,
                        "user_management": False,
                        "system_settings": False,
                        "advanced_analysis": True,
                        "data_export": True,
                        "device_control": True
                    },
                    "permissions": [
                        "read", "write", "configure"
                    ]
                },
                "researchers": {
                    "name": "Researchers",
                    "description": "Research-focused features with data analysis",
                    "features": {
                        "measurements": True,
                        "analysis_workflow": True,
                        "ai_dashboard": True,
                        "calibration": True,
                        "peak_detection": True,
                        "data_logging": True,
                        "csv_emulation": True,
                        "hardware_diagnostics": False,
                        "user_management": False,
                        "system_settings": False,
                        "advanced_analysis": True,
                        "data_export": True,
                        "device_control": False
                    },
                    "permissions": [
                        "read", "write"
                    ]
                },
                "viewers": {
                    "name": "Viewers",
                    "description": "Read-only access to data and basic visualizations",
                    "features": {
                        "measurements": False,
                        "analysis_workflow": True,
                        "ai_dashboard": False,
                        "calibration": False,
                        "peak_detection": True,
                        "data_logging": False,
                        "csv_emulation": False,
                        "hardware_diagnostics": False,
                        "user_management": False,
                        "system_settings": False,
                        "advanced_analysis": False,
                        "data_export": False,
                        "device_control": False
                    },
                    "permissions": [
                        "read"
                    ]
                }
            }
            
            with open(self.groups_file, 'w') as f:
                json.dump(default_groups, f, indent=2)
            
            logger.info("Initialized default user groups")
    
    def _hash_password(self, password):
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{pwd_hash}"
    
    def _verify_password(self, password, hash_str):
        """Verify password against hash"""
        try:
            salt, pwd_hash = hash_str.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
        except ValueError:
            return False
    
    def _load_sessions(self):
        """Load active sessions from file"""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r') as f:
                    stored_sessions = json.load(f)
                
                # Clean expired sessions
                current_time = datetime.now()
                for session_id, session_data in stored_sessions.items():
                    expires_at = datetime.fromisoformat(session_data['expires_at'])
                    if expires_at > current_time:
                        self.active_sessions[session_id] = session_data
                
                self._save_sessions()
                
            except Exception as e:
                logger.error(f"Failed to load sessions: {e}")
                self.active_sessions = {}
    
    def _save_sessions(self):
        """Save active sessions to file"""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(self.active_sessions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    def authenticate(self, username, password):
        """Authenticate user and create session"""
        try:
            with open(self.users_file, 'r') as f:
                users = json.load(f)
            
            if username not in users:
                return None
            
            user = users[username]
            
            if not user.get('active', True):
                return None
            
            if not self._verify_password(password, user['password_hash']):
                return None
            
            # Create session
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)  # 24 hour session
            
            session_data = {
                'session_id': session_id,
                'username': username,
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat(),
                'last_activity': datetime.now().isoformat()
            }
            
            self.active_sessions[session_id] = session_data
            self._save_sessions()
            
            # Update last login
            user['last_login'] = datetime.now().isoformat()
            users[username] = user
            
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
            
            logger.info(f"User {username} authenticated successfully")
            return session_data
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
    
    def validate_session(self, session_id):
        """Validate session and return user info"""
        if not session_id or session_id not in self.active_sessions:
            return None
        
        session_data = self.active_sessions[session_id]
        
        # Check if session is expired
        expires_at = datetime.fromisoformat(session_data['expires_at'])
        if expires_at <= datetime.now():
            del self.active_sessions[session_id]
            self._save_sessions()
            return None
        
        # Update last activity
        session_data['last_activity'] = datetime.now().isoformat()
        self.active_sessions[session_id] = session_data
        self._save_sessions()
        
        return session_data
    
    def logout(self, session_id):
        """Logout user by removing session"""
        if session_id in self.active_sessions:
            username = self.active_sessions[session_id]['username']
            del self.active_sessions[session_id]
            self._save_sessions()
            logger.info(f"User {username} logged out")
            return True
        return False
    
    def get_user_info(self, username):
        """Get user information"""
        try:
            with open(self.users_file, 'r') as f:
                users = json.load(f)
            
            if username not in users:
                return None
            
            user = users[username].copy()
            # Remove sensitive data
            user.pop('password_hash', None)
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None
    
    def get_user_features(self, username):
        """Get features available to user based on their groups"""
        try:
            user = self.get_user_info(username)
            if not user:
                return {}
            
            with open(self.groups_file, 'r') as f:
                groups = json.load(f)
            
            # Aggregate features from all user groups
            user_features = {}
            user_permissions = set()
            
            for group_name in user.get('groups', []):
                if group_name in groups:
                    group = groups[group_name]
                    # Merge features (OR operation - if any group has feature, user gets it)
                    for feature, enabled in group.get('features', {}).items():
                        user_features[feature] = user_features.get(feature, False) or enabled
                    
                    # Add permissions
                    user_permissions.update(group.get('permissions', []))
            
            return {
                'features': user_features,
                'permissions': list(user_permissions),
                'groups': user.get('groups', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get user features: {e}")
            return {'features': {}, 'permissions': [], 'groups': []}
    
    def has_permission(self, username, permission):
        """Check if user has specific permission"""
        user_data = self.get_user_features(username)
        return permission in user_data.get('permissions', [])
    
    def has_feature(self, username, feature):
        """Check if user has access to specific feature"""
        user_data = self.get_user_features(username)
        return user_data.get('features', {}).get(feature, False)
    
    def get_all_groups(self):
        """Get all available user groups"""
        try:
            with open(self.groups_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to get groups: {e}")
            return {}
    
    def create_user(self, username, password, email, full_name, groups=None):
        """Create new user"""
        try:
            with open(self.users_file, 'r') as f:
                users = json.load(f)
            
            if username in users:
                return False, "User already exists"
            
            if groups is None:
                groups = ["viewers"]  # Default group
            
            users[username] = {
                "username": username,
                "password_hash": self._hash_password(password),
                "email": email,
                "full_name": full_name,
                "groups": groups,
                "created_at": datetime.now().isoformat(),
                "active": True,
                "last_login": None
            }
            
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
            
            logger.info(f"Created user: {username}")
            return True, "User created successfully"
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return False, str(e)
    
    def update_user_groups(self, username, groups):
        """Update user's groups"""
        try:
            with open(self.users_file, 'r') as f:
                users = json.load(f)
            
            if username not in users:
                return False, "User not found"
            
            users[username]['groups'] = groups
            
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
            
            logger.info(f"Updated groups for user {username}: {groups}")
            return True, "User groups updated successfully"
            
        except Exception as e:
            logger.error(f"Failed to update user groups: {e}")
            return False, str(e)
    
    def get_all_users(self):
        """Get all users (without sensitive data)"""
        try:
            with open(self.users_file, 'r') as f:
                users = json.load(f)
            
            # Remove sensitive data
            safe_users = {}
            for username, user_data in users.items():
                safe_user = user_data.copy()
                safe_user.pop('password_hash', None)
                safe_users[username] = safe_user
            
            return safe_users
            
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            return {}
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in self.active_sessions.items():
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if expires_at <= current_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            self._save_sessions()
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)

# Global instance
user_service = UserService()