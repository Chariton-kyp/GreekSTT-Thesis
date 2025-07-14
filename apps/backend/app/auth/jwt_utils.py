"""JWT utilities for custom claims and token management."""

from typing import Dict, Any, Optional, List
from flask import current_app, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from app.users.models import User


def create_custom_claims(user: User) -> Dict[str, Any]:
    """Create custom claims for JWT token based on user data.
    
    Args:
        user: User model instance
        
    Returns:
        Dict containing custom claims to be added to JWT
    """
    # Academic package limits - unlimited for research
    package_limits = {
        'minutes_per_month': 999999,
        'max_file_size_mb': 8192,  # 8GB max file size
        'max_files_per_upload': 100,
        'api_calls_per_day': 999999
    }
    
    # Essential user information for frontend
    claims = {
        # User identification
        'email': user.email,
        'username': user.username,
        'full_name': user.full_name,
        'user_type': 'student',
        
        # Academic package info
        'academic_mode': True,
        
        # Academic package limits - unlimited for research
        'package_limits': package_limits,
        
        # User status
        'email_verified': user.primary_email_verified,
    }
    
    return claims


def create_user_tokens(user: User, additional_claims: Optional[Dict[str, Any]] = None, remember_me: bool = False) -> Dict[str, str]:
    """Create access and refresh tokens with custom claims for a user.
    
    Args:
        user: User model instance
        additional_claims: Optional additional claims to include
        
    Returns:
        Dict containing access_token and refresh_token
    """
    # Create base custom claims
    custom_claims = create_custom_claims(user)
    
    # Add any additional claims
    if additional_claims:
        custom_claims.update(additional_claims)
    
    # Set different expiration for remember_me
    from datetime import timedelta
    if remember_me:
        access_expires = timedelta(days=7)   # 7 days for remember_me (more secure)
        refresh_expires = timedelta(days=90)  # 90 days for refresh token (reduced)
    else:
        access_expires = timedelta(minutes=15)  # 15 minutes (more secure)
        refresh_expires = timedelta(days=7)     # 7 days (more secure)
    
    # Create tokens with custom claims and expiration
    access_token = create_access_token(
        identity=user.id,
        additional_claims=custom_claims,
        expires_delta=access_expires
    )
    
    # For refresh token, include minimal claims to keep it small
    refresh_claims = {
        'email': user.email,
        'username': user.username,
        'academic_mode': True,
        'user_type': 'student'
    }
    
    refresh_token = create_refresh_token(
        identity=user.id,
        additional_claims=refresh_claims,
        expires_delta=refresh_expires
    )
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }


def refresh_user_token(user_id: int) -> str:
    """Create a new access token with fresh user data for token refresh.
    
    Args:
        user_id: User ID from the refresh token
        
    Returns:
        New access token with updated custom claims
        
    Raises:
        ValueError: If user not found or inactive
    """
    # Get fresh user data
    user = User.query.filter_by(id=user_id, is_active=True, is_deleted=False).first()
    if not user:
        raise ValueError("User not found or inactive")
    
    # Create new access token with fresh claims
    custom_claims = create_custom_claims(user)
    
    return create_access_token(
        identity=user.id,
        additional_claims=custom_claims
    )

def get_user_package_from_token() -> str:
    """Extract user academic mode from current JWT token.
    
    Returns:
        Always returns 'academic' for research platform
        
    Note:
        This function should be called within a JWT-required context
    """
    from flask_jwt_extended import get_jwt
    
    try:
        jwt_claims = get_jwt()
        return 'academic' if jwt_claims.get('academic_mode', True) else 'academic'
    except Exception:
        return 'academic'

def create_auth_response(user: User, additional_claims: Optional[Dict[str, Any]] = None, remember_me: bool = False) -> Dict[str, Any]:
    """Create a consistent authentication response with tokens and user data.
    
    Args:
        user: User model instance
        additional_claims: Optional additional claims for JWT
        
    Returns:
        Dict containing tokens and user information
    """
    # Create tokens with remember_me support
    tokens = create_user_tokens(user, additional_claims, remember_me)
    
    # Return consistent response
    return {
        'access_token': tokens['access_token'],
        'refresh_token': tokens['refresh_token'],
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'academic_mode': True,
            'email_verified': user.primary_email_verified,
            'organization': user.organization,
            'phone': user.phone
        }
    }

def validate_session_from_token() -> bool:
    """Validate session from JWT token claims.
    
    Returns:
        True if session is valid, False otherwise
        
    Note:
        This function should be called within a JWT-required context
    """
    try:
        # Import here to avoid circular imports
        from app.sessions.services import session_service
        
        jwt_claims = get_jwt()
        session_id = jwt_claims.get('session_id')
        user_id = get_jwt_identity()
        
        if not session_id or not user_id:
            # No session tracking for this token
            return True
        
        # Get request information
        ip_address = request.remote_addr or '127.0.0.1'
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # Validate session
        session = session_service.validate_session(
            session_id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            update_activity=True
        )
        
        return session is not None
        
    except Exception as e:
        current_app.logger.error(f"Session validation error: {str(e)}")
        return False


def get_session_id_from_token() -> Optional[str]:
    """Extract session ID from current JWT token.
    
    Returns:
        Session ID string or None if not present
        
    Note:
        This function should be called within a JWT-required context
    """
    try:
        jwt_claims = get_jwt()
        return jwt_claims.get('session_id')
    except Exception:
        return None