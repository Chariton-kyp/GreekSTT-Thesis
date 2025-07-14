"""
Email verification requirement decorator for routes.
This allows users to access basic features without email verification
but restricts advanced features that require verified email.
"""

from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import get_current_user, jwt_required

from app.constants.messages import AUTH_MESSAGES


def verification_required(f):
    """
    Decorator that requires email verification for specific endpoints.
    
    Users can access dashboard and profile without verification,
    but other features are restricted until email is verified.
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        # Get current user
        current_user = get_current_user()
        
        # Check if email verification is required
        if (current_app.config.get('ENABLE_EMAIL_VERIFICATION') and 
            not current_user.email_verified):
            
            return jsonify({
                'error': 'Email verification required for this action',
                'error_code': 'EMAIL_NOT_VERIFIED',
                'message': 'Παρακαλώ επιβεβαιώστε το email σας για να χρησιμοποιήσετε αυτή τη λειτουργία.',
                'verification_required': True
            }), 403  # 403 Forbidden instead of 401 Unauthorized
        
        return f(*args, **kwargs)
    
    return decorated_function


def verification_optional(f):
    """
    Decorator that marks a route as not requiring email verification.
    This is for documentation purposes and routes that should always be accessible.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    
    return decorated_function