"""Comprehensive correlation logging for GreekSTT Comparison Platform."""

import logging
import json
from typing import Dict, Any, Optional
from flask import g, request
from flask_jwt_extended import get_jwt_identity, get_jwt
from datetime import datetime


class CorrelationLogger:
    """
    Enhanced logger that automatically includes correlation IDs and user context
    in all log messages.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._context_cache = {}
    
    def _get_correlation_context(self) -> Dict[str, Any]:
        """Get current request correlation context."""
        try:
            # Check cache first to avoid repeated JWT parsing
            request_id = getattr(g, 'request_id', 'unknown')
            if request_id in self._context_cache:
                return self._context_cache[request_id]
            
            context = {
                'request_id': request_id,
                'session_id': getattr(g, 'session_correlation_id', 'unknown'),
                'session_req': getattr(g, 'session_request_count', 0),
                'timestamp': datetime.utcnow().isoformat(),
                'endpoint': getattr(request, 'endpoint', 'unknown'),
                'method': getattr(request, 'method', 'unknown'),
                'path': getattr(request, 'path', 'unknown'),
                'ip': getattr(request, 'remote_addr', 'unknown')
            }
            
            # Add user context if available
            try:
                user_id = get_jwt_identity()
                jwt_claims = get_jwt()
                if user_id and jwt_claims:
                    context.update({
                        'user_id': user_id,
                        'user_email': jwt_claims.get('email', 'unknown'),
                        'user_type': jwt_claims.get('user_type', 'student'),
                        'user_verified': jwt_claims.get('email_verified', False)
                    })
                else:
                    context.update({
                        'user_id': 'anonymous',
                        'user_email': 'unknown',
                        'user_type': 'anonymous',
                        'user_verified': False
                    })
            except Exception:
                context.update({
                    'user_id': 'anonymous',
                    'user_email': 'unknown', 
                    'user_type': 'anonymous',
                    'user_verified': False
                })
            
            # Cache for this request
            self._context_cache[request_id] = context
            return context
            
        except Exception as e:
            # Fallback context if something fails
            return {
                'request_id': 'error',
                'session_id': 'error',
                'session_req': 0,
                'timestamp': datetime.utcnow().isoformat(),
                'endpoint': 'unknown',
                'method': 'unknown',
                'path': 'unknown',
                'ip': 'unknown',
                'user_id': 'unknown',
                'user_email': 'unknown',
                'user_type': 'error',
                'user_verified': False,
                'context_error': str(e)
            }
    
    def _format_correlation_prefix(self, context: Dict[str, Any]) -> str:
        """Format correlation prefix for log messages."""
        return (
            f"[{context['timestamp']}] "
            f"REQ={context['request_id']} | "
            f"SES={context['session_id'][:8]}...{context['session_id'][-4:]} | "
            f"#{context['session_req']:03d} | "
            f"USR={context['user_id']} | "
            f"TYPE={context['user_type']} | "
            f"{context['method']} {context['path']} | "
        )
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log info message with correlation context."""
        context = self._get_correlation_context()
        correlation_prefix = self._format_correlation_prefix(context)
        
        if extra_data:
            extra_str = f" | DATA={json.dumps(extra_data, default=str, ensure_ascii=False)}"
        else:
            extra_str = ""
        
        self.logger.info(f"{correlation_prefix}{message}{extra_str}")
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log warning message with correlation context."""
        context = self._get_correlation_context()
        correlation_prefix = self._format_correlation_prefix(context)
        
        if extra_data:
            extra_str = f" | DATA={json.dumps(extra_data, default=str, ensure_ascii=False)}"
        else:
            extra_str = ""
        
        self.logger.warning(f"{correlation_prefix}{message}{extra_str}")
    
    def error(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log error message with correlation context."""
        context = self._get_correlation_context()
        correlation_prefix = self._format_correlation_prefix(context)
        
        if extra_data:
            extra_str = f" | DATA={json.dumps(extra_data, default=str, ensure_ascii=False)}"
        else:
            extra_str = ""
        
        self.logger.error(f"{correlation_prefix}{message}{extra_str}")
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log debug message with correlation context."""
        context = self._get_correlation_context()
        correlation_prefix = self._format_correlation_prefix(context)
        
        if extra_data:
            extra_str = f" | DATA={json.dumps(extra_data, default=str, ensure_ascii=False)}"
        else:
            extra_str = ""
        
        self.logger.debug(f"{correlation_prefix}{message}{extra_str}")
    
    def user_journey(self, step: str, step_data: Optional[Dict[str, Any]] = None):
        """Log user journey step for complete process tracking."""
        context = self._get_correlation_context()
        
        journey_message = (
            f"USER_JOURNEY | STEP={step} | "
            f"REQ={context['request_id']} | "
            f"SES={context['session_id']} | "
            f"#{context['session_req']:03d} | "
            f"USR={context['user_id']} | "
            f"PATH={context['path']} | "
            f"DATA={json.dumps(step_data or {}, default=str, ensure_ascii=False)}"
        )
        
        self.logger.info(journey_message)
    
    def clear_cache(self):
        """Clear request context cache (called at end of request)."""
        self._context_cache.clear()


# Factory function to create correlation loggers
def get_correlation_logger(name: str) -> CorrelationLogger:
    """Get a correlation logger instance for the given module."""
    return CorrelationLogger(name)


# Convenience functions for quick usage
def log_user_action(action: str, details: Optional[Dict[str, Any]] = None):
    """Quick log user action with correlation."""
    logger = get_correlation_logger('user_action')
    logger.info(f"USER_ACTION: {action}", details)


def log_data_access(resource_type: str, resource_id: Optional[str] = None, 
                   access_type: str = 'read'):
    """Quick log data access with correlation."""
    logger = get_correlation_logger('data_access')
    details = {
        'resource_type': resource_type,
        'resource_id': resource_id,
        'access_type': access_type
    }


def log_business_flow(flow_name: str, step: str, step_data: Optional[Dict[str, Any]] = None):
    """Quick log business flow step with correlation."""
    logger = get_correlation_logger('business_flow')
    logger.user_journey(f"{flow_name}:{step}", step_data)


def log_correlation(correlation_id: str, event: str, level: str, message: str, 
                   extra_data: Optional[Dict[str, Any]] = None):
    """Log with correlation ID for request tracking."""
    logger = get_correlation_logger('correlation')
    
    log_data = {
        'correlation_id': correlation_id,
        'event': event,
        **(extra_data or {})
    }
    
    if level.lower() == 'info':
        logger.info(message, log_data)
    elif level.lower() == 'warning':
        logger.warning(message, log_data)
    elif level.lower() == 'error':
        logger.error(message, log_data)
    else:
        logger.debug(message, log_data)