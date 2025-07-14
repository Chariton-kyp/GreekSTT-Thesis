"""Simple security middleware for thesis project."""

import logging
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)


def security_headers(response):
    """Add basic security headers to response."""
    # Security headers for thesis demo
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Simple Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "font-src 'self'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' ws: wss:; "
        "frame-src 'self'; "
        "object-src 'none';"
    )
    response.headers['Content-Security-Policy'] = csp
    
    return response


def init_security_middleware(app):
    """Initialize basic security middleware for Flask app."""
    
    @app.before_request
    def before_request():
        """Simple request logging."""
        if current_app.config.get('DEBUG', False):
            logger.debug(f"Request: {request.method} {request.path}")
    
    @app.after_request
    def after_request(response):
        """Add security headers to all responses."""
        return security_headers(response)
    
    @app.errorhandler(413)
    def request_too_large(error):
        return jsonify({
            'error': 'Request too large',
            'message': 'The request payload is too large.'
        }), 413
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad request',
            'message': 'The request could not be understood by the server.'
        }), 400