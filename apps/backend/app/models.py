"""Shared application models."""

from app.extensions import db
from datetime import datetime


class BlacklistToken(db.Model):
    """Model for storing revoked JWT tokens."""
    
    __tablename__ = 'blacklist_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BlacklistToken {self.jti}>'