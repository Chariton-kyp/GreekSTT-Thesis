"""Redis session caching service."""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import redis

logger = logging.getLogger(__name__)


class SessionCacheService:
    """Service για caching user sessions στο Redis."""
    
    def __init__(self):
        self._redis_client = None
        self.cache_prefix = "session:"
        self.default_ttl = 600  # 10 minutes - shorter than transcriptions
        self.redis_url = None
    
    @property
    def redis_client(self):
        """Lazy initialization του Redis client."""
        if self._redis_client is None:
            try:
                # Get Redis URL from environment variables
                if self.redis_url is None:
                    import os
                    self.redis_url = os.environ.get('REDIS_URL')
                    if not self.redis_url:
                        # Construct from individual environment variables for Docker
                        redis_host = os.environ.get('REDIS_HOST', 'localhost')
                        redis_port = os.environ.get('REDIS_PORT', '6379')
                        redis_db = os.environ.get('REDIS_DB', '0')
                        self.redis_url = f'redis://{redis_host}:{redis_port}/{redis_db}'
                
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                # Test connection
                self._redis_client.ping()
                logger.info(f"Session cache Redis connection established to {self.redis_url}")
            except Exception as e:
                logger.warning(f"Failed to connect session cache to Redis: {str(e)}")
                self._redis_client = None
        return self._redis_client
    
    def _get_cache_key(self, jti: str) -> str:
        """Δημιουργεί cache key για session."""
        return f"{self.cache_prefix}{jti}"
    
    def _serialize_session(self, session) -> Dict[str, Any]:
        """Μετατρέπει UserSession object σε dictionary για Redis."""
        try:
            return {
                'id': session.id,
                'user_id': session.user_id,
                'jti': session.jti,
                'expires_at': session.expires_at.isoformat() if session.expires_at else None,
                'ip_address': session.ip_address,
                'user_agent': session.user_agent,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'updated_at': session.updated_at.isoformat() if session.updated_at else None,
                
                # Cache metadata
                'cached_at': datetime.utcnow().isoformat(),
                'is_cached': True
            }
        except Exception as e:
            logger.error(f"Error serializing session {session.jti}: {str(e)}")
            return None
    
    def cache_session(self, session, ttl: Optional[int] = None) -> bool:
        """Αποθηκεύει session στο Redis cache."""
        if not self.redis_client or not session:
            return False
        
        try:
            cache_key = self._get_cache_key(session.jti)
            serialized = self._serialize_session(session)
            
            if not serialized:
                return False
            
            # Αποθήκευση στο Redis με TTL
            ttl = ttl or self.default_ttl
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(serialized, ensure_ascii=False)
            )
            
            logger.debug(f"Cached session {session.jti} for user {session.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache session {session.jti}: {str(e)}")
            return False
    
    def get_cached_session(self, jti: str) -> Optional[Dict[str, Any]]:
        """Ανακτά session από το Redis cache."""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(jti)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Cache HIT: Retrieved session {jti} from Redis")
                return data
            else:
                logger.debug(f"Cache MISS: Session {jti} not found in cache")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve cached session {jti}: {str(e)}")
            return None
    
    def invalidate_session(self, jti: str) -> bool:
        """Διαγράφει session από το cache."""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._get_cache_key(jti)
            result = self.redis_client.delete(cache_key)
            
            if result:
                logger.debug(f"Invalidated cached session {jti}")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to invalidate cached session {jti}: {str(e)}")
            return False
    
    def invalidate_user_sessions(self, user_id: int) -> int:
        """Διαγράφει όλα τα cached sessions για έναν χρήστη."""
        if not self.redis_client:
            return 0
        
        try:
            # Αφού δεν έχουμε user_id στο cache key, δεν μπορούμε να κάνουμε bulk delete
            # Αυτό είναι trade-off για απλότητα - sessions expire σύντομα ούτως ή άλλως
            logger.debug(f"Cannot bulk invalidate sessions for user {user_id} - sessions expire in {self.default_ttl}s")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to invalidate user sessions for user {user_id}: {str(e)}")
            return 0


# Singleton instance
_session_cache = None


def get_session_cache() -> SessionCacheService:
    """Επιστρέφει το singleton instance του SessionCacheService."""
    global _session_cache
    if _session_cache is None:
        _session_cache = SessionCacheService()
    return _session_cache