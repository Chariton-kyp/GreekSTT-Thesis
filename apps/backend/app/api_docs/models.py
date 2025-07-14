"""API models for documentation."""

from flask_restx import fields
from app.extensions import api

# Authentication models
login_model = api.model('Login', {
    'email': fields.String(required=True, description='User email address', example='user@example.com'),
    'password': fields.String(required=True, description='User password', example='securepassword123')
})

register_model = api.model('Register', {
    'email': fields.String(required=True, description='User email address', example='user@example.com'),
    'username': fields.String(required=True, description='Unique username', example='johndoe'),
    'password': fields.String(required=True, description='User password (min 5 characters)', example='pass1'),
    'first_name': fields.String(required=True, description='User first name', example='John'),
    'last_name': fields.String(required=True, description='User last name', example='Doe'),
    'sector': fields.String(description='Professional sector', example='academic', enum=['academic', 'legal', 'business', 'general'])
})

user_response_model = api.model('UserResponse', {
    'id': fields.Integer(description='User ID', example=1),
    'email': fields.String(description='User email', example='user@example.com'),
    'username': fields.String(description='Username', example='johndoe'),
    'first_name': fields.String(description='First name', example='John'),
    'last_name': fields.String(description='Last name', example='Doe'),
    'sector': fields.String(description='Professional sector', example='academic'),
    'created_at': fields.DateTime(description='Account creation date'),
    'email_verified': fields.Boolean(description='Email verification status', example=True)
})

token_response_model = api.model('TokenResponse', {
    'access_token': fields.String(description='JWT access token'),
    'refresh_token': fields.String(description='JWT refresh token'),
    'user': fields.Nested(user_response_model, description='User information')
})

# Audio models
audio_upload_model = api.model('AudioUpload', {
    'file': fields.String(required=True, description='Audio file (multipart/form-data)', example='audio.wav'),
    'title': fields.String(description='Audio title', example='Meeting Recording'),
    'description': fields.String(description='Audio description', example='Weekly team meeting'),
    'sector': fields.String(description='Target sector for transcription', example='business')
})

audio_response_model = api.model('AudioResponse', {
    'id': fields.Integer(description='Audio file ID', example=1),
    'title': fields.String(description='Audio title', example='Meeting Recording'),
    'filename': fields.String(description='Original filename', example='meeting.wav'),
    'file_size': fields.Integer(description='File size in bytes', example=1048576),
    'duration': fields.Float(description='Duration in seconds', example=120.5),
    'format': fields.String(description='Audio format', example='wav'),
    'status': fields.String(description='Processing status', example='uploaded', enum=['uploaded', 'processing', 'completed', 'failed']),
    'upload_date': fields.DateTime(description='Upload timestamp'),
    'user_id': fields.Integer(description='Owner user ID', example=1)
})

# Transcription models
transcription_request_model = api.model('TranscriptionRequest', {
    'audio_id': fields.Integer(required=True, description='Audio file ID', example=1),
    'language': fields.String(description='Transcription language', example='el', default='el'),
    'options': fields.Raw(description='Additional transcription options', example={
        'enable_punctuation': True,
        'enable_diarization': False,
        'confidence_threshold': 0.8
    })
})

transcription_response_model = api.model('TranscriptionResponse', {
    'id': fields.Integer(description='Transcription ID', example=1),
    'audio_id': fields.Integer(description='Source audio ID', example=1),
    'text': fields.String(description='Transcribed text', example='Καλησπέρα, πώς είστε σήμερα;'),
    'confidence': fields.Float(description='Overall confidence score', example=0.95),
    'status': fields.String(description='Transcription status', example='completed', 
                          enum=['pending', 'processing', 'completed', 'failed']),
    'language': fields.String(description='Detected/used language', example='el'),
    'duration': fields.Float(description='Processing duration in seconds', example=30.2),
    'word_count': fields.Integer(description='Number of words', example=156),
    'segments': fields.List(fields.Raw, description='Timestamped segments'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'completed_at': fields.DateTime(description='Completion timestamp')
})

# Template models removed - academic version has no template system

# Error models
error_model = api.model('Error', {
    'error': fields.String(description='Error message', example='Invalid credentials'),
    'code': fields.String(description='Error code', example='AUTH_001'),
    'details': fields.Raw(description='Additional error details')
})

success_model = api.model('Success', {
    'message': fields.String(description='Success message', example='Operation completed successfully'),
    'data': fields.Raw(description='Response data')
})

# Health check model
health_model = api.model('Health', {
    'status': fields.String(description='Service status', example='healthy'),
    'service': fields.String(description='Service name', example='greekstt-research-backend'),
    'version': fields.String(description='API version', example='1.0.0'),
    'timestamp': fields.DateTime(description='Health check timestamp'),
    'uptime': fields.String(description='Service uptime', example='2d 4h 30m'),
    'database': fields.String(description='Database status', example='connected'),
    'redis': fields.String(description='Redis status', example='connected'),
    'ai_service': fields.String(description='AI service status', example='available')
})