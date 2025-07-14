"""
ASR Service - Simplified transcription service for separated architecture
Handles Whisper and wav2vec2 models only (transformers 4.36.0)
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ASRService:
    """Simple ASR service for separated architecture"""
    
    def __init__(self):
        self.whisper_model = None
        self.wav2vec2_model = None
        
    async def initialize(self):
        """Initialize ASR models on demand"""
        logger.info("ASR Service initialized - models will load on demand")


# Global service instance
_asr_service = None


def get_asr_service() -> ASRService:
    """Get or create the global ASR service instance"""
    global _asr_service
    if _asr_service is None:
        _asr_service = ASRService()
    return _asr_service