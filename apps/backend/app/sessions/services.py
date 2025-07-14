"""Simple session management service for thesis project."""

from datetime import datetime
from typing import Optional
from app.extensions import db
from app.sessions.models import UserSession
from app.users.models import User


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
        return session
    
    def get_session_by_jti(self, jti: str) -> Optional[UserSession]:
        """Get session by JWT ID."""
        return UserSession.query.filter_by(jti=jti).first()
    
    def delete_session(self, jti: str) -> bool:
        """Delete a session by JWT ID."""
        session = self.get_session_by_jti(jti)
        if session:
            db.session.delete(session)
            db.session.commit()
            return True
        return False
    
    def delete_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user."""
        count = UserSession.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return count
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions from database."""
        count = UserSession.query.filter(
            UserSession.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
        return count


# Global session service instance
session_service = SessionService()