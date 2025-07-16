"""
wav2vec2 Service - Dedicated transcription service for wav2vec2 model
Handles only wav2vec2 transcription (transformers 4.36.0)
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Wav2Vec2Service:
    """Dedicated wav2vec2 transcription service"""
    
    def __init__(self):
        self.wav2vec2_model = None
        
    async def initialize(self):
        """Initialize wav2vec2 model on demand"""
        logger.info("wav2vec2 Service initialized - model will load on demand")


# Global service instance
_wav2vec2_service = None


def get_asr_service() -> Wav2Vec2Service:
    """Get or create the global wav2vec2 service instance"""
    global _wav2vec2_service
    if _wav2vec2_service is None:
        _wav2vec2_service = Wav2Vec2Service()
    return _wav2vec2_service