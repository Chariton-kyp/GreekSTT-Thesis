"""Audio file repositories."""

from typing import Dict, Any
from app.common.repository import BaseRepository
from app.audio.models import AudioFile


class AudioRepository(BaseRepository):
    """Repository for audio file data access."""
    
    def __init__(self):
        super().__init__(AudioFile)
    
    def get_user_files(self, user_id: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get all audio files for a user with pagination."""
        return self.paginate(
            page=page,
            per_page=per_page,
            filters={'user_id': user_id}
        )
    
    def get_by_hash(self, file_hash: str):
        """Get audio file by its hash."""
        return self.model.query.filter_by(
            file_hash=file_hash,
            is_deleted=False
        ).first()
    
    def get_processing_files(self):
        """Get all files that are currently being processed."""
        return self.model.query.filter_by(
            status='processing',
            is_deleted=False
        ).all()
    
    def get_failed_files(self):
        """Get all files that failed processing."""
        return self.model.query.filter_by(
            status='failed',
            is_deleted=False
        ).all()