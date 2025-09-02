"""Audio file management API documentation."""

from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required

from app.api_docs import audio_ns
from app.api_docs.models import error_model


@audio_ns.route('')
class AudioListAPI(Resource):
    """Audio file operations."""
    
    @audio_ns.doc('get_audio_files', security='Bearer')
    @audio_ns.marshal_list_with(audio_ns.model('AudioResponse', {
        'id': fields.Integer(description='Audio file ID'),
        'title': fields.String(description='Audio title'),
        'filename': fields.String(description='Original filename'),
        'duration': fields.Float(description='Duration in seconds'),
        'format': fields.String(description='Audio format'),
        'status': fields.String(description='Processing status')
    }), code=200)
    @audio_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def get(self):
        """
        Get user audio files.
        
        Returns list of uploaded audio files with metadata.
        """
        pass  # Documentation only
    
    @audio_ns.doc('upload_audio_file', security='Bearer')
    @audio_ns.expect(audio_ns.model('AudioUpload', {
        'file': fields.String(required=True, description='Audio file'),
        'title': fields.String(description='Audio title')
    }), validate=True)
    @audio_ns.response(201, 'Audio uploaded successfully')
    @audio_ns.response(400, 'Invalid file format', error_model)
    @audio_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def post(self):
        """
        Upload audio file.
        
        Supports multiple formats: MP3, WAV, M4A, FLAC, OGG, WebM.
        """
        pass  # Documentation only


@audio_ns.route('/url')
class AudioURLAPI(Resource):
    """URL-based audio processing."""
    
    @audio_ns.doc('process_audio_url', security='Bearer')
    @audio_ns.expect(audio_ns.model('AudioURL', {
        'url': fields.String(required=True, description='Video/Audio URL'),
        'title': fields.String(description='Custom title')
    }), validate=True)
    @audio_ns.response(201, 'URL processing started')
    @audio_ns.response(400, 'Invalid URL', error_model)
    @audio_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def post(self):
        """
        Process audio from URL.
        
        Downloads audio from YouTube, Facebook, TikTok, Vimeo, etc.
        """
        pass  # Documentation only