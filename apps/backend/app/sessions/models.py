"""Simple session management for thesis project."""

from datetime import datetime
from app.extensions import db
from app.common.models import BaseModel


class UserSession(BaseModel):
    """Simplified model for tracking JWT sessions."""
    
    __tablename__ = 'user_sessions'
    
    # Core session fields only
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    jti = db.Column(db.String(36), unique=True, nullable=False)  # JWT ID
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Basic tracking
    ip_address = db.Column(db.String(45))  # Optional IP tracking
    user_agent = db.Column(db.Text)  # Optional browser info
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('sessions', lazy='dynamic'))
    
    def __repr__(self):
        return f'<UserSession user_id={self.user_id} jti={self.jti}>'


# Simple index for performance
db.Index('idx_user_sessions_user_id', UserSession.user_id)
db.Index('idx_user_sessions_jti', UserSession.jti)