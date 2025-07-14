"""
Unified message response system for consistent API responses.
All responses use a single 'message' field with 'message_type' to indicate toast type.
Supports multilingual messages (Greek/English) with Greek as default.
"""

from flask import jsonify, request
from typing import Dict, Any, Optional, Union, List
from app.constants.multilingual_messages import (
    get_auth_message, get_validation_message, get_file_message,
    get_transcription_message, get_user_message, get_academic_message,
    get_session_message, get_error_message,
    get_success_message, MultilingualMessages
)


class ApiResponse:
    """Utility class for creating standardized API responses with unified messaging."""
    
    @staticmethod
    def _get_language():
        """Get the current request language, defaulting to Greek."""
        # Check Accept-Language header or use a custom header
        accept_language = request.headers.get('Accept-Language', 'el')
        if accept_language.startswith('en'):
            return 'en'
        return 'el'  # Default to Greek
    
    @staticmethod
    def success(
        message: str = None, 
        data: Any = None, 
        status_code: int = 200,
        message_key: str = None,
        message_category: str = 'SUCCESS_MESSAGES',
        language: str = None,
        **format_kwargs
    ):
        """Create a standardized success response."""
        if not language:
            language = ApiResponse._get_language()
            
        if message_key:
            if message_category == 'AUTH_MESSAGES':
                message = get_auth_message(message_key, language, **format_kwargs)
            elif message_category == 'SUCCESS_MESSAGES':
                message = get_success_message(message_key, language, **format_kwargs)
            elif message_category == 'TRANSCRIPTION_MESSAGES':
                message = get_transcription_message(message_key, language, **format_kwargs)
            elif message_category == 'USER_MESSAGES':
                message = get_user_message(message_key, language, **format_kwargs)
            elif message_category == 'FILE_MESSAGES':
                message = get_file_message(message_key, language, **format_kwargs)
            elif message_category == 'ACADEMIC_MESSAGES':
                message = get_academic_message(message_key, language, **format_kwargs)
            elif message_category == 'SESSION_MESSAGES':
                message = get_session_message(message_key, language, **format_kwargs)
        
        if not message:
            message = get_success_message('OPERATION_SUCCESSFUL', language)
        
        response = {
            'success': True,
            'message': message,
            'message_type': 'success'
        }
        
        if data is not None:
            if isinstance(data, dict):
                response.update(data)
            else:
                response['data'] = data
                
        return jsonify(response), status_code
    
    @staticmethod
    def error(
        message: str = None,
        error_code: str = None,
        status_code: int = 400,
        details: Dict[str, Any] = None,
        message_key: str = None,
        message_category: str = 'ERROR_MESSAGES',
        language: str = None,
        **format_kwargs
    ):
        """Create a standardized error response."""
        if not language:
            language = ApiResponse._get_language()
            
        if message_key:
            if message_category == 'AUTH_MESSAGES':
                message = get_auth_message(message_key, language, **format_kwargs)
            elif message_category == 'ERROR_MESSAGES':
                message = get_error_message(message_key, language, **format_kwargs)
            elif message_category == 'VALIDATION_MESSAGES':
                message = get_validation_message(message_key, language, **format_kwargs)
            elif message_category == 'TRANSCRIPTION_MESSAGES':
                message = get_transcription_message(message_key, language, **format_kwargs)
            elif message_category == 'USER_MESSAGES':
                message = get_user_message(message_key, language, **format_kwargs)
            elif message_category == 'FILE_MESSAGES':
                message = get_file_message(message_key, language, **format_kwargs)
            elif message_category == 'ACADEMIC_MESSAGES':
                message = get_academic_message(message_key, language, **format_kwargs)
        
        if not message:
            message = get_error_message('BAD_REQUEST', language)
        
        response = {
            'success': False,
            'message': message,
            'message_type': 'error'
        }
        
        if error_code:
            response['error_code'] = error_code
            
        if details:
            response.update(details)
            
        return jsonify(response), status_code
    
    @staticmethod
    def warning(
        message: str = None,
        error_code: str = None,
        status_code: int = 400,
        details: Dict[str, Any] = None,
        message_key: str = None,
        message_category: str = 'ERROR_MESSAGES',
        language: str = None,
        **format_kwargs
    ):
        """Create a standardized warning response."""
        if not language:
            language = ApiResponse._get_language()
            
        if message_key:
            if message_category == 'AUTH_MESSAGES':
                message = get_auth_message(message_key, language, **format_kwargs)
            elif message_category == 'ERROR_MESSAGES':
                message = get_error_message(message_key, language, **format_kwargs)
            elif message_category == 'VALIDATION_MESSAGES':
                message = get_validation_message(message_key, language, **format_kwargs)
        
        default_warning = 'Προσοχή απαιτείται' if language == 'el' else 'Attention required'
        
        response = {
            'success': False,
            'message': message or default_warning,
            'message_type': 'warning'
        }
        
        if error_code:
            response['error_code'] = error_code
            
        if details:
            response.update(details)
            
        return jsonify(response), status_code
    
    @staticmethod
    def info(
        message: str = None,
        data: Any = None,
        status_code: int = 200,
        message_key: str = None,
        message_category: str = 'SUCCESS_MESSAGES',
        language: str = None,
        **format_kwargs
    ):
        """Create a standardized info response."""
        if not language:
            language = ApiResponse._get_language()
            
        if message_key:
            if message_category == 'AUTH_MESSAGES':
                message = get_auth_message(message_key, language, **format_kwargs)
            elif message_category == 'SUCCESS_MESSAGES':
                message = get_success_message(message_key, language, **format_kwargs)
        
        default_info = 'Πληροφορία' if language == 'el' else 'Information'
        
        response = {
            'success': True,
            'message': message or default_info,
            'message_type': 'info'
        }
        
        if data is not None:
            if isinstance(data, dict):
                response.update(data)
            else:
                response['data'] = data
                
        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(
        errors: Union[Dict, List, str],
        message: str = None,
        status_code: int = 400,
        language: str = None
    ):
        """Create a standardized validation error response."""
        if not language:
            language = ApiResponse._get_language()
            
        default_message = get_error_message('VALIDATION_ERROR', language)
        
        response = {
            'success': False,
            'message': message or default_message,
            'message_type': 'validation',
            'error_code': 'VALIDATION_ERROR'
        }
        
        if isinstance(errors, dict):
            response['details'] = errors
        elif isinstance(errors, list):
            response['errors'] = errors
        else:
            response['details'] = {'general': [str(errors)]}
            
        return jsonify(response), status_code
    
    @staticmethod
    def verification_error(
        error_code: str,
        attempts_left: int = None,
        remaining_time: int = None,
        status_code: int = 400,
        language: str = None
    ):
        """Create a standardized verification error response."""
        if not language:
            language = ApiResponse._get_language()
            
        # Map error codes to user-friendly messages and determine message type
        error_mappings = {
            'INVALID_CODE': {
                'message_key': 'INVALID_VERIFICATION_CODE',
                'type': 'warning'
            },
            'CODE_EXPIRED': {
                'message_key': 'VERIFICATION_CODE_EXPIRED',
                'type': 'error'
            },
            'MAX_ATTEMPTS_REACHED': {
                'message_key': 'TOO_MANY_VERIFICATION_ATTEMPTS',
                'type': 'error'
            },
            'EXPIRED_OR_MAX_ATTEMPTS': {
                'message_key': 'VERIFICATION_CODE_EXPIRED' if remaining_time == 0 
                              else 'TOO_MANY_VERIFICATION_ATTEMPTS',
                'type': 'error'
            },
            'CODE_NOT_FOUND': {
                'message': 'Δεν βρέθηκε ενεργός κωδικός επιβεβαίωσης. Παρακαλώ ζητήστε νέο κωδικό.' if language == 'el' 
                          else 'No active verification code found. Please request a new code.',
                'type': 'warning'
            },
            'ALREADY_VERIFIED': {
                'message_key': 'EMAIL_ALREADY_VERIFIED',
                'type': 'info'
            },
            'NO_CODE': {
                'message': 'Δεν έχει σταλεί κωδικός επιβεβαίωσης. Παρακαλώ ζητήστε νέο κωδικό.' if language == 'el'
                          else 'No verification code has been sent. Please request a new code.',
                'type': 'warning'
            }
        }
        
        mapping = error_mappings.get(error_code, {
            'message_key': 'INVALID_VERIFICATION_CODE',
            'type': 'error'
        })
        
        # Get the message
        if 'message_key' in mapping:
            message = get_auth_message(mapping['message_key'], language)
        else:
            message = mapping['message']
            
        message_type = mapping['type']
        
        # Add attempts information to message if available
        if error_code == 'INVALID_CODE' and attempts_left is not None and attempts_left > 0:
            if language == 'el':
                message = f"Μη έγκυρος κωδικός επιβεβαίωσης. Απομένουν {attempts_left} προσπάθειες."
            else:
                message = f"Invalid verification code. {attempts_left} attempts remaining."
        
        response = {
            'success': False,
            'message': message,
            'message_type': message_type,
            'error_code': error_code
        }
        
        if attempts_left is not None:
            response['attempts_left'] = attempts_left
            
        if remaining_time is not None:
            response['remaining_time'] = remaining_time
            
        # Set appropriate status code
        if error_code in ['EXPIRED_OR_MAX_ATTEMPTS', 'CODE_EXPIRED', 'MAX_ATTEMPTS_REACHED']:
            status_code = 410  # Gone
        elif error_code in ['CODE_NOT_FOUND', 'NO_CODE']:
            status_code = 404  # Not Found
            
        return jsonify(response), status_code


# Convenience functions for common responses
def success_response(message_key: str = None, data: Any = None, message_category: str = 'SUCCESS_MESSAGES', **kwargs):
    """Shorthand for success response."""
    return ApiResponse.success(message_key=message_key, data=data, message_category=message_category, **kwargs)

def error_response(message_key: str = None, error_code: str = None, message_category: str = 'ERROR_MESSAGES', **kwargs):
    """Shorthand for error response."""
    return ApiResponse.error(message_key=message_key, error_code=error_code, message_category=message_category, **kwargs)

def warning_response(message_key: str = None, error_code: str = None, message_category: str = 'ERROR_MESSAGES', **kwargs):
    """Shorthand for warning response."""
    return ApiResponse.warning(message_key=message_key, error_code=error_code, message_category=message_category, **kwargs)

def info_response(message_key: str = None, data: Any = None, message_category: str = 'SUCCESS_MESSAGES', **kwargs):
    """Shorthand for info response."""
    return ApiResponse.info(message_key=message_key, data=data, message_category=message_category, **kwargs)

def validation_error_response(errors: Union[Dict, List, str], **kwargs):
    """Shorthand for validation error response."""
    return ApiResponse.validation_error(errors=errors, **kwargs)

def verification_error_response(error_code: str, **kwargs):
    """Shorthand for verification error response."""
    return ApiResponse.verification_error(error_code=error_code, **kwargs)

# Specialized shortcuts for different message categories
def auth_success_response(message_key: str, data: Any = None, **kwargs):
    """Auth success response shortcut."""
    return success_response(message_key=message_key, data=data, message_category='AUTH_MESSAGES', **kwargs)

def auth_error_response(message_key: str, error_code: str = None, **kwargs):
    """Auth error response shortcut."""
    return error_response(message_key=message_key, error_code=error_code, message_category='AUTH_MESSAGES', **kwargs)

def transcription_success_response(message_key: str, data: Any = None, **kwargs):
    """Transcription success response shortcut."""
    return success_response(message_key=message_key, data=data, message_category='TRANSCRIPTION_MESSAGES', **kwargs)

def transcription_error_response(message_key: str, error_code: str = None, **kwargs):
    """Transcription error response shortcut."""
    return error_response(message_key=message_key, error_code=error_code, message_category='TRANSCRIPTION_MESSAGES', **kwargs)

def user_success_response(message_key: str, data: Any = None, **kwargs):
    """User success response shortcut."""
    return success_response(message_key=message_key, data=data, message_category='USER_MESSAGES', **kwargs)

def user_error_response(message_key: str, error_code: str = None, **kwargs):
    """User error response shortcut."""
    return error_response(message_key=message_key, error_code=error_code, message_category='USER_MESSAGES', **kwargs)

def file_success_response(message_key: str, data: Any = None, **kwargs):
    """File success response shortcut."""
    return success_response(message_key=message_key, data=data, message_category='FILE_MESSAGES', **kwargs)

def file_error_response(message_key: str, error_code: str = None, **kwargs):
    """File error response shortcut."""
    return error_response(message_key=message_key, error_code=error_code, message_category='FILE_MESSAGES', **kwargs)

def academic_success_response(message_key: str, data: Any = None, **kwargs):
    """Academic success response shortcut."""
    return success_response(message_key=message_key, data=data, message_category='ACADEMIC_MESSAGES', **kwargs)

def academic_error_response(message_key: str, error_code: str = None, **kwargs):
    """Academic error response shortcut."""
    return error_response(message_key=message_key, error_code=error_code, message_category='ACADEMIC_MESSAGES', **kwargs)

# Template response functions removed - academic version has no template system

def session_success_response(message_key: str, data: Any = None, **kwargs):
    """Session success response shortcut."""
    return success_response(message_key=message_key, data=data, message_category='SESSION_MESSAGES', **kwargs)

def session_error_response(message_key: str, error_code: str = None, **kwargs):
    """Session error response shortcut."""
    return error_response(message_key=message_key, error_code=error_code, message_category='SESSION_MESSAGES', **kwargs)