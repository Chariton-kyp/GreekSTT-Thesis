"""Simple session management service for thesis project."""

from datetime import datetime
from typing import Optional
import logging
from app.extensions import db
from app.sessions.models import UserSession
from app.users.models import User

logger = logging.getLogger(__name__)


class SessionService:
    """Simplified service for managing JWT sessions."""
    
    def create_session(
        self,
        user: User,
        jti: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """Create a new JWT session record."""
        session = UserSession(
            user_id=user.id,
            jti=jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(session)
        db.session.commit()
        
        # Cache the session in Redis for faster retrieval
        try:
            from app.cache.session_cache import get_session_cache
            get_session_cache().cache_session(session)
            logger.debug(f"Cached session {jti} in Redis")
        except Exception as e:
            logger.warning(f"Failed to cache session {jti}: {str(e)}")
        
        return session
    
    def get_session_by_jti(self, jti: str) -> Optional[UserSession]:
        """Get session by JWT ID - with Redis caching."""
        # First check Redis cache
        try:
            from app.cache.session_cache import get_session_cache
            cached_data = get_session_cache().get_cached_session(jti)
            
            if cached_data:
                logger.debug(f"Session {jti} retrieved from Redis cache")
                return self._create_session_from_cache(cached_data)
        except Exception as e:
            logger.warning(f"Redis cache lookup failed for session {jti}: {str(e)}")
        
        # Fallback to database
        session = UserSession.query.filter_by(jti=jti).first()
        
        # Cache the result if found
        if session:
            try:
                from app.cache.session_cache import get_session_cache
                get_session_cache().cache_session(session)
                logger.debug(f"Cached session {jti} after database retrieval")
            except Exception as e:
                logger.warning(f"Failed to cache session {jti}: {str(e)}")
        
        return session
    
    def delete_session(self, jti: str) -> bool:
        """Delete a session by JWT ID."""
        session = self.get_session_by_jti(jti)
        if session:
            db.session.delete(session)
            db.session.commit()
            
            # Invalidate cache
            try:
                from app.cache.session_cache import get_session_cache
                get_session_cache().invalidate_session(jti)
                logger.debug(f"Invalidated cached session {jti}")
            except Exception as e:
                logger.warning(f"Failed to invalidate cached session {jti}: {str(e)}")
            
            return True
        return False
    
    def delete_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user."""
        count = UserSession.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return count
    
    def _create_session_from_cache(self, cached_data: dict) -> Optional[UserSession]:
        """Reconstruct UserSession object from cached data."""
        try:
            # Create UserSession object without adding to session
            session = UserSession()
            session.id = cached_data.get('id')
            session.user_id = cached_data.get('user_id')
            session.jti = cached_data.get('jti')
            session.ip_address = cached_data.get('ip_address')
            session.user_agent = cached_data.get('user_agent')
            
            # Parse datetime fields
            if cached_data.get('expires_at'):
                session.expires_at = datetime.fromisoformat(cached_data['expires_at'])
            if cached_data.get('created_at'):
                session.created_at = datetime.fromisoformat(cached_data['created_at'])
            if cached_data.get('updated_at'):
                session.updated_at = datetime.fromisoformat(cached_data['updated_at'])
            
            return session
            
        except Exception as e:
            logger.error(f"Error reconstructing session from cache: {str(e)}")
            return None

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions from database."""
        count = UserSession.query.filter(
            UserSession.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
        return count


# Global session service instance
session_service = SessionService()