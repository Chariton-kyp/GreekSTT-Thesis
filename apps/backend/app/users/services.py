"""User services."""

import logging
from typing import Optional, Tuple, List, Dict, Any
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import func
from app.extensions import db
from app.users.models import User
from app.users.repositories import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """Service for user operations."""
    
    def __init__(self):
        self.repository = UserRepository()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        logger.debug(f"Fetching user by ID: {user_id}")
        user = self.repository.get_by_id(user_id)
        if user:
            logger.debug(f"User found: {user.email} (active: {user.is_active})")
        else:
            logger.debug(f"User {user_id} not found")
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        logger.debug(f"Fetching user by email: {email}")
        user = self.repository.get_by_email(email)
        if user:
            logger.debug(f"User found: {user.id} (active: {user.is_active})")
        else:
            logger.debug(f"User with email {email} not found")
        return user
    
    def get_all_users(self, page: int = 1, per_page: int = 20) -> Tuple[List[User], Dict[str, Any]]:
        """Get all users with pagination."""
        logger.info(f"Fetching users page {page} (per_page: {per_page})")
        result = self.repository.paginate(page=page, per_page=per_page)
        logger.info(f"Retrieved {len(result['items'])} users (total: {result['total']})")
        return result['items'], {
            'total': result['total'],
            'pages': result['pages'],
            'current_page': result['current_page'],
            'per_page': result['per_page'],
            'has_prev': result['has_prev'],
            'has_next': result['has_next']
        }
    
    def update_user(self, user_id: int, data: dict) -> Optional[User]:
        """Update user profile."""
        logger.info(f"Updating user {user_id} with fields: {list(data.keys())}")
        
        # Remove fields that shouldn't be updated through this method
        data.pop('password', None)
        data.pop('email', None)  # Email change should be done separately with verification
        
        updated_user = self.repository.update(user_id, **data)
        if updated_user:
            logger.info(f"User {user_id} updated successfully")
        else:
            logger.warning(f"Failed to update user {user_id} - user not found")
        
        return updated_user
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password."""
        logger.info(f"Password change attempt for user {user_id}")
        user = self.repository.get_by_id(user_id)
        
        if not user:
            logger.warning(f"Password change failed - user {user_id} not found")
            return False
            
        if not check_password_hash(user.password_hash, current_password):
            logger.warning(f"Password change failed for user {user_id} - invalid current password")
            return False
        
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        logger.info(f"Password changed successfully for user {user_id}")
        return True
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics."""
        logger.info(f"Calculating statistics for user {user_id}")
        user = self.repository.get_by_id(user_id)
        if not user:
            logger.warning(f"Cannot calculate stats - user {user_id} not found")
            return {}
        
        # Get transcription statistics
        from app.transcription.models import Transcription
        
        total_transcriptions = Transcription.query.filter_by(
            user_id=user_id,
            is_deleted=False
        ).count()
        
        total_duration = db.session.query(
            func.sum(Transcription.duration_seconds)
        ).filter_by(
            user_id=user_id,
            is_deleted=False
        ).scalar() or 0
        
        # Get this month's usage
        from datetime import datetime, timedelta
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        monthly_duration = db.session.query(
            func.sum(Transcription.duration_seconds)
        ).filter(
            Transcription.user_id == user_id,
            Transcription.created_at >= start_of_month,
            Transcription.is_deleted == False
        ).scalar() or 0
        
        # Get recent transcriptions
        recent_transcriptions = Transcription.query.filter_by(
            user_id=user_id,
            is_deleted=False
        ).order_by(
            Transcription.created_at.desc()
        ).limit(5).all()
        
        stats = {
            'total_transcriptions': total_transcriptions,
            'total_duration_seconds': float(total_duration),
            'total_duration_formatted': self._format_duration(total_duration),
            'monthly_duration_seconds': float(monthly_duration),
            'monthly_duration_formatted': self._format_duration(monthly_duration),
            'recent_transcriptions': [t.to_dict() for t in recent_transcriptions]
        }
        
        logger.info(f"Stats calculated for user {user_id}: {total_transcriptions} transcriptions, {self._format_duration(total_duration)} total")
        return stats
    
    def activate_user(self, user_id: int) -> Optional[User]:
        """Activate a user."""
        logger.info(f"Activating user {user_id}")
        user = self.repository.update(user_id, is_active=True)
        if user:
            logger.info(f"User {user_id} ({user.email}) activated successfully")
        else:
            logger.warning(f"Failed to activate user {user_id} - user not found")
        return user
    
    def deactivate_user(self, user_id: int) -> Optional[User]:
        """Deactivate a user."""
        logger.info(f"Deactivating user {user_id}")
        user = self.repository.update(user_id, is_active=False)
        if user:
            logger.info(f"User {user_id} ({user.email}) deactivated successfully")
        else:
            logger.warning(f"Failed to deactivate user {user_id} - user not found")
        return user
    
    def delete_user(self, user_id: int, force_delete: bool = False) -> Optional[User]:
        """Delete a user (soft delete by default)."""
        logger.info(f"Deleting user {user_id} (force: {force_delete})")
        
        # Get user first for logging
        user = self.repository.get_by_id(user_id)
        if not user:
            logger.warning(f"Failed to delete user {user_id} - user not found")
            return None
        
        logger.info(f"Found user to delete: {user.email} (active: {user.is_active}, deleted: {user.is_deleted})")
        
        # Use repository's delete method
        try:
            logger.info(f"Calling repository.delete(user_id={user_id}, soft={not force_delete})")
            success = self.repository.delete(user_id, soft=not force_delete)
            logger.info(f"Repository.delete returned: {success}")
            
            if success:
                delete_type = "hard deleted" if force_delete else "soft deleted"
                logger.info(f"User {user_id} ({user.email}) {delete_type}")
                return user
            else:
                logger.warning(f"Failed to delete user {user_id} - repository.delete returned False")
                return None
        except Exception as e:
            logger.error(f"Exception during user deletion: {str(e)}")
            return None
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"