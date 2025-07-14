"""Transcription models."""

from datetime import datetime, timezone
from app.extensions import db
from app.common.models import BaseModel
from sqlalchemy.dialects.postgresql import JSONB


class Transcription(BaseModel):
    """Model for audio transcriptions."""
    
    __tablename__ = 'transcriptions'
    
    # Association with audio file
    audio_file_id = db.Column(db.Integer, db.ForeignKey('audio_files.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # User-provided metadata
    title = db.Column(db.String(255), nullable=True)  # User-provided title
    description = db.Column(db.Text, nullable=True)   # User-provided description
    
    # Transcription details
    text = db.Column(db.Text, nullable=True)  # Allow null initially, will be filled after processing
    language = db.Column(db.String(10), default='el')  # el for Greek
    
    # Academic notes (for research purposes)
    academic_notes = db.Column(db.Text, nullable=True)
    
    # Processing information
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Transcription metadata
    duration_seconds = db.Column(db.Float, nullable=True)
    word_count = db.Column(db.Integer, nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)  # Overall confidence 0-1
    
    # AI processing details
    model_used = db.Column(db.String(100), nullable=True)
    processing_metadata = db.Column(JSONB, nullable=True)  # Detailed metrics from AI service
    
    # Model-specific columns for comparison
    whisper_text = db.Column(db.Text, nullable=True)
    whisper_confidence = db.Column(db.Float, nullable=True)
    whisper_processing_time = db.Column(db.Float, nullable=True)
    wav2vec_text = db.Column(db.Text, nullable=True)
    wav2vec_confidence = db.Column(db.Float, nullable=True)
    wav2vec_processing_time = db.Column(db.Float, nullable=True)
    comparison_metrics = db.Column(JSONB, nullable=True)
    
    # WER/CER Evaluation fields for academic research
    ground_truth_text = db.Column(db.Text, nullable=True)  # Human-provided correct transcription
    whisper_wer = db.Column(db.Float, nullable=True)  # Word Error Rate for Whisper
    whisper_cer = db.Column(db.Float, nullable=True)  # Character Error Rate for Whisper 
    wav2vec_wer = db.Column(db.Float, nullable=True)  # Word Error Rate for wav2vec2
    wav2vec_cer = db.Column(db.Float, nullable=True)  # Character Error Rate for wav2vec2
    
    # Evaluation metadata
    evaluation_completed = db.Column(db.Boolean, default=False, nullable=False)
    evaluation_date = db.Column(db.DateTime, nullable=True)
    evaluated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    evaluation_notes = db.Column(db.Text, nullable=True)
    
    # Academic accuracy metrics (calculated from WER/CER)
    academic_accuracy_score = db.Column(db.Float, nullable=True)  # Best accuracy based on WER
    best_performing_model = db.Column(db.String(50), nullable=True)  # 'whisper' or 'wav2vec2'
    
    # Speed comparison metrics
    faster_model = db.Column(db.String(50), nullable=True)  # 'whisper' or 'wav2vec2' based on processing time
    
    # Pre-calculated accuracy fields (100 - WER/CER)
    whisper_accuracy = db.Column(db.Float, nullable=True)        # Word accuracy (100 - WER)
    wav2vec_accuracy = db.Column(db.Float, nullable=True)        # Word accuracy (100 - WER)
    whisper_char_accuracy = db.Column(db.Float, nullable=True)   # Character accuracy (100 - CER)
    wav2vec_char_accuracy = db.Column(db.Float, nullable=True)   # Character accuracy (100 - CER)
    
    # Greek-specific accuracy metrics
    whisper_diacritic_accuracy = db.Column(db.Float, nullable=True)   # Accuracy για τόνους
    wav2vec_diacritic_accuracy = db.Column(db.Float, nullable=True)   
    whisper_diacritic_errors = db.Column(db.Float, nullable=True)     # Pre-calculated diacritic errors
    wav2vec_diacritic_errors = db.Column(db.Float, nullable=True)     # Pre-calculated diacritic errors
    whisper_greek_char_accuracy = db.Column(db.Float, nullable=True)  # Accuracy για ελληνικούς χαρακτήρες
    wav2vec_greek_char_accuracy = db.Column(db.Float, nullable=True)
    
    # Detailed error analysis fields
    whisper_substitutions = db.Column(db.Integer, nullable=True)      # Αριθμός αντικαταστάσεων
    whisper_deletions = db.Column(db.Integer, nullable=True)          # Αριθμός διαγραφών
    whisper_insertions = db.Column(db.Integer, nullable=True)         # Αριθμός εισαγωγών
    wav2vec_substitutions = db.Column(db.Integer, nullable=True)
    wav2vec_deletions = db.Column(db.Integer, nullable=True)
    wav2vec_insertions = db.Column(db.Integer, nullable=True)
    
    # Academic usage tracking (for research metrics only)
    processing_cost_estimate = db.Column(db.Float, default=0)  # Academic cost estimation for research
    
    # Template functionality removed for thesis simplification
    
    def to_dict(self):
        """Convert transcription to dictionary with optimized data structure."""
        data = super().to_dict()
        
        # Determine transcription type
        is_comparison = bool(self.whisper_text and self.wav2vec_text)
        is_whisper_only = bool(self.whisper_text and not self.wav2vec_text)
        is_wav2vec_only = bool(self.wav2vec_text and not self.whisper_text)
        
        # Core data
        data.update({
            'audio_file_id': self.audio_file_id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'text': self.text,
            'language': self.language,
            'academic_notes': self.academic_notes,
            'status': self.status,
            'started_at': self.started_at.replace(tzinfo=timezone.utc).isoformat() if self.started_at else None,
            'completed_at': self.completed_at.replace(tzinfo=timezone.utc).isoformat() if self.completed_at else None,
            'processing_time': self._calculate_processing_time(),
            'error_message': self.error_message,
            'duration_seconds': self.duration_seconds,
            'duration_formatted': self._format_duration(self.duration_seconds) if self.duration_seconds else None,
            'word_count': self.word_count,
            'character_count': len(self.text) if self.text else 0, # Calculate character count from text
            'confidence_score': self.confidence_score,
            'model_used': self.model_used,
            'processing_cost_estimate': self.processing_cost_estimate,
            'metadata': self.processing_metadata or {},
        })
        
        # Model-specific data (only include relevant fields)
        if is_comparison:
            data.update({
                'whisper_text': self.whisper_text,
                'whisper_confidence': self.whisper_confidence,
                'whisper_processing_time': self.whisper_processing_time,
                'wav2vec_text': self.wav2vec_text,
                'wav2vec_confidence': self.wav2vec_confidence,
                'wav2vec_processing_time': self.wav2vec_processing_time,
                'comparison_metrics': self.comparison_metrics or {},
                'faster_model': self.faster_model,
            })
        elif is_whisper_only:
            data.update({
                'whisper_text': self.whisper_text,
                'whisper_confidence': self.whisper_confidence,
                'whisper_processing_time': self.whisper_processing_time,
            })
        elif is_wav2vec_only:
            data.update({
                'wav2vec_text': self.wav2vec_text,
                'wav2vec_confidence': self.wav2vec_confidence,
                'wav2vec_processing_time': self.wav2vec_processing_time,
            })
        
        # WER/CER Evaluation Data (always include if available)
        if self.evaluation_completed or self.ground_truth_text:
            data.update({
                'ground_truth_text': self.ground_truth_text,
                'ground_truth_word_count': len(self.ground_truth_text.split()) if self.ground_truth_text else 0, # Calculate ground truth word count
                'evaluation_completed': self.evaluation_completed,
                'evaluation_date': self.evaluation_date.replace(tzinfo=timezone.utc).isoformat() if self.evaluation_date else None,
                'evaluation_notes': self.evaluation_notes,
                'academic_accuracy_score': self.academic_accuracy_score,
                'best_performing_model': self.best_performing_model,
                'has_evaluation': self.evaluation_completed,
            })
            
            # Include WER/CER metrics only for relevant models
            if is_comparison:
                data.update({
                    'whisper_wer': self.whisper_wer,
                    'whisper_cer': self.whisper_cer,
                    'wav2vec_wer': self.wav2vec_wer,
                    'wav2vec_cer': self.wav2vec_cer,
                    'whisper_accuracy': self.whisper_accuracy,
                    'wav2vec_accuracy': self.wav2vec_accuracy,
                    'whisper_char_accuracy': self.whisper_char_accuracy,
                    'wav2vec_char_accuracy': self.wav2vec_char_accuracy,
                    # Greek-specific metrics
                    'whisper_diacritic_accuracy': self.whisper_diacritic_accuracy,
                    'wav2vec_diacritic_accuracy': self.wav2vec_diacritic_accuracy,
                    'whisper_greek_char_accuracy': self.whisper_greek_char_accuracy,
                    'wav2vec_greek_char_accuracy': self.wav2vec_greek_char_accuracy,
                    # Detailed error analysis
                    'whisper_substitutions': self.whisper_substitutions,
                    'whisper_deletions': self.whisper_deletions,
                    'whisper_insertions': self.whisper_insertions,
                    'whisper_diacritic_errors': self.whisper_diacritic_errors,
                    'wav2vec_substitutions': self.wav2vec_substitutions,
                    'wav2vec_deletions': self.wav2vec_deletions,
                    'wav2vec_insertions': self.wav2vec_insertions,
                    'wav2vec_diacritic_errors': self.wav2vec_diacritic_errors,
                })
            elif is_whisper_only:
                data.update({
                    'whisper_wer': self.whisper_wer,
                    'whisper_cer': self.whisper_cer,
                    'whisper_accuracy': self.whisper_accuracy,
                    'whisper_char_accuracy': self.whisper_char_accuracy,
                    # Greek-specific metrics
                    'whisper_diacritic_accuracy': self.whisper_diacritic_accuracy,
                    'whisper_greek_char_accuracy': self.whisper_greek_char_accuracy,
                    # Detailed error analysis
                    'whisper_substitutions': self.whisper_substitutions,
                    'whisper_deletions': self.whisper_deletions,
                    'whisper_insertions': self.whisper_insertions,
                    'whisper_diacritic_errors': self.whisper_diacritic_errors,
                })
            elif is_wav2vec_only:
                data.update({
                    'wav2vec_wer': self.wav2vec_wer,
                    'wav2vec_cer': self.wav2vec_cer,
                    'wav2vec_accuracy': self.wav2vec_accuracy,
                    'wav2vec_char_accuracy': self.wav2vec_char_accuracy,
                    # Greek-specific metrics
                    'wav2vec_diacritic_accuracy': self.wav2vec_diacritic_accuracy,
                    'wav2vec_greek_char_accuracy': self.wav2vec_greek_char_accuracy,
                    # Detailed error analysis
                    'wav2vec_substitutions': self.wav2vec_substitutions,
                    'wav2vec_deletions': self.wav2vec_deletions,
                    'wav2vec_insertions': self.wav2vec_insertions,
                    'wav2vec_diacritic_errors': self.wav2vec_diacritic_errors,
                })
        else:
            # Minimal evaluation data when no evaluation exists
            data.update({
                'has_evaluation': False,
                'evaluation_completed': False,
            })
        
        
        # Include audio file info if relationship is loaded
        if hasattr(self, 'audio_file'):
            data['audio_file'] = {
                'id': self.audio_file.id,
                'filename': self.audio_file.original_filename,
                'duration': self.audio_file.duration_seconds,
                'file_size': self.audio_file.file_size,
                'file_size_formatted': self.audio_file._format_file_size(self.audio_file.file_size),
                'mime_type': self.audio_file.mime_type
            }
        
        return data
    
    def _calculate_processing_time(self):
        """Calculate processing time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration to human-readable format."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    
    def calculate_faster_model(self):
        """Calculate which model was faster based on processing times."""
        if self.whisper_processing_time is not None and self.wav2vec_processing_time is not None:
            if self.whisper_processing_time < self.wav2vec_processing_time:
                self.faster_model = 'whisper'
            else:
                self.faster_model = 'wav2vec2'
        elif self.whisper_processing_time is not None:
            self.faster_model = 'whisper'
        elif self.wav2vec_processing_time is not None:
            self.faster_model = 'wav2vec2'
        else:
            self.faster_model = None
        
        return self.faster_model
    
    def calculate_wer_cer(self, ground_truth: str, hypothesis: str) -> tuple[float, float]:
        """Calculate Word Error Rate (WER) and Character Error Rate (CER)."""
        from app.core.services.wer_calculator import calculate_wer, calculate_cer
        
        if not ground_truth or not hypothesis:
            return 0.0, 0.0
            
        wer = calculate_wer(ground_truth, hypothesis)
        cer = calculate_cer(ground_truth, hypothesis)
        
        return wer, cer
    
    def evaluate_with_ground_truth(self, ground_truth: str, user_id: int, notes: str = None):
        """Evaluate transcription accuracy against ground truth text using enhanced metrics."""
        from datetime import datetime
        from app.core.services.wer_calculator import AdvancedWERCalculator
        
        self.ground_truth_text = ground_truth
        self.evaluated_by_user_id = user_id
        self.evaluation_date = datetime.utcnow()
        self.evaluation_notes = notes
        
        calculator = AdvancedWERCalculator()
        
        # Calculate detailed metrics for each model if text exists
        if self.whisper_text:
            whisper_metrics = calculator.calculate_detailed_metrics(ground_truth, self.whisper_text)
            
            # Basic WER/CER metrics
            self.whisper_wer = whisper_metrics['wer']
            self.whisper_cer = whisper_metrics['cer']
            
            # Pre-calculated accuracy fields (100 - WER/CER)
            self.whisper_accuracy = whisper_metrics['accuracy']
            self.whisper_char_accuracy = whisper_metrics['char_accuracy']
            
            # Greek-specific accuracy metrics
            self.whisper_diacritic_accuracy = whisper_metrics['diacritic_accuracy']
            self.whisper_diacritic_errors = whisper_metrics['diacritic_errors']
            self.whisper_greek_char_accuracy = whisper_metrics['greek_char_accuracy']
            
            # Detailed error analysis
            self.whisper_substitutions = whisper_metrics['substitutions']
            self.whisper_deletions = whisper_metrics['deletions']
            self.whisper_insertions = whisper_metrics['insertions']
            
        if self.wav2vec_text:
            wav2vec_metrics = calculator.calculate_detailed_metrics(ground_truth, self.wav2vec_text)
            
            # Basic WER/CER metrics
            self.wav2vec_wer = wav2vec_metrics['wer']
            self.wav2vec_cer = wav2vec_metrics['cer']
            
            # Pre-calculated accuracy fields (100 - WER/CER)
            self.wav2vec_accuracy = wav2vec_metrics['accuracy']
            self.wav2vec_char_accuracy = wav2vec_metrics['char_accuracy']
            
            # Greek-specific accuracy metrics
            self.wav2vec_diacritic_accuracy = wav2vec_metrics['diacritic_accuracy']
            self.wav2vec_diacritic_errors = wav2vec_metrics['diacritic_errors']
            self.wav2vec_greek_char_accuracy = wav2vec_metrics['greek_char_accuracy']
            
            # Detailed error analysis
            self.wav2vec_substitutions = wav2vec_metrics['substitutions']
            self.wav2vec_deletions = wav2vec_metrics['deletions']
            self.wav2vec_insertions = wav2vec_metrics['insertions']
        
        # Calculate academic accuracy score and determine best model
        # Use pre-calculated accuracy values instead of recalculating
        whisper_accuracy = self.whisper_accuracy
        wav2vec_accuracy = self.wav2vec_accuracy
        
        if whisper_accuracy is not None and wav2vec_accuracy is not None:
            # Both models evaluated - compare them
            if whisper_accuracy > wav2vec_accuracy:
                self.academic_accuracy_score = whisper_accuracy
                self.best_performing_model = 'whisper'
            elif wav2vec_accuracy > whisper_accuracy:
                self.academic_accuracy_score = wav2vec_accuracy
                self.best_performing_model = 'wav2vec2'
            else:
                # Tie - both models have identical performance
                self.academic_accuracy_score = whisper_accuracy  # Same as wav2vec_accuracy
                self.best_performing_model = 'tie'
        elif whisper_accuracy is not None:
            # Only Whisper evaluated
            self.academic_accuracy_score = whisper_accuracy
            self.best_performing_model = 'whisper'
        elif wav2vec_accuracy is not None:
            # Only wav2vec2 evaluated
            self.academic_accuracy_score = wav2vec_accuracy
            self.best_performing_model = 'wav2vec2'
        else:
            # No models evaluated
            self.academic_accuracy_score = None
            self.best_performing_model = None
        
        self.evaluation_completed = True
        
        # Commit to database
        from app.extensions import db
        db.session.commit()
        
        # Return enhanced evaluation results with all new metrics
        result = {
            'whisper_wer': self.whisper_wer,
            'whisper_cer': self.whisper_cer,
            'wav2vec_wer': self.wav2vec_wer,
            'wav2vec_cer': self.wav2vec_cer,
            'academic_accuracy': self.academic_accuracy_score,
            'best_model': self.best_performing_model
        }
        
        # Add detailed metrics if available
        if self.whisper_text:
            result.update({
                'whisper_accuracy': whisper_accuracy,
                'whisper_diacritic_accuracy': self.whisper_diacritic_accuracy,
                'whisper_greek_char_accuracy': self.whisper_greek_char_accuracy,
                'whisper_substitutions': self.whisper_substitutions,
                'whisper_deletions': self.whisper_deletions,
                'whisper_insertions': self.whisper_insertions,
            })
        
        if self.wav2vec_text:
            result.update({
                'wav2vec_accuracy': wav2vec_accuracy,
                'wav2vec_diacritic_accuracy': self.wav2vec_diacritic_accuracy,
                'wav2vec_greek_char_accuracy': self.wav2vec_greek_char_accuracy,
                'wav2vec_substitutions': self.wav2vec_substitutions,
                'wav2vec_deletions': self.wav2vec_deletions,
                'wav2vec_insertions': self.wav2vec_insertions,
            })
        
        return result
    
    def __repr__(self):
        return f'<Transcription {self.id} - {self.status}>'


class TranscriptionSegment(BaseModel):
    """Model for transcription segments (for detailed timestamps)."""
    
    __tablename__ = 'transcription_segments'
    
    transcription_id = db.Column(db.Integer, db.ForeignKey('transcriptions.id'), nullable=False)
    
    # Segment details
    start_time = db.Column(db.Float, nullable=False)  # in seconds
    end_time = db.Column(db.Float, nullable=False)
    text = db.Column(db.Text, nullable=False)
    confidence = db.Column(db.Float, nullable=True)
    speaker = db.Column(db.String(50), nullable=True)  # For multi-speaker scenarios
    
    # Relationship with ordered segments
    transcription = db.relationship('Transcription', backref=db.backref('segments', order_by='TranscriptionSegment.start_time'))
    
    def to_dict(self):
        """Convert segment to dictionary."""
        return {
            'id': self.id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'text': self.text,
            'confidence': self.confidence,
            'speaker': self.speaker
        }
    
    def __repr__(self):
        return f'<TranscriptionSegment {self.start_time}-{self.end_time}>'