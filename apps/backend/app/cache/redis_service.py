"""Redis caching service for transcriptions."""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import redis
from flask import current_app

from app.transcription.models import Transcription

logger = logging.getLogger(__name__)


class TranscriptionCacheService:
    """Service για caching transcriptions στο Redis."""
    
    def __init__(self):
        self._redis_client = None
        self.cache_prefix = "transcription:"
        self.default_ttl = 1800  # 30 minutes
        self.redis_url = None  # Will be set lazily
    
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
                        logger.info(f"Constructed Redis URL: {self.redis_url}")
                
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                # Test connection
                self._redis_client.ping()
                logger.info(f"Redis connection established successfully to {self.redis_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {str(e)}")
                self._redis_client = None
        return self._redis_client
    
    def _get_cache_key(self, transcription_id: int, user_id: int) -> str:
        """Δημιουργεί unique cache key για transcription."""
        return f"{self.cache_prefix}{user_id}:{transcription_id}"
    
    def _serialize_transcription(self, transcription: Transcription) -> Dict[str, Any]:
        """Μετατρέπει Transcription object σε dictionary για Redis."""
        try:
            return {
                'id': transcription.id,
                'title': transcription.title,
                'description': transcription.description,
                'text': transcription.text,
                'language': transcription.language,
                'status': transcription.status,
                'model_used': transcription.model_used,
                'confidence_score': transcription.confidence_score,
                'word_count': transcription.word_count,
                'duration_seconds': transcription.duration_seconds,
                'processing_time': getattr(transcription, 'processing_time', None),
                'user_id': transcription.user_id,
                'audio_file_id': transcription.audio_file_id,
                'created_at': transcription.created_at.isoformat() if transcription.created_at else None,
                'completed_at': transcription.completed_at.isoformat() if transcription.completed_at else None,
                'started_at': transcription.started_at.isoformat() if transcription.started_at else None,
                'updated_at': transcription.updated_at.isoformat() if transcription.updated_at else None,
                'error_message': getattr(transcription, 'error_message', None),
                'credits_used': getattr(transcription, 'credits_used', None),
                
                # Comparison data
                'whisper_text': getattr(transcription, 'whisper_text', None),
                'whisper_confidence': getattr(transcription, 'whisper_confidence', None),
                'whisper_processing_time': getattr(transcription, 'whisper_processing_time', None),
                'wav2vec_text': getattr(transcription, 'wav2vec_text', None),
                'wav2vec_confidence': getattr(transcription, 'wav2vec_confidence', None),
                'wav2vec_processing_time': getattr(transcription, 'wav2vec_processing_time', None),
                
                # Performance metrics
                'whisper_wer': getattr(transcription, 'whisper_wer', None),
                'whisper_cer': getattr(transcription, 'whisper_cer', None),
                'whisper_accuracy': getattr(transcription, 'whisper_accuracy', None),
                'wav2vec_wer': getattr(transcription, 'wav2vec_wer', None),
                'wav2vec_cer': getattr(transcription, 'wav2vec_cer', None),
                'wav2vec_accuracy': getattr(transcription, 'wav2vec_accuracy', None),
                'best_performing_model': getattr(transcription, 'best_performing_model', None),
                'faster_model': getattr(transcription, 'faster_model', None),
                'academic_accuracy_score': getattr(transcription, 'academic_accuracy_score', None),
                'evaluation_completed': getattr(transcription, 'evaluation_completed', False),
                'ground_truth_text': getattr(transcription, 'ground_truth_text', None),
                
                # Cache metadata
                'cached_at': datetime.utcnow().isoformat(),
                'is_cached': True
            }
        except Exception as e:
            logger.error(f"Error serializing transcription {transcription.id}: {str(e)}")
            return None
    
    def cache_transcription(self, transcription: Transcription, ttl: Optional[int] = None) -> bool:
        """Αποθηκεύει transcription στο Redis cache."""
        if not self.redis_client or transcription.status != 'completed':
            return False
        
        try:
            cache_key = self._get_cache_key(transcription.id, transcription.user_id)
            serialized = self._serialize_transcription(transcription)
            
            if not serialized:
                return False
            
            # Αποθήκευση στο Redis με TTL
            ttl = ttl or self.default_ttl
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(serialized, ensure_ascii=False)
            )
            
            logger.info(f"Cached transcription {transcription.id} for user {transcription.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache transcription {transcription.id}: {str(e)}")
            return False
    
    def get_cached_transcription(self, transcription_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Ανακτά transcription από το Redis cache."""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(transcription_id, user_id)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f"Cache HIT: Retrieved transcription {transcription_id} from Redis")
                return data
            else:
                logger.debug(f"Cache MISS: Transcription {transcription_id} not found in cache")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve cached transcription {transcription_id}: {str(e)}")
            return None
    
    def invalidate_transcription(self, transcription_id: int, user_id: int) -> bool:
        """Διαγράφει transcription από το cache."""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._get_cache_key(transcription_id, user_id)
            result = self.redis_client.delete(cache_key)
            
            if result:
                logger.info(f"Invalidated cached transcription {transcription_id}")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to invalidate cached transcription {transcription_id}: {str(e)}")
            return False
    
    def invalidate_user_cache(self, user_id: int) -> int:
        """Διαγράφει όλα τα cached transcriptions για έναν χρήστη."""
        if not self.redis_client:
            return 0
        
        try:
            pattern = f"{self.cache_prefix}{user_id}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} cached transcriptions for user {user_id}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to invalidate user cache for user {user_id}: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Επιστρέφει στατιστικά για το cache."""
        if not self.redis_client:
            return {"status": "disconnected"}
        
        try:
            info = self.redis_client.info()
            pattern = f"{self.cache_prefix}*"
            cached_transcriptions = len(self.redis_client.keys(pattern))
            
            return {
                "status": "connected",
                "redis_version": info.get('redis_version'),
                "used_memory_human": info.get('used_memory_human'),
                "connected_clients": info.get('connected_clients'),
                "cached_transcriptions": cached_transcriptions,
                "cache_prefix": self.cache_prefix,
                "default_ttl": self.default_ttl
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def extend_ttl(self, transcription_id: int, user_id: int, additional_seconds: int = 1800) -> bool:
        """Επεκτείνει το TTL ενός cached transcription."""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._get_cache_key(transcription_id, user_id)
            result = self.redis_client.expire(cache_key, additional_seconds)
            
            if result:
                logger.info(f"Extended TTL for cached transcription {transcription_id}")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to extend TTL for transcription {transcription_id}: {str(e)}")
            return False
    
    def batch_cache_transcriptions(self, transcriptions: list, ttl: Optional[int] = None) -> int:
        """Αποθηκεύει πολλαπλά transcriptions μαζί για καλύτερη performance."""
        if not self.redis_client or not transcriptions:
            return 0
        
        cached_count = 0
        ttl = ttl or self.default_ttl
        
        try:
            # Χρησιμοποιούμε pipeline για batch operations
            pipe = self.redis_client.pipeline()
            
            for transcription in transcriptions:
                if transcription.status == 'completed':
                    cache_key = self._get_cache_key(transcription.id, transcription.user_id)
                    serialized = self._serialize_transcription(transcription)
                    
                    if serialized:
                        pipe.setex(
                            cache_key,
                            ttl,
                            json.dumps(serialized, ensure_ascii=False)
                        )
                        cached_count += 1
            
            if cached_count > 0:
                pipe.execute()
                logger.info(f"Batch cached {cached_count} transcriptions")
            
            return cached_count
            
        except Exception as e:
            logger.error(f"Failed to batch cache transcriptions: {str(e)}")
            return 0


# Singleton instance
_transcription_cache = None


def get_transcription_cache() -> TranscriptionCacheService:
    """Επιστρέφει το singleton instance του TranscriptionCacheService."""
    global _transcription_cache
    if _transcription_cache is None:
        _transcription_cache = TranscriptionCacheService()
    return _transcription_cache


def reset_transcription_cache() -> None:
    """Επαναφέρει το singleton instance για fresh σύνδεση."""
    global _transcription_cache
    if _transcription_cache:
        try:
            if _transcription_cache._redis_client:
                _transcription_cache._redis_client.close()
        except:
            pass
        _transcription_cache = None