"""
ASR Service Client for GreekSTT Research Platform
Communicates with separated ASR service (Whisper + wav2vec2)
"""
import httpx
import logging
from typing import Dict, Any, Optional
from app.utils.correlation_logger import get_correlation_logger

logger = get_correlation_logger(__name__)


class ASRServiceClient:
    """Client for communicating with the ASR service"""
    
    def __init__(self):
        self.asr_service_url = "http://asr-service:8001"  # Docker network URL
        self.timeout = 3600  # 60 minutes for long transcriptions (whisper processing)
        
    async def health_check(self) -> Dict[str, Any]:
        """Check ASR service health"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.asr_service_url}/api/v1/health")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"ASR service health check failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def transcribe_whisper(self, audio_file: bytes, filename: str = "audio.mp3", transcription_id: str = None) -> Dict[str, Any]:
        """Transcribe audio with Whisper model"""
        try:
            logger.info(f"Sending {filename} to ASR service for Whisper transcription")
            
            # Prepare headers with transcription_id for callback
            headers = {}
            if transcription_id:
                headers["X-Transcription-ID"] = str(transcription_id)
                logger.info(f"Including transcription_id {transcription_id} for callback support")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"file": (filename, audio_file, "audio/mpeg")}
                
                response = await client.post(
                    f"{self.asr_service_url}/api/v1/transcribe/whisper",
                    files=files,
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Whisper transcription completed for {filename}")
                return result
                
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise Exception(f"ASR service error: {str(e)}")
    
    async def transcribe_wav2vec2(self, audio_file: bytes, filename: str = "audio.mp3", transcription_id: str = None) -> Dict[str, Any]:
        """Transcribe audio with wav2vec2 model"""
        try:
            logger.info(f"Sending {filename} to ASR service for wav2vec2 transcription")
            
            # Prepare headers with transcription_id for callback
            headers = {}
            if transcription_id:
                headers["X-Transcription-ID"] = str(transcription_id)
                logger.info(f"Including transcription_id {transcription_id} for wav2vec2 callback support")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"file": (filename, audio_file, "audio/mpeg")}
                
                response = await client.post(
                    f"{self.asr_service_url}/api/v1/transcribe/wav2vec2",
                    files=files,
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"wav2vec2 transcription completed for {filename}")
                return result
                
        except Exception as e:
            logger.error(f"wav2vec2 transcription failed: {e}")
            raise Exception(f"ASR service error: {str(e)}")
    
    async def compare_models(self, audio_file: bytes, filename: str = "audio.mp3", transcription_id: str = None) -> Dict[str, Any]:
        """Compare Whisper vs wav2vec2 models"""
        try:
            logger.info(f"Sending {filename} to ASR service for model comparison")
            
            # Prepare headers with transcription_id for callback
            headers = {}
            if transcription_id:
                headers["X-Transcription-ID"] = str(transcription_id)
                logger.info(f"Including transcription_id {transcription_id} for comparison callback support")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"file": (filename, audio_file, "audio/mpeg")}
                
                response = await client.post(
                    f"{self.asr_service_url}/api/v1/transcribe/compare",
                    files=files,
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Model comparison completed for {filename}")
                return result
                
        except Exception as e:
            logger.error(f"Model comparison failed: {e}")
            raise Exception(f"ASR service error: {str(e)}")


# Singleton instance
asr_client = ASRServiceClient()