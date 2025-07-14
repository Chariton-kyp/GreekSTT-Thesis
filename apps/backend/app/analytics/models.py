"""
Analytics Models

Advanced analytics models for academic research tracking,
performance monitoring, and language-specific metrics.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy import func

from ..extensions import db


class UserAnalytics(db.Model):
    """
    Daily user analytics aggregation.
    
    Stores per-user daily metrics for academic research tracking
    and performance monitoring.
    """
    __tablename__ = 'user_analytics'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    
    # Transcription Metrics
    transcriptions_count = Column(Integer, nullable=False, default=0)
    total_audio_duration = Column(Float, nullable=False, default=0.0)
    total_processing_time = Column(Float, nullable=False, default=0.0)
    average_accuracy_score = Column(Float, nullable=True)
    total_words_transcribed = Column(Integer, nullable=False, default=0)
    
    # Model Usage
    whisper_usage_count = Column(Integer, nullable=False, default=0)
    wav2vec_usage_count = Column(Integer, nullable=False, default=0)
    comparison_usage_count = Column(Integer, nullable=False, default=0)
    
    # Voice Notes Metrics
    voice_notes_created = Column(Integer, nullable=False, default=0)
    voice_notes_transcribed = Column(Integer, nullable=False, default=0)
    
    # Academic Research Metrics
    research_sessions = Column(Integer, nullable=False, default=0)
    exports_generated = Column(Integer, nullable=False, default=0)
    analysis_reports_viewed = Column(Integer, nullable=False, default=0)
    
    # Quality Metrics
    average_whisper_wer = Column(Float, nullable=True)
    average_wav2vec_wer = Column(Float, nullable=True)
    greek_accuracy_score = Column(Float, nullable=True)
    
    # Performance Metrics
    whisper_avg_processing_time = Column(Float, nullable=True)
    wav2vec_avg_processing_time = Column(Float, nullable=True)
    
    # Metadata
    data_metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="analytics_data")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_user_analytics_user_date'),
    )

    def __repr__(self):
        return f'<UserAnalytics {self.user_id} on {self.date}>'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat(),
            'transcriptions_count': self.transcriptions_count,
            'total_audio_duration': self.total_audio_duration,
            'total_processing_time': self.total_processing_time,
            'average_accuracy_score': self.average_accuracy_score,
            'total_words_transcribed': self.total_words_transcribed,
            'whisper_usage_count': self.whisper_usage_count,
            'wav2vec_usage_count': self.wav2vec_usage_count,
            'comparison_usage_count': self.comparison_usage_count,
            'voice_notes_created': self.voice_notes_created,
            'voice_notes_transcribed': self.voice_notes_transcribed,
            'research_sessions': self.research_sessions,
            'exports_generated': self.exports_generated,
            'analysis_reports_viewed': self.analysis_reports_viewed,
            'average_whisper_wer': self.average_whisper_wer,
            'average_wav2vec_wer': self.average_wav2vec_wer,
            'greek_accuracy_score': self.greek_accuracy_score,
            'whisper_avg_processing_time': self.whisper_avg_processing_time,
            'wav2vec_avg_processing_time': self.wav2vec_avg_processing_time,
            'metadata': self.data_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class SystemAnalytics(db.Model):
    """
    Daily system-wide analytics aggregation.
    
    Stores system-level metrics for overall platform monitoring
    and academic research insights.
    """
    __tablename__ = 'system_analytics'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, unique=True)
    
    # User Metrics
    total_users = Column(Integer, nullable=False, default=0)
    active_users = Column(Integer, nullable=False, default=0)
    new_users = Column(Integer, nullable=False, default=0)
    verified_users = Column(Integer, nullable=False, default=0)
    
    # Processing Metrics
    total_transcriptions = Column(Integer, nullable=False, default=0)
    successful_transcriptions = Column(Integer, nullable=False, default=0)
    failed_transcriptions = Column(Integer, nullable=False, default=0)
    total_processing_time = Column(Float, nullable=False, default=0.0)
    total_audio_hours = Column(Float, nullable=False, default=0.0)
    
    # Model Performance
    whisper_usage = Column(Integer, nullable=False, default=0)
    wav2vec_usage = Column(Integer, nullable=False, default=0)
    comparison_usage = Column(Integer, nullable=False, default=0)
    average_whisper_wer = Column(Float, nullable=True)
    average_wav2vec_wer = Column(Float, nullable=True)
    
    # Academic Metrics
    voice_notes_created = Column(Integer, nullable=False, default=0)
    research_exports = Column(Integer, nullable=False, default=0)
    academic_reports_generated = Column(Integer, nullable=False, default=0)
    
    # Performance Metrics
    average_response_time = Column(Float, nullable=True)
    system_uptime_percentage = Column(Float, nullable=True)
    peak_concurrent_users = Column(Integer, nullable=True)
    
    # Greek Language Specific
    greek_transcription_accuracy = Column(Float, nullable=True)
    diacritic_accuracy = Column(Float, nullable=True)
    morphology_accuracy = Column(Float, nullable=True)
    
    # Error Tracking
    error_count = Column(Integer, nullable=False, default=0)
    error_types = Column(JSONB, nullable=True)
    
    # Metadata
    data_metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SystemAnalytics {self.date}>'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'total_users': self.total_users,
            'active_users': self.active_users,
            'new_users': self.new_users,
            'verified_users': self.verified_users,
            'total_transcriptions': self.total_transcriptions,
            'successful_transcriptions': self.successful_transcriptions,
            'failed_transcriptions': self.failed_transcriptions,
            'total_processing_time': self.total_processing_time,
            'total_audio_hours': self.total_audio_hours,
            'whisper_usage': self.whisper_usage,
            'wav2vec_usage': self.wav2vec_usage,
            'comparison_usage': self.comparison_usage,
            'average_whisper_wer': self.average_whisper_wer,
            'average_wav2vec_wer': self.average_wav2vec_wer,
            'voice_notes_created': self.voice_notes_created,
            'research_exports': self.research_exports,
            'academic_reports_generated': self.academic_reports_generated,
            'average_response_time': self.average_response_time,
            'system_uptime_percentage': self.system_uptime_percentage,
            'peak_concurrent_users': self.peak_concurrent_users,
            'greek_transcription_accuracy': self.greek_transcription_accuracy,
            'diacritic_accuracy': self.diacritic_accuracy,
            'morphology_accuracy': self.morphology_accuracy,
            'error_count': self.error_count,
            'error_types': self.error_types,
            'metadata': self.data_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ModelPerformance(db.Model):
    """
    Model-specific performance tracking.
    
    Stores detailed performance metrics for each AI model
    with language-specific analysis.
    """
    __tablename__ = 'model_performance'

    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    language = Column(String(10), nullable=False, default='el')
    
    # Performance Metrics
    usage_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)
    average_wer = Column(Float, nullable=True)
    average_cer = Column(Float, nullable=True)
    average_processing_time = Column(Float, nullable=True)
    average_confidence = Column(Float, nullable=True)
    
    # Greek Language Specific Metrics
    diacritic_accuracy = Column(Float, nullable=True)
    morphology_accuracy = Column(Float, nullable=True)
    proper_noun_accuracy = Column(Float, nullable=True)
    technical_term_accuracy = Column(Float, nullable=True)
    
    # Audio Characteristics
    average_audio_duration = Column(Float, nullable=True)
    audio_quality_score = Column(Float, nullable=True)
    background_noise_level = Column(Float, nullable=True)
    
    # Resource Usage
    average_memory_usage = Column(Float, nullable=True)
    average_cpu_usage = Column(Float, nullable=True)
    average_gpu_usage = Column(Float, nullable=True)
    
    # Error Analysis
    common_errors = Column(JSONB, nullable=True)
    error_patterns = Column(JSONB, nullable=True)
    
    # Metadata
    data_metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('model_name', 'date', 'language', name='uq_model_performance_unique'),
    )

    def __repr__(self):
        return f'<ModelPerformance {self.model_name} on {self.date}>'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'model_name': self.model_name,
            'date': self.date.isoformat(),
            'language': self.language,
            'usage_count': self.usage_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': (self.success_count / self.usage_count * 100) if self.usage_count > 0 else 0.0,
            'average_wer': self.average_wer,
            'average_cer': self.average_cer,
            'average_processing_time': self.average_processing_time,
            'average_confidence': self.average_confidence,
            'diacritic_accuracy': self.diacritic_accuracy,
            'morphology_accuracy': self.morphology_accuracy,
            'proper_noun_accuracy': self.proper_noun_accuracy,
            'technical_term_accuracy': self.technical_term_accuracy,
            'average_audio_duration': self.average_audio_duration,
            'audio_quality_score': self.audio_quality_score,
            'background_noise_level': self.background_noise_level,
            'average_memory_usage': self.average_memory_usage,
            'average_cpu_usage': self.average_cpu_usage,
            'average_gpu_usage': self.average_gpu_usage,
            'common_errors': self.common_errors,
            'error_patterns': self.error_patterns,
            'metadata': self.data_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class LanguageMetrics(db.Model):
    """
    Language-specific analysis metrics.
    
    Stores detailed linguistic analysis for Greek language
    processing and optimization insights.
    """
    __tablename__ = 'language_metrics'

    id = Column(Integer, primary_key=True)
    language_code = Column(String(10), nullable=False)
    date = Column(Date, nullable=False)
    
    # Text Analysis
    total_words_processed = Column(Integer, nullable=False, default=0)
    unique_words_discovered = Column(Integer, nullable=False, default=0)
    out_of_vocabulary_words = Column(Integer, nullable=False, default=0)
    average_word_length = Column(Float, nullable=True)
    average_sentence_length = Column(Float, nullable=True)
    
    # Greek Language Specific
    diacritics_detected = Column(Integer, nullable=False, default=0)
    diacritics_correctly_placed = Column(Integer, nullable=False, default=0)
    morphological_variants_detected = Column(Integer, nullable=False, default=0)
    proper_nouns_detected = Column(Integer, nullable=False, default=0)
    technical_terms_detected = Column(Integer, nullable=False, default=0)
    
    # Accuracy Metrics
    character_accuracy = Column(Float, nullable=True)
    word_accuracy = Column(Float, nullable=True)
    sentence_accuracy = Column(Float, nullable=True)
    semantic_accuracy = Column(Float, nullable=True)
    
    # Phonetic Analysis
    phoneme_accuracy = Column(Float, nullable=True)
    stress_pattern_accuracy = Column(Float, nullable=True)
    syllable_boundary_accuracy = Column(Float, nullable=True)
    
    # Common Patterns
    frequent_error_patterns = Column(JSONB, nullable=True)
    challenging_phonemes = Column(JSONB, nullable=True)
    improvement_suggestions = Column(JSONB, nullable=True)
    
    # Metadata
    data_metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('language_code', 'date', name='uq_language_metrics_lang_date'),
    )

    def __repr__(self):
        return f'<LanguageMetrics {self.language_code} on {self.date}>'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'language_code': self.language_code,
            'date': self.date.isoformat(),
            'total_words_processed': self.total_words_processed,
            'unique_words_discovered': self.unique_words_discovered,
            'out_of_vocabulary_words': self.out_of_vocabulary_words,
            'vocabulary_coverage': ((self.total_words_processed - self.out_of_vocabulary_words) / self.total_words_processed * 100) if self.total_words_processed > 0 else 0.0,
            'average_word_length': self.average_word_length,
            'average_sentence_length': self.average_sentence_length,
            'diacritics_detected': self.diacritics_detected,
            'diacritics_correctly_placed': self.diacritics_correctly_placed,
            'diacritic_accuracy': (self.diacritics_correctly_placed / self.diacritics_detected * 100) if self.diacritics_detected > 0 else 0.0,
            'morphological_variants_detected': self.morphological_variants_detected,
            'proper_nouns_detected': self.proper_nouns_detected,
            'technical_terms_detected': self.technical_terms_detected,
            'character_accuracy': self.character_accuracy,
            'word_accuracy': self.word_accuracy,
            'sentence_accuracy': self.sentence_accuracy,
            'semantic_accuracy': self.semantic_accuracy,
            'phoneme_accuracy': self.phoneme_accuracy,
            'stress_pattern_accuracy': self.stress_pattern_accuracy,
            'syllable_boundary_accuracy': self.syllable_boundary_accuracy,
            'frequent_error_patterns': self.frequent_error_patterns,
            'challenging_phonemes': self.challenging_phonemes,
            'improvement_suggestions': self.improvement_suggestions,
            'metadata': self.data_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ResearchProgress(db.Model):
    """
    Academic research progress tracking.
    
    Tracks academic milestones, thesis progress, and
    research methodology advancement.
    """
    __tablename__ = 'research_progress'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    research_type = Column(String(100), nullable=False)  # thesis, experiment, analysis, etc.
    milestone_name = Column(String(200), nullable=False)
    milestone_description = Column(Text, nullable=True)
    target_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    completion_percentage = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default='planned')  # planned, in_progress, completed, delayed
    
    # Academic Context
    thesis_chapter = Column(String(100), nullable=True)
    research_question = Column(Text, nullable=True)
    methodology_notes = Column(Text, nullable=True)
    findings_summary = Column(Text, nullable=True)
    
    # Metrics
    data_points_collected = Column(Integer, nullable=False, default=0)
    models_tested = Column(Integer, nullable=False, default=0)
    comparisons_completed = Column(Integer, nullable=False, default=0)
    analysis_depth_score = Column(Float, nullable=True)
    
    # Quality Assessment
    confidence_level = Column(Float, nullable=True)  # 0.0 to 1.0
    peer_review_status = Column(String(50), nullable=True)  # pending, reviewed, approved
    supervisor_approval = Column(Boolean, nullable=False, default=False)
    
    # Metadata
    data_metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="research_progress")

    def __repr__(self):
        return f'<ResearchProgress {self.milestone_name} ({self.completion_percentage}%)>'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'research_type': self.research_type,
            'milestone_name': self.milestone_name,
            'milestone_description': self.milestone_description,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'completion_percentage': self.completion_percentage,
            'status': self.status,
            'thesis_chapter': self.thesis_chapter,
            'research_question': self.research_question,
            'methodology_notes': self.methodology_notes,
            'findings_summary': self.findings_summary,
            'data_points_collected': self.data_points_collected,
            'models_tested': self.models_tested,
            'comparisons_completed': self.comparisons_completed,
            'analysis_depth_score': self.analysis_depth_score,
            'confidence_level': self.confidence_level,
            'peer_review_status': self.peer_review_status,
            'supervisor_approval': self.supervisor_approval,
            'metadata': self.data_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def calculate_progress_score(self) -> float:
        """Calculate overall progress score based on multiple factors."""
        base_score = self.completion_percentage / 100.0
        
        # Bonus for data collection
        data_bonus = min(self.data_points_collected / 100.0, 0.1)
        
        # Bonus for model testing
        model_bonus = min(self.models_tested / 5.0, 0.1)
        
        # Bonus for comparisons
        comparison_bonus = min(self.comparisons_completed / 10.0, 0.1)
        
        # Quality bonus
        quality_bonus = (self.confidence_level or 0.0) * 0.1
        
        # Supervisor approval bonus
        approval_bonus = 0.1 if self.supervisor_approval else 0.0
        
        total_score = base_score + data_bonus + model_bonus + comparison_bonus + quality_bonus + approval_bonus
        return min(total_score, 1.0)


class Templates(db.Model):
    """
    Transcription templates for academic research.
    
    Stores reusable templates for different academic
    domains and research contexts.
    """
    __tablename__ = 'templates'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String(50), nullable=False)  # transcription, analysis, export, etc.
    content = Column(Text, nullable=False)
    language = Column(String(10), nullable=False, default='el')
    category = Column(String(100), nullable=True)  # academic, medical, legal, technical
    academic_domain = Column(String(100), nullable=True)  # linguistics, computer_science, etc.
    
    # Template Configuration
    prompt_template = Column(Text, nullable=True)
    post_processing_rules = Column(JSONB, nullable=True)
    vocabulary_hints = Column(ARRAY(String), nullable=True)
    format_specifications = Column(JSONB, nullable=True)
    
    # Usage Tracking
    usage_count = Column(Integer, nullable=False, default=0)
    success_rate = Column(Float, nullable=True)
    average_improvement = Column(Float, nullable=True)
    
    # Academic Metadata
    research_applications = Column(ARRAY(String), nullable=True)
    recommended_for = Column(Text, nullable=True)
    limitations = Column(Text, nullable=True)
    
    # Access Control
    is_public = Column(Boolean, nullable=False, default=True)
    created_by_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # BaseModel fields
    is_active = Column(Boolean, nullable=False, default=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_by_email = Column(String(255), nullable=True)
    updated_by_email = Column(String(255), nullable=True)
    
    # Relationships
    created_by_user = relationship("User", foreign_keys=[created_by_user_id], backref="created_templates")
    created_by = relationship("User", foreign_keys=[created_by_id])
    updated_by = relationship("User", foreign_keys=[updated_by_id])

    def __repr__(self):
        return f'<Template {self.name} ({self.template_type})>'

    def to_dict(self, include_content: bool = True) -> Dict[str, Any]:
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_type': self.template_type,
            'language': self.language,
            'category': self.category,
            'academic_domain': self.academic_domain,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate,
            'average_improvement': self.average_improvement,
            'research_applications': self.research_applications,
            'recommended_for': self.recommended_for,
            'limitations': self.limitations,
            'is_public': self.is_public,
            'created_by_user_id': self.created_by_user_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_content:
            result.update({
                'content': self.content,
                'prompt_template': self.prompt_template,
                'post_processing_rules': self.post_processing_rules,
                'vocabulary_hints': self.vocabulary_hints,
                'format_specifications': self.format_specifications
            })
        
        return result

    def increment_usage(self):
        """Increment usage count for this template."""
        self.usage_count += 1
        self.updated_at = datetime.utcnow()

    @classmethod
    def get_popular_templates(cls, limit: int = 10) -> List['Templates']:
        """Get most popular templates by usage count."""
        return cls.query.filter_by(is_active=True, is_deleted=False, is_public=True)\
                      .order_by(cls.usage_count.desc())\
                      .limit(limit).all()

    @classmethod
    def get_by_academic_domain(cls, domain: str) -> List['Templates']:
        """Get templates for a specific academic domain."""
        return cls.query.filter_by(academic_domain=domain, is_active=True, is_deleted=False, is_public=True)\
                      .order_by(cls.usage_count.desc()).all()


class ExportHistory(db.Model):
    """
    Export and report generation history.
    
    Tracks all generated exports and reports for academic research
    with metadata and download tracking.
    """
    __tablename__ = 'export_history'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Export Details
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=True)
    export_type = Column(String(100), nullable=False)  # report, transcriptions, analytics, comparison
    format = Column(String(20), nullable=False)  # pdf, docx, json, csv, xlsx
    file_size = Column(Integer, nullable=True)  # in bytes
    file_path = Column(String(1000), nullable=True)  # where file is stored
    
    # Generation Details  
    report_type = Column(String(100), nullable=True)  # system-overview, model-performance, etc.
    date_range_start = Column(DateTime, nullable=True)
    date_range_end = Column(DateTime, nullable=True)
    selected_sections = Column(ARRAY(String), nullable=True)
    generation_parameters = Column(JSONB, nullable=True)
    
    # Status and Metadata
    status = Column(String(50), nullable=False, default='completed')  # generating, completed, failed, expired
    error_message = Column(Text, nullable=True)
    download_count = Column(Integer, nullable=False, default=0)
    last_downloaded_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # for temporary exports
    
    # Academic Context
    title = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    language = Column(String(10), nullable=False, default='el')
    tags = Column(ARRAY(String), nullable=True)
    
    # Performance Metrics
    generation_time_seconds = Column(Float, nullable=True)
    data_points_included = Column(Integer, nullable=True)
    total_pages = Column(Integer, nullable=True)
    
    # Timestamps (using Greek timezone)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="export_history")

    def __repr__(self):
        return f'<ExportHistory {self.filename} ({self.format}) by {self.user_id}>'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'export_type': self.export_type,
            'format': self.format,
            'file_size': self.file_size,
            'file_path': self.file_path,
            'report_type': self.report_type,
            'date_range_start': self.date_range_start.isoformat() if self.date_range_start else None,
            'date_range_end': self.date_range_end.isoformat() if self.date_range_end else None,
            'selected_sections': self.selected_sections,
            'generation_parameters': self.generation_parameters,
            'status': self.status,
            'error_message': self.error_message,
            'download_count': self.download_count,
            'last_downloaded_at': self.last_downloaded_at.isoformat() if self.last_downloaded_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'title': self.title,
            'description': self.description,
            'language': self.language,
            'tags': self.tags,
            'generation_time_seconds': self.generation_time_seconds,
            'data_points_included': self.data_points_included,
            'total_pages': self.total_pages,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'createdAt': self.created_at.isoformat(),  # frontend compatibility
        }

    def get_display_title(self) -> str:
        """Get a user-friendly title for display."""
        if self.title:
            return self.title
        
        type_names = {
            'system-overview': 'Γενική Επισκόπηση Συστήματος',
            'model-performance': 'Επίδοση Μοντέλων ASR', 
            'greek-language-analysis': 'Ανάλυση Ελληνικής Γλώσσας',
            'comparative-research': 'Συγκριτική Έρευνα',
            'transcriptions': 'Εξαγωγή Μεταγραφών',
            'analytics': 'Αναλυτικά Στοιχεία',
            'comparison': 'Σύγκριση Μοντέλων'
        }
        
        return type_names.get(self.report_type or self.export_type, self.export_type.title())

    def increment_download(self):
        """Increment download count and update last downloaded timestamp."""
        self.download_count += 1
        self.last_downloaded_at = datetime.utcnow()
        
    @classmethod
    def get_user_recent_exports(cls, user_id: int, limit: int = 10) -> List['ExportHistory']:
        """Get recent exports for a user."""
        return cls.query.filter_by(user_id=user_id, status='completed')\
                      .order_by(cls.created_at.desc())\
                      .limit(limit).all()