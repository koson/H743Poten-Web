from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
import uuid

# Create blueprint
bp = Blueprint('peak_analysis', __name__)

# Store for temporary analysis sessions
analysis_sessions = {}

@bp.route('/create_analysis_session', methods=['POST'])
def create_analysis_session():
    """Create a new analysis session and return session ID"""
    data = request.json
    session_id = str(uuid.uuid4())
    
    # Store data in server-side session
    analysis_sessions[session_id] = {
        'peaks': data['peaks'],
        'data': data['data'],
        'created_at': datetime.utcnow()
    }
    
    return jsonify({'session_id': session_id})

@bp.route('/peak_analysis/<session_id>')
def peak_analysis(session_id):
    """Render the peak analysis page with session data"""
    if session_id not in analysis_sessions:
        return "Analysis session not found", 404
        
    session_data = analysis_sessions[session_id]
    return render_template('peak_analysis.html',
                         peaks=session_data['peaks'],
                         data=session_data['data'])

# Cleanup function for old sessions
def cleanup_old_sessions(max_age_hours=24):
    """Remove analysis sessions older than max_age_hours"""
    current_time = datetime.utcnow()
    expired_sessions = [
        session_id for session_id, data in analysis_sessions.items()
        if (current_time - data['created_at']).total_seconds() > max_age_hours * 3600
    ]
    for session_id in expired_sessions:
        del analysis_sessions[session_id]