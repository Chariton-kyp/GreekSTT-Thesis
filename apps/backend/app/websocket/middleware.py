"""WebSocket middleware for handling upgrade issues."""

import logging
from flask import request
from werkzeug.exceptions import BadRequest

logger = logging.getLogger(__name__)


class WebSocketMiddleware:
    """Middleware to handle WebSocket upgrade issues during page refresh."""
    
    def __init__(self, app):
        self.app = app
        self.wsgi_app = app.wsgi_app
        app.wsgi_app = self
    
    def __call__(self, environ, start_response):
        """Handle WebSocket upgrade requests properly."""
        try:
            # Check if this is a WebSocket upgrade request
            if environ.get('HTTP_UPGRADE', '').lower() == 'websocket':
                # Check for Socket.IO specific paths
                path = environ.get('PATH_INFO', '')
                if '/socket.io/' in path:
                    logger.debug(f"WebSocket upgrade request detected for path: {path}")
                    
                    # Ensure proper headers are set for WebSocket upgrade
                    if 'HTTP_SEC_WEBSOCKET_KEY' not in environ:
                        logger.warning("WebSocket upgrade missing Sec-WebSocket-Key header")
                    
                    # Let the request through to the WebSocket handler
                    return self.wsgi_app(environ, start_response)
            
            # Normal HTTP request
            return self.wsgi_app(environ, start_response)
            
        except Exception as e:
            logger.error(f"WebSocket middleware error: {str(e)}")
            # Let the error propagate so it can be handled properly
            raise