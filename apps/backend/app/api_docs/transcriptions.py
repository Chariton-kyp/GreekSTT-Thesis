"""Transcription API documentation."""

from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required

from app.api_docs import transcription_ns
from app.api_docs.models import error_model


@transcription_ns.route('')
class TranscriptionListAPI(Resource):
    """Transcription operations."""
    
    @transcription_ns.doc('get_transcriptions', security='Bearer')
    @transcription_ns.marshal_list_with(transcription_ns.model('TranscriptionResponse', {
        'id': fields.Integer(description='Transcription ID'),
        'audio_id': fields.Integer(description='Source audio ID'),
        'text': fields.String(description='Transcribed text'),
        'confidence': fields.Float(description='Confidence score'),
        'status': fields.String(description='Processing status'),
        'model': fields.String(description='ASR model used'),
        'language': fields.String(description='Language detected')
    }), code=200)
    @transcription_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def get(self):
        """
        Get user transcriptions.
        
        Returns list of transcriptions with processing status.
        """
        pass  # Documentation only
    
    @transcription_ns.doc('create_transcription', security='Bearer')
    @transcription_ns.expect(transcription_ns.model('TranscriptionRequest', {
        'audio_id': fields.Integer(required=True, description='Audio file ID'),
        'model': fields.String(description='ASR model: whisper (high accuracy, slower) or wav2vec2 (high speed)', 
                              enum=['whisper', 'wav2vec2'], example='whisper'),
        'language': fields.String(description='Language code', default='el', example='el')
    }), validate=True)
    @transcription_ns.response(201, 'Transcription started')
    @transcription_ns.response(400, 'Invalid request', error_model)
    @transcription_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def post(self):
        """
        Create new transcription.
        
        Starts ASR processing for uploaded audio file.
        """
        pass  # Documentation only


@transcription_ns.route('/compare')
class TranscriptionComparisonAPI(Resource):
    """Model comparison."""
    
    @transcription_ns.doc('compare_models', security='Bearer')
    @transcription_ns.expect(transcription_ns.model('ModelComparison', {
        'audio_id': fields.Integer(required=True, description='Audio file ID'),
        'models': fields.List(fields.String, required=True, 
                            description='Models to compare: whisper (~7x realtime, WER ~2.5%), wav2vec2 (~16x realtime)',
                            example=['whisper', 'wav2vec2']),
        'ground_truth': fields.String(description='Ground truth text for WER/CER calculation (optional)',
                                    example='Πώς θα φαντάζονταν την εκατόστη επετειό της μεταπολίτευσης...')
    }), validate=True)
    @transcription_ns.response(200, 'Comparison completed')
    @transcription_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def post(self):
        """
        Compare ASR models for academic research.
        
        Runs transcription with both Whisper and wav2vec2 models for comprehensive comparison.
        
        Research Findings (Real-world Greek Audio - YouTube):
        - **Whisper**: WER 2.5%, CER 1.3%, Accuracy 97.56%, Speed ~7x realtime
        - **wav2vec2**: WER 61.4%, CER 30.9%, Accuracy 38.68%, Speed ~16x realtime
        
        Key Insights:
        - Whisper excels in accuracy for challenging, non-studio Greek audio
        - wav2vec2 optimized for speed but struggles with real-world conditions
        - Significant performance gap demonstrates model specialization trade-offs
        - Tested on authentic YouTube content (not controlled studio recordings)
        """
        pass  # Documentation only