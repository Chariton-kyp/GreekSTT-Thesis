"""Common decorators for the application."""

from functools import wraps
from flask import jsonify

def validate_request(schema_class):
    """Decorator to validate request data with marshmallow schema."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request
            schema = schema_class()
            
            # Get data from request
            data = request.get_json() if request.is_json else {}
            
            # Validate data
            errors = schema.validate(data)
            if errors:
                return jsonify({'error': 'Validation failed', 'details': errors}), 400
            
            # Load validated data
            kwargs['validated_data'] = schema.load(data)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def async_task(f):
    """Decorator to run a function as an async task using Celery."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.common.tasks import run_async_task
        task = run_async_task.delay(f.__name__, *args, **kwargs)
        return jsonify({
            'message': 'Task started',
            'task_id': task.id
        }), 202
    return decorated_function


def handle_file_upload_errors(f):
    """Decorator to handle common file upload errors."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request
        from app.common.responses import error_response, validation_error_response
        
        try:
            # Check if request has file part
            if 'audio' not in request.files:
                return validation_error_response({'audio': ['Audio file is required']})
            
            file = request.files['audio']
            
            # Check if file is selected
            if file.filename == '':
                return validation_error_response({'audio': ['No file selected']})
            
            # Check file size (basic check)
            if hasattr(file, 'content_length') and file.content_length:
                max_size = 8 * 1024 * 1024 * 1024  # 8GB for academic use
                if file.content_length > max_size:
                    return error_response(
                        message_key='FILE_TOO_LARGE_ACADEMIC',
                        error_code='FILE_SIZE_EXCEEDED'
                    )
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return error_response(
                message_key='FILE_UPLOAD_ERROR',
                error_code='UPLOAD_FAILED'
            )
            
    return decorated_function