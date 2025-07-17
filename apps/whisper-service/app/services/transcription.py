"""
Whisper Service - Dedicated transcription service for Whisper model
Handles only Whisper transcription (transformers 4.36.0)
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class WhisperService:
    """Dedicated Whisper transcription service"""
    
    def __init__(self):
        self.whisper_model = None
        
    async def initialize(self):
        """Initialize Whisper model on demand
        
        Model loading is deferred until first transcription request
        to optimize startup time and memory usage.
        """
        logger.info("Whisper Service initialized - model will load on demand")


_whisper_service = None


def get_asr_service() -> WhisperService:
    """Get or create the global Whisper service instance
    
    Returns:
        WhisperService: Singleton instance of the Whisper service
    """
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = WhisperService()
    return _whisper_service