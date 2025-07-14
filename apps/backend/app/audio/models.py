"""Audio file models."""

from app.extensions import db
from app.common.models import BaseModel


class AudioFile(BaseModel):
    """Model for uploaded audio files."""
    
    __tablename__ = 'audio_files'
    
    # File information
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), unique=True, nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)  # in bytes
    file_hash = db.Column(db.String(64), nullable=False, index=True)  # SHA256 - indexed but not unique
    mime_type = db.Column(db.String(100), nullable=False)
    
    # Audio metadata
    duration_seconds = db.Column(db.Float, nullable=True)
    sample_rate = db.Column(db.Integer, nullable=True)
    channels = db.Column(db.Integer, nullable=True)
    bitrate = db.Column(db.Integer, nullable=True)
    
    # User association
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Processing status
    status = db.Column(db.String(50), default='uploaded')  # uploaded, processing, completed, failed
    
    # Source information (for URL downloads)
    source_url = db.Column(db.Text, nullable=True)  # Original video URL
    video_metadata = db.Column(db.JSON, nullable=True)  # Additional metadata from source
    
    # Relationships
    transcriptions = db.relationship('Transcription', backref='audio_file', lazy='dynamic')
    
    def to_dict(self):
        """Convert audio file to dictionary."""
        data = super().to_dict()
        data.update({
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'file_size': self.file_size,
            'file_size_formatted': self._format_file_size(self.file_size),
            'mime_type': self.mime_type,
            'duration_seconds': self.duration_seconds,
            'duration_formatted': self._format_duration(self.duration_seconds) if self.duration_seconds else None,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'bitrate': self.bitrate,
            'status': self.status,
            'user_id': self.user_id,
            'source_url': self.source_url,
            'video_metadata': self.video_metadata,
            'transcriptions_count': self.transcriptions.count()
        })
        return data
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration to human-readable format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def __repr__(self):
        return f'<AudioFile {self.original_filename}>'