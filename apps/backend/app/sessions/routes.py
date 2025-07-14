"""Simple session management routes for thesis project."""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.sessions.services import session_service
from app.users.models import User

sessions_bp = Blueprint('sessions', __name__)


@sessions_bp.route('/active', methods=['GET'])
@jwt_required()
def get_active_sessions():
    """Get active sessions count for current user."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Simple session count
        session_count = user.sessions.count()
        
        return jsonify({
            'success': True,
            'session_count': session_count,
            'message': f'You have {session_count} active session(s)'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting sessions: {str(e)}")
        return jsonify({'error': 'Failed to get sessions'}), 500


@sessions_bp.route('/logout-all', methods=['POST'])
@jwt_required()
def logout_all_sessions():
    """Logout all sessions for current user."""
    try:
        user_id = get_jwt_identity()
        count = session_service.delete_user_sessions(user_id)
        
        return jsonify({
            'success': True,
            'message': f'Successfully logged out from {count} session(s)'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error logging out sessions: {str(e)}")
        return jsonify({'error': 'Failed to logout sessions'}), 500