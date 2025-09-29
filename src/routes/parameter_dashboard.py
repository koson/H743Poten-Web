"""
Parameter Dashboard Routes
Provides web interface routes for parameter management
"""

from flask import Blueprint, render_template
import logging

logger = logging.getLogger(__name__)

# Main blueprint for dashboard routes (no prefix)
parameter_dashboard_bp = Blueprint('parameter_dashboard', __name__)

@parameter_dashboard_bp.route('/parameter_dashboard')
def parameter_dashboard():
    """Display parameter management dashboard"""
    logger.info("Parameter dashboard accessed")
    return render_template('parameter_dashboard.html')

@parameter_dashboard_bp.route('/api/measurements')
def api_measurements_redirect():
    """Redirect for direct API access"""
    from flask import redirect, url_for
    return redirect(url_for('parameter_api.get_measurements'))