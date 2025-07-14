import time
import uuid
import logging
from flask import request, g, current_app, session
from functools import wraps
from typing import Optional, Dict, Any
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    """
    Comprehensive request logging middleware for production monitoring and debugging.
    
    Features:
    - Request/response correlation with unique request IDs
    - Performance monitoring with response times
    - User context tracking for authenticated requests
    - Detailed request/response logging for debugging
    - Structured logging format for production monitoring
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app."""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_appcontext(self._teardown_request)
    
    def _before_request(self):
        """Log request start and set up request context."""
        # Generate unique request ID for correlation
        g.request_id = str(uuid.uuid4())[:8]
        g.start_time = time.time()
        
        # Set up session correlation ID for user journey tracking
        self._setup_session_correlation()
        
        # Get user context if authenticated
        user_info = self._get_user_context()
        
        # Log request details
        self._log_request_start(user_info)
    
    def _after_request(self, response):
        """Log request completion with performance metrics."""
        duration = time.time() - getattr(g, 'start_time', time.time())
        user_info = self._get_user_context()
        
        self._log_request_end(response, duration, user_info)
        
        # Add request ID to response headers for debugging
        response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
        
        return response
    
    def _teardown_request(self, exception):
        """Log any unhandled exceptions and clean up correlation context."""
        if exception:
            try:
                duration = time.time() - getattr(g, 'start_time', time.time())
                user_info = self._get_user_context()
                
                # Check if we have request context
                try:
                    method = request.method
                    path = request.path
                except RuntimeError:
                    # No request context available
                    method = 'unknown'
                    path = 'unknown'
                
                logger.error(
                    f"Request failed | "
                    f"request_id={getattr(g, 'request_id', 'unknown')} | "
                    f"session_id={getattr(g, 'session_correlation_id', 'unknown')} | "
                    f"session_req={getattr(g, 'session_request_count', 0)} | "
                    f"method={method} | "
                    f"path={path} | "
                    f"user_id={user_info.get('user_id', 'anonymous')} | "
                    f"duration={duration:.3f}s | "
                    f"exception={str(exception)}"
                )
            except Exception as log_error:
                # Fallback logging if everything fails
                logger.error(f"Exception during teardown logging: {log_error} | Original exception: {exception}")
        
        # Clean up correlation logger cache
        try:
            from app.utils.correlation_logger import get_correlation_logger
            correlation_logger = get_correlation_logger('middleware')
            correlation_logger.clear_cache()
        except Exception:
            pass  # Ignore cache cleanup errors
    
    def _setup_session_correlation(self):
        """Set up session correlation ID for tracking user journeys."""
        try:
            # Check if we have a session correlation ID
            if 'session_correlation_id' not in session:
                # Create new session correlation ID
                session['session_correlation_id'] = str(uuid.uuid4())
                session['session_start_time'] = datetime.utcnow().isoformat()
                session['request_count'] = 0
                
                # Log new session start
                logger.info(
                    f"New session started | "
                    f"session_id={session['session_correlation_id']} | "
                    f"ip={request.remote_addr} | "
                    f"user_agent={request.headers.get('User-Agent', 'unknown')[:100]}"
                )
            
            # Increment request counter for this session
            session['request_count'] = session.get('request_count', 0) + 1
            
            # Store in request context for easy access
            g.session_correlation_id = session['session_correlation_id']
            g.session_request_count = session['request_count']
            
        except Exception as e:
            # Fallback if session handling fails
            logger.warning(f"Session correlation setup failed: {e}")
            g.session_correlation_id = 'session_error'
            g.session_request_count = 0
    
    def _get_user_context(self) -> Dict[str, Any]:
        """Extract user context from JWT token if available."""
        try:
            from flask_jwt_extended import get_jwt_identity, get_jwt
            
            # Try to get user from JWT
            user_id = get_jwt_identity()
            jwt_claims = get_jwt()
            
            if user_id and jwt_claims:
                return {
                    'user_id': user_id,
                    'email': jwt_claims.get('email', 'unknown'),
                    'user_type': jwt_claims.get('user_type', 'student'),
                    'verified': jwt_claims.get('email_verified', False)
                }
        except Exception:
            # No JWT or invalid token
            pass
        
        return {'user_id': 'anonymous'}
    
    def _log_request_start(self, user_info: Dict[str, Any]):
        """Log request start with context."""
        # Get request size if available
        content_length = request.content_length or 0
        
        # Log based on environment
        if current_app.debug:
            # Detailed logging for development
            logger.info(
                f"Request started | "
                f"request_id={getattr(g, 'request_id', 'unknown')} | "
                f"session_id={getattr(g, 'session_correlation_id', 'unknown')} | "
                f"session_req={getattr(g, 'session_request_count', 0)} | "
                f"method={request.method} | "
                f"path={request.path} | "
                f"remote_addr={request.remote_addr} | "
                f"user_agent={request.headers.get('User-Agent', 'unknown')[:100]} | "
                f"user_id={user_info.get('user_id', 'anonymous')} | "
                f"content_length={content_length} | "
                f"query_params={dict(request.args)}"
            )
        else:
            # Concise logging for production
            logger.info(
                f"Request | "
                f"id={getattr(g, 'request_id', 'unknown')} | "
                f"session={getattr(g, 'session_correlation_id', 'unknown')[:8]} | "
                f"req#{getattr(g, 'session_request_count', 0)} | "
                f"{request.method} {request.path} | "
                f"user={user_info.get('user_id', 'anon')} | "
                f"ip={request.remote_addr}"
            )
    
    def _log_request_end(self, response, duration: float, user_info: Dict[str, Any]):
        """Log request completion with performance metrics."""
        status_code = response.status_code
        # Handle different response types safely
        try:
            response_size = len(response.get_data()) if hasattr(response, 'get_data') else 0
        except (RuntimeError, AttributeError):
            # Handle direct passthrough mode or other response types
            response_size = 0
        
        # Determine log level based on status code
        if status_code >= 500:
            log_level = logger.error
        elif status_code >= 400:
            log_level = logger.warning
        else:
            log_level = logger.info
        
        if current_app.debug:
            # Detailed logging for development
            log_level(
                f"Request completed | "
                f"request_id={getattr(g, 'request_id', 'unknown')} | "
                f"session_id={getattr(g, 'session_correlation_id', 'unknown')} | "
                f"session_req={getattr(g, 'session_request_count', 0)} | "
                f"method={request.method} | "
                f"path={request.path} | "
                f"status={status_code} | "
                f"duration={duration:.3f}s | "
                f"user_id={user_info.get('user_id', 'anonymous')} | "
                f"response_size={response_size} | "
                f"content_type={response.content_type}"
            )
        else:
            # Concise logging for production
            log_level(
                f"Response | "
                f"id={getattr(g, 'request_id', 'unknown')} | "
                f"session={getattr(g, 'session_correlation_id', 'unknown')[:8]} | "
                f"req#{getattr(g, 'session_request_count', 0)} | "
                f"{request.method} {request.path} | "
                f"status={status_code} | "
                f"duration={duration:.3f}s | "
                f"user={user_info.get('user_id', 'anon')}"
            )


def log_business_operation(operation: str, details: Optional[Dict[str, Any]] = None):
    """
    Decorator for logging business operations with user context.
    
    Args:
        operation: Name of the business operation (e.g., 'user_registration', 'file_upload')
        details: Additional operation-specific details to log
    
    Usage:
        @log_business_operation('user_registration', {'method': 'email'})
        def register_user(...):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request_id = getattr(g, 'request_id', 'unknown')
            start_time = time.time()
            
            # Get user context
            try:
                from flask_jwt_extended import get_jwt_identity, get_jwt
                user_id = get_jwt_identity() or 'anonymous'
                jwt_claims = get_jwt() or {}
                user_email = jwt_claims.get('email', 'unknown')
            except Exception:
                user_id = 'anonymous'
                user_email = 'unknown'
            
            # Log operation start
            session_id = getattr(g, 'session_correlation_id', 'unknown')
            session_req = getattr(g, 'session_request_count', 0)
            
            logger.info(
                f"Operation started | "
                f"operation={operation} | "
                f"request_id={request_id} | "
                f"session_id={session_id} | "
                f"session_req={session_req} | "
                f"user_id={user_id} | "
                f"user_email={user_email} | "
                f"details={json.dumps(details or {}, default=str, ensure_ascii=False)}"
            )
            
            try:
                # Execute the operation
                result = func(*args, **kwargs)
                
                # Log successful completion
                duration = time.time() - start_time
                logger.info(
                    f"Operation completed | "
                    f"operation={operation} | "
                    f"request_id={request_id} | "
                    f"session_id={session_id} | "
                    f"session_req={session_req} | "
                    f"user_id={user_id} | "
                    f"duration={duration:.3f}s | "
                    f"status=success"
                )
                
                return result
                
            except Exception as e:
                # Log operation failure
                duration = time.time() - start_time
                logger.error(
                    f"Operation failed | "
                    f"operation={operation} | "
                    f"request_id={request_id} | "
                    f"session_id={session_id} | "
                    f"session_req={session_req} | "
                    f"user_id={user_id} | "
                    f"duration={duration:.3f}s | "
                    f"status=error | "
                    f"error={str(e)}"
                )
                raise
        
        return wrapper
    return decorator


def log_external_service_call(service_name: str, endpoint: str):
    """
    Decorator for logging external service calls with performance monitoring.
    
    Args:
        service_name: Name of the external service (e.g., 'ai_service', 'email_service')
        endpoint: The endpoint being called
    
    Usage:
        @log_external_service_call('ai_service', '/transcribe')
        def call_ai_service(...):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request_id = getattr(g, 'request_id', 'unknown')
            session_id = getattr(g, 'session_correlation_id', 'unknown')
            session_req = getattr(g, 'session_request_count', 0)
            start_time = time.time()
            
            logger.info(
                f"External service call | "
                f"service={service_name} | "
                f"endpoint={endpoint} | "
                f"request_id={request_id} | "
                f"session_id={session_id} | "
                f"session_req={session_req} | "
                f"status=started"
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"External service call | "
                    f"service={service_name} | "
                    f"endpoint={endpoint} | "
                    f"request_id={request_id} | "
                    f"session_id={session_id} | "
                    f"session_req={session_req} | "
                    f"duration={duration:.3f}s | "
                    f"status=success"
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"External service call | "
                    f"service={service_name} | "
                    f"endpoint={endpoint} | "
                    f"request_id={request_id} | "
                    f"session_id={session_id} | "
                    f"session_req={session_req} | "
                    f"duration={duration:.3f}s | "
                    f"status=error | "
                    f"error={str(e)}"
                )
                raise
        
        return wrapper
    return decorator


def log_sensitive_access(operation: str, resource_id: Optional[str] = None):
    """
    Decorator for logging access to sensitive operations with enhanced security auditing.
    
    Args:
        operation: Name of the sensitive operation (e.g., 'model_comparison', 'transcription_export')
        resource_id: ID of the resource being accessed
    
    Usage:
        @log_sensitive_access('model_comparison', 'transcription_123')
        def analyze_transcription(...):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request_id = getattr(g, 'request_id', 'unknown')
            start_time = time.time()
            
            # Get user context
            try:
                from flask_jwt_extended import get_jwt_identity, get_jwt
                user_id = get_jwt_identity() or 'anonymous'
                jwt_claims = get_jwt() or {}
                user_email = jwt_claims.get('email', 'unknown')
                user_type = jwt_claims.get('user_type', 'student')
            except Exception:
                user_id = 'anonymous'
                user_email = 'unknown'
                user_type = 'student'
            
            # Log sensitive operation access
            session_id = getattr(g, 'session_correlation_id', 'unknown')
            session_req = getattr(g, 'session_request_count', 0)
            
            logger.warning(
                f"SENSITIVE ACCESS  < /dev/null |  "
                f"operation={operation} | "
                f"resource_id={resource_id or 'N/A'} | "
                f"request_id={request_id} | "
                f"session_id={session_id} | "
                f"session_req={session_req} | "
                f"user_id={user_id} | "
                f"user_email={user_email} | "
                f"user_type={user_type} | "
                f"ip={request.remote_addr} | "
                f"user_agent={request.headers.get('User-Agent', 'unknown')[:100]} | "
                f"status=started"
            )
            
            try:
                # Execute the operation
                result = func(*args, **kwargs)
                
                # Log successful completion
                duration = time.time() - start_time
                logger.warning(
                    f"SENSITIVE ACCESS COMPLETED | "
                    f"operation={operation} | "
                    f"resource_id={resource_id or 'N/A'} | "
                    f"request_id={request_id} | "
                    f"session_id={session_id} | "
                    f"user_id={user_id} | "
                    f"duration={duration:.3f}s | "
                    f"status=success"
                )
                
                return result
                
            except Exception as e:
                # Log operation failure with high priority
                duration = time.time() - start_time
                logger.error(
                    f"SENSITIVE ACCESS FAILED | "
                    f"operation={operation} | "
                    f"resource_id={resource_id or 'N/A'} | "
                    f"request_id={request_id} | "
                    f"session_id={session_id} | "
                    f"user_id={user_id} | "
                    f"duration={duration:.3f}s | "
                    f"status=error | "
                    f"error={str(e)}"
                )
                raise
        
        return wrapper
    return decorator
