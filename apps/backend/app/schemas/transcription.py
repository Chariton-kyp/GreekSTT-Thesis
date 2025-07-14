"""Transcription schemas for request validation."""

from marshmallow import Schema, fields, validate


class CreateTranscriptionSchema(Schema):
    """Schema for creating new transcriptions."""
    audio_file_url = fields.Str(required=False, validate=validate.Length(max=500))
    audio_file_path = fields.Str(required=False, validate=validate.Length(max=500))
    model_type = fields.Str(required=False, validate=validate.OneOf(['whisper', 'wav2vec2', 'comparison']))
    language = fields.Str(required=False, validate=validate.OneOf(['el', 'en', 'auto']))
    custom_vocabulary = fields.List(fields.Str(), required=False)
    
    
class UpdateTranscriptionTextSchema(Schema):
    """Schema for updating transcription text."""
    transcription_text = fields.Str(required=True, validate=validate.Length(min=1, max=10000))
    confidence_score = fields.Float(required=False, validate=validate.Range(min=0.0, max=1.0))
    manual_correction = fields.Bool(required=False)