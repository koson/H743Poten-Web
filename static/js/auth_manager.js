/**
 * Authentication and Feature Management for H743Poten Web Interface
 */

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.userFeatures = {};
        this.menuItems = [];
        this.isAuthenticated = false;
        
        // Initialize on page load
        this.init();
    }
    
    async init() {
        // Check session on page load
        await this.checkSession();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Update UI based on auth state
        this.updateUI();
    }
    
    setupEventListeners() {
        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }
        
        // Refresh session periodically (every 5 minutes)
        setInterval(() => {
            if (this.isAuthenticated) {
                this.checkSession();
            }
        }, 5 * 60 * 1000);
    }
    
    async checkSession() {
        try {
            const response = await fetch('/auth/check-session', {
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (data.success && data.authenticated) {
                this.currentUser = data.user;
                this.userFeatures = data.features || {};
                this.menuItems = data.menu_items || [];
                this.isAuthenticated = true;
                
                console.log('User authenticated:', this.currentUser.username);
                console.log('Available features:', Object.keys(this.userFeatures));
                
            } else {
                this.currentUser = null;
                this.userFeatures = {};
                this.menuItems = [];
                this.isAuthenticated = false;
                
                // Redirect to login for protected pages
                if (this.isProtectedPage()) {
                    this.redirectToLogin();
                }
            }
            
            this.updateUI();
            
        } catch (error) {
            console.error('Session check failed:', error);
            this.isAuthenticated = false;
            this.updateUI();
        }
    }
    
    async logout() {
        try {
            const response = await fetch('/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentUser = null;
                this.userFeatures = {};
                this.menuItems = [];
                this.isAuthenticated = false;
                
                this.updateUI();
                
                // Show success message
                this.showAlert('Logged out successfully', 'success');
                
                // Redirect to login page after a delay
                setTimeout(() => {
                    window.location.href = '/auth/login-page';
                }, 1000);
                
            } else {
                this.showAlert('Logout failed', 'danger');
            }
            
        } catch (error) {
            console.error('Logout failed:', error);
            this.showAlert('Logout failed', 'danger');
        }
    }
    
    updateUI() {
        this.updateUserMenu();
        this.updateNavigation();
        this.updateFeatureElements();
    }
    
    updateUserMenu() {
        const userMenuContainer = document.getElementById('userMenuContainer');
        const loginBtnContainer = document.getElementById('loginBtnContainer');
        
        if (this.isAuthenticated && this.currentUser) {
            // Show user menu
            if (userMenuContainer) userMenuContainer.style.display = 'block';
            if (loginBtnContainer) loginBtnContainer.style.display = 'none';
            
            // Update user info
            const currentUsername = document.getElementById('currentUsername');
            const userFullName = document.getElementById('userFullName');
            const userEmail = document.getElementById('userEmail');
            const userRoleBadges = document.getElementById('userRoleBadges');
            
            if (currentUsername) currentUsername.textContent = this.currentUser.username;
            if (userFullName) userFullName.textContent = this.currentUser.full_name;
            if (userEmail) userEmail.textContent = this.currentUser.email;
            
            // Update role badges
            if (userRoleBadges && this.currentUser.groups) {
                userRoleBadges.innerHTML = this.currentUser.groups.map(group => {
                    const badgeClass = this.getBadgeClass(group);
                    return `<span class="badge ${badgeClass} user-role-badge">${group}</span>`;
                }).join(' ');
            }
            
        } else {
            // Show login button
            if (userMenuContainer) userMenuContainer.style.display = 'none';
            if (loginBtnContainer) loginBtnContainer.style.display = 'block';
        }
    }
    
    updateNavigation() {
        // Update navigation items based on user features
        const navItems = document.querySelectorAll('[data-feature]');
        
        navItems.forEach(item => {
            const featureName = item.getAttribute('data-feature');
            
            if (this.hasFeature(featureName)) {
                item.classList.remove('feature-disabled');
                item.style.display = '';
            } else {
                item.classList.add('feature-disabled');
                // Hide completely for unauthorized features
                if (!this.isAuthenticated) {
                    item.style.display = 'none';
                }
            }
        });
    }
    
    updateFeatureElements() {
        // Update any elements that depend on specific features
        const featureElements = document.querySelectorAll('[data-requires-feature]');
        
        featureElements.forEach(element => {
            const requiredFeature = element.getAttribute('data-requires-feature');
            
            if (this.hasFeature(requiredFeature)) {
                element.style.display = '';
                element.classList.remove('feature-disabled');
            } else {
                element.style.display = 'none';
                element.classList.add('feature-disabled');
            }
        });
        
        // Update permission-based elements
        const permissionElements = document.querySelectorAll('[data-requires-permission]');
        
        permissionElements.forEach(element => {
            const requiredPermission = element.getAttribute('data-requires-permission');
            
            if (this.hasPermission(requiredPermission)) {
                element.style.display = '';
                element.classList.remove('feature-disabled');
            } else {
                element.style.display = 'none';
                element.classList.add('feature-disabled');
            }
        });
    }
    
    hasFeature(featureName) {
        if (!this.isAuthenticated) return false;
        return this.userFeatures.features && this.userFeatures.features[featureName] === true;
    }
    
    hasPermission(permission) {
        if (!this.isAuthenticated) return false;
        return this.userFeatures.permissions && this.userFeatures.permissions.includes(permission);
    }
    
    getBadgeClass(groupName) {
        const classMap = {
            'administrators': 'bg-danger',
            'operators': 'bg-primary',
            'researchers': 'bg-info',
            'viewers': 'bg-secondary'
        };
        return classMap[groupName] || 'bg-warning';
    }
    
    isProtectedPage() {
        // Define which pages require authentication
        const protectedPaths = [
            '/admin/',
            '/settings',
            '/api/'
        ];
        
        const currentPath = window.location.pathname;
        return protectedPaths.some(path => currentPath.startsWith(path));
    }
    
    redirectToLogin() {
        // Save current page for redirect after login
        sessionStorage.setItem('redirectAfterLogin', window.location.href);
        window.location.href = '/auth/login-page';
    }
    
    showAlert(message, type = 'info') {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alert.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
        `;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
    
    // Utility method to make authenticated API calls
    async authenticatedFetch(url, options = {}) {
        const defaultOptions = {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };
        
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        // Check if response indicates authentication failure
        if (response.status === 401) {
            this.isAuthenticated = false;
            this.updateUI();
            this.redirectToLogin();
            throw new Error('Authentication required');
        }
        
        return response;
    }
    
    // Check if user can access specific route
    canAccessRoute(route) {
        if (!this.isAuthenticated) return false;
        
        // Implementation would depend on backend route checking
        // For now, just check if user has any permissions
        return this.userFeatures.permissions && this.userFeatures.permissions.length > 0;
    }
}

// Initialize auth manager when DOM is loaded
let authManager;

document.addEventListener('DOMContentLoaded', () => {
    authManager = new AuthManager();
});

// Export for use in other scripts
window.authManager = authManager;