"""User repositories."""

from typing import Optional
from app.common.repository import BaseRepository
from app.users.models import User


class UserRepository(BaseRepository):
    """Repository for user data access."""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.model.query.filter_by(
            email=email,
            is_deleted=False
        ).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.model.query.filter_by(
            username=username,
            is_deleted=False
        ).first()
    
    def get_by_sector(self, sector: str):
        """Get all users in a specific sector."""
        return self.model.query.filter_by(
            sector=sector,
            is_deleted=False,
            is_active=True
        ).all()