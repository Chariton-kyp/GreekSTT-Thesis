"""Base models for the application."""

from datetime import datetime, timezone
from app.extensions import db


class TimestampMixin:
    """Mixin for adding timestamp fields."""
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class BaseModel(db.Model, TimestampMixin):
    """Base model with common fields and timestamps (simplified for thesis)."""
    
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    
    def __init__(self, **kwargs):
        """Initialize model."""
        super().__init__(**kwargs)
    
    def soft_delete(self):
        """Soft delete the record."""
        self.is_deleted = True
        self.is_active = False
        db.session.commit()
    
    def save(self):
        """Save the record."""
        db.session.add(self)
        db.session.commit()
        return self
    
    def to_dict(self):
        """Convert model to dictionary with proper timezone handling."""
        return {
            'id': self.id,
            'created_at': self.created_at.replace(tzinfo=timezone.utc).isoformat() if self.created_at else None,
            'updated_at': self.updated_at.replace(tzinfo=timezone.utc).isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'is_deleted': self.is_deleted
        }