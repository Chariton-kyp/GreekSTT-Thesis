"""Application error handlers with unified message system."""

from flask import jsonify, current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import ValidationError
try:
    from flask_jwt_extended.exceptions import (
        NoAuthorizationError, InvalidHeaderError, 
        ExpiredSignatureError, DecodeError, InvalidTokenError,
        RevokedTokenError, FreshTokenRequired, UserLookupError
    )
except ImportError:
    InvalidHeaderError = None
    ExpiredSignatureError = None
    DecodeError = None
    InvalidTokenError = None
    RevokedTokenError = None
    FreshTokenRequired = None
    UserLookupError = None
from app.common.responses import validation_error_response, error_response, auth_error_response
import logging

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register error handlers for the application."""
    if NoAuthorizationError:
        @app.errorhandler(NoAuthorizationError)
        def handle_no_authorization_error(e):
            return auth_error_response(
                message_key='AUTHORIZATION_REQUIRED',
                error_code='MISSING_AUTHORIZATION_HEADER',
                status_code=401
            )
    
    if InvalidHeaderError:
        @app.errorhandler(InvalidHeaderError)
        def handle_invalid_header_error(e):
            return auth_error_response(
                message_key='INVALID_AUTHORIZATION_HEADER',
                error_code='INVALID_AUTHORIZATION_HEADER', 
                status_code=401
            )
    
    if ExpiredSignatureError:
        @app.errorhandler(ExpiredSignatureError)
        def handle_expired_token_error(e):
            """Handle expired JWT token."""
            return auth_error_response(
                message_key='TOKEN_EXPIRED',
                error_code='TOKEN_EXPIRED',
                status_code=401
            )
    
    if DecodeError:
        @app.errorhandler(DecodeError)
        def handle_decode_error(e):
            """Handle JWT decode errors."""
            return auth_error_response(
                message_key='INVALID_TOKEN',
                error_code='TOKEN_DECODE_ERROR',
                status_code=401
            )
    
    if InvalidTokenError:
        @app.errorhandler(InvalidTokenError)
        def handle_invalid_token_error(e):
            """Handle invalid JWT tokens."""
            return auth_error_response(
                message_key='INVALID_TOKEN',
                error_code='INVALID_TOKEN',
                status_code=401
            )
    
    if RevokedTokenError:
        @app.errorhandler(RevokedTokenError)
        def handle_revoked_token_error(e):
            """Handle revoked JWT tokens."""
            return auth_error_response(
                message_key='TOKEN_REVOKED',
                error_code='TOKEN_REVOKED',
                status_code=401
            )
    
    if FreshTokenRequired:
        @app.errorhandler(FreshTokenRequired)
        def handle_fresh_token_required_error(e):
            """Handle fresh token required errors."""
            return auth_error_response(
                message_key='SESSION_EXPIRED',
                error_code='FRESH_TOKEN_REQUIRED',
                status_code=401
            )
    
    if UserLookupError:
        @app.errorhandler(UserLookupError)
        def handle_user_lookup_error(e):
            """Handle user lookup errors."""
            return auth_error_response(
                message_key='UNAUTHORIZED',
                error_code='USER_LOOKUP_ERROR',
                status_code=401
            )
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        """Handle marshmallow validation errors."""
        return validation_error_response(e.messages)
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle HTTP exceptions."""
        # Map common HTTP errors to appropriate message types
        message_type = 'error'
        if e.code == 400:
            message_type = 'warning'
        elif e.code in [401, 403]:
            message_type = 'error'
        elif e.code == 404:
            message_type = 'warning'
        elif e.code == 429:
            message_type = 'warning'
        
        return jsonify({
            'success': False,
            'message': e.description or f'HTTP {e.code} Error',
            'message_type': message_type,
            'error_code': f'HTTP_{e.code}'
        }), e.code
    
    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(e):
        """Handle database errors."""
        logger.error(f"Database error: {str(e)}")
        return error_response(
            message='Σφάλμα βάσης δεδομένων. Παρακαλώ δοκιμάστε αργότερα.',
            error_code='DATABASE_ERROR',
            status_code=500
        )
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        """Handle unexpected errors."""
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        
        if app.config.get('DEBUG'):
            return error_response(
                message=f'Εσωτερικό σφάλμα: {str(e)}',
                error_code='INTERNAL_SERVER_ERROR',
                status_code=500
            )
        
        return error_response(
            message='Εσωτερικό σφάλμα διακομιστή. Παρακαλώ δοκιμάστε αργότερα.',
            error_code='INTERNAL_SERVER_ERROR',
            status_code=500
        )