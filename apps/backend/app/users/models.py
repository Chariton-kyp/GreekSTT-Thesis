"""User models."""

from app.extensions import db
from app.common.models import BaseModel

class User(BaseModel):
    """User model."""
    
    __tablename__ = 'users'
    
    # Authentication fields
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # Required for academic authentication
    email_verified = db.Column(db.Boolean, default=False)
    
    
    # Personal information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    
    # Professional information
    organization = db.Column(db.String(100))
    
    # Academic and research fields  
    institution = db.Column(db.String(200))
    research_focus = db.Column(db.String(500))
    academic_level = db.Column(db.String(50))
    thesis_title = db.Column(db.String(300))
    academic_year = db.Column(db.String(20))
    
    # Relationships
    audio_files = db.relationship('AudioFile', foreign_keys='AudioFile.user_id', backref='user', lazy='dynamic')
    transcriptions = db.relationship('Transcription', foreign_keys='Transcription.user_id', backref='user', lazy='dynamic')
    
    @property
    def full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    
    @property
    def primary_email_verified(self):
        """Check if primary email is verified."""
        return self.email_verified
    
    # Academic version - simplified for thesis demonstration
    
    # Simplified thesis platform - no complex limits or research levels
    
    def to_dict(self):
        """Convert user to dictionary."""
        data = super().to_dict()
        data.update({
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'organization': self.organization,
            'institution': self.institution,
            'research_focus': self.research_focus,
            'academic_level': self.academic_level,
            'thesis_title': self.thesis_title,
            'academic_year': self.academic_year,
            'email_verified': self.email_verified,
            'primary_email_verified': self.primary_email_verified,
        })
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'