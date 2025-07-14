"""Model comparison database models."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Float, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.extensions import db
from app.common.models import TimestampMixin


class ModelComparison(db.Model, TimestampMixin):
    """Model for storing model comparison results."""
    
    __tablename__ = 'model_comparisons'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    audio_file_id = Column(Integer, ForeignKey('audio_files.id'), nullable=False)
    
    # Transcription results
    whisper_transcription_id = Column(Integer, ForeignKey('transcriptions.id'))
    wav2vec_transcription_id = Column(Integer, ForeignKey('transcriptions.id'))
    
    # Comparison metrics
    whisper_wer = Column(Float)
    wav2vec_wer = Column(Float)
    whisper_processing_time = Column(Float)
    wav2vec_processing_time = Column(Float)
    
    # Analysis results
    comparison_summary = Column(Text)
    performance_metrics = Column(JSON)
    academic_insights = Column(JSON)
    
    # Relationships
    user = relationship('User', backref='model_comparisons')
    audio_file = relationship('AudioFile', backref='model_comparisons')
    whisper_transcription = relationship('Transcription', foreign_keys=[whisper_transcription_id])
    wav2vec_transcription = relationship('Transcription', foreign_keys=[wav2vec_transcription_id])