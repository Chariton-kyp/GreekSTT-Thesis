"""Authentication decorators with session validation."""

import functools
from flask import jsonify, current_app
from flask_jwt_extended import jwt_required, verify_jwt_in_request, get_jwt_identity
from app.auth.jwt_utils import validate_session_from_token, validate_token_claims


def session_required(f):
    """Decorator that requires a valid JWT token with session validation."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # First verify JWT token
        verify_jwt_in_request()
        
        # Then validate session if session management is enabled
        if current_app.config.get('ENABLE_SESSION_MANAGEMENT', True):
            if not validate_session_from_token():
                return jsonify({
                    'error': 'Session invalid or expired. Please log in again.',
                    'error_code': 'SESSION_INVALID'
                }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def auth_required(validate_session=True):
    """
    Simplified authentication decorator for academic research platform.
    
    Args:
        validate_session: Whether to validate session (default True)
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Verify JWT token
            verify_jwt_in_request()
            
            # Validate session if enabled
            if validate_session and current_app.config.get('ENABLE_SESSION_MANAGEMENT', True):
                if not validate_session_from_token():
                    return jsonify({
                        'error': 'Session invalid or expired. Please log in again.',
                        'error_code': 'SESSION_INVALID'
                    }), 401
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator




# Simplified login required alias
login_required = session_required