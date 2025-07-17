"""
Callback service for notifying backend when transcription completes
"""
import logging
import asyncio
import json
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class CallbackService:
    """Service for sending completion callbacks to backend"""
    
    def __init__(self):
        self.backend_url = "http://backend:5000"  # Internal Docker network URL
        self.timeout = 10  # Timeout for connection issue detection
        self.max_retries = 5  # More retries for better reliability
        self.base_delay = 1  # Base delay for exponential backoff
        
    async def notify_completion(
        self, 
        transcription_id: Optional[str], 
        result: Dict[str, Any], 
        error: Optional[str] = None
    ) -> bool:
        """
        Notify backend about transcription completion
        
        Args:
            transcription_id: ID of the transcription (if available)
            result: Transcription result data
            error: Error message if transcription failed
            
        Returns:
            bool: True if notification was successful
        """
        if not transcription_id:
            logger.warning("No transcription_id provided for callback - skipping notification")
            return False
            
        # Prepare callback data with size optimization for large results
        processed_result = result
        if result and not error:
            # Reduce large segment arrays if necessary for callback payload
            if "segments" in result and len(result["segments"]) > 200:
                logger.info(f"Large segment count ({len(result['segments'])}), truncating for callback")
                processed_result = result.copy()
                processed_result["segments"] = result["segments"][:200]  # Keep first 200 segments
                processed_result["metadata"]["segments_truncated"] = True
                processed_result["metadata"]["total_segments"] = len(result["segments"])
        
        callback_data = {
            "transcription_id": transcription_id,
            "status": "completed" if not error else "failed",
            "result": processed_result if not error else None,
            "error_message": error,
            "source": "wav2vec2-service"
        }
        
        # Add small delay to ensure backend is ready (especially after long processing)
        await asyncio.sleep(0.5)
        
        # Pre-check: verify backend connectivity on first attempt
        if await self.check_backend_health():
            logger.debug(f"Backend health check passed for transcription {transcription_id}")
        else:
            logger.warning(f"Backend health check failed for transcription {transcription_id} - will still attempt callback")

        # Try to send callback with retries and better error handling
        last_error = None
        for attempt in range(self.max_retries):
            try:
                success = await self._send_callback(callback_data)
                if success:
                    logger.info(f"✅ Callback sent successfully for transcription {transcription_id} on attempt {attempt + 1}")
                    return True
                
                # Calculate exponential backoff delay
                delay = self.base_delay * (2 ** attempt)
                logger.info(f"Callback attempt {attempt + 1} failed, retrying in {delay}s...")
                await asyncio.sleep(delay)
                
            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                logger.warning(f"Callback attempt {attempt + 1}/{self.max_retries} failed ({error_type}): {e}")
                
                # Don't wait after the last attempt
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.info(f"Retrying callback in {delay}s...")
                    await asyncio.sleep(delay)
        
        # Log final failure with details about the last error
        if last_error:
            logger.error(f"❌ Failed to send callback for transcription {transcription_id} after {self.max_retries} attempts. Last error: {type(last_error).__name__}: {last_error}")
        else:
            logger.error(f"❌ Failed to send callback for transcription {transcription_id} after {self.max_retries} attempts. All attempts returned failure status.")
        return False
    
    async def _send_callback(self, callback_data: Dict[str, Any]) -> bool:
        """Send the actual callback to backend with improved error handling"""
        try:
            # Create client with specific timeouts
            timeout_config = httpx.Timeout(
                connect=5.0,  # Connection timeout
                read=self.timeout,  # Read timeout  
                write=5.0,  # Write timeout
                pool=10.0   # Pool timeout
            )
            
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                # Add retry-specific headers
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "wav2vec2-service-callback/1.0",
                    "X-Service-Source": "wav2vec2-service"
                }
                
                # Log payload size for debugging and check if too large
                import json
                payload_size = len(json.dumps(callback_data))
                logger.debug(f"Sending callback to {self.backend_url}/api/internal/transcription-callback (payload: {payload_size} bytes)")
                
                # If payload is very large (>512KB), send callback without segments
                if payload_size > 512 * 1024:  # 512KB
                    logger.warning(f"Callback payload too large ({payload_size} bytes), sending callback without segments")
                    minimal_callback = {
                        "transcription_id": callback_data["transcription_id"],
                        "status": callback_data["status"],
                        "result": {
                            "text": callback_data["result"]["text"] if callback_data.get("result") else "",
                            "duration": callback_data["result"].get("duration", 0) if callback_data.get("result") else 0,
                            "language": callback_data["result"].get("language", "el") if callback_data.get("result") else "el",
                            "metadata": {
                                "processing_time_ms": callback_data["result"]["metadata"].get("processing_time_ms", 0) if callback_data.get("result") and callback_data["result"].get("metadata") else 0,
                                "accuracy": callback_data["result"]["metadata"].get("accuracy", 0) if callback_data.get("result") and callback_data["result"].get("metadata") else 0,
                                "avg_confidence": callback_data["result"]["metadata"].get("avg_confidence", 0) if callback_data.get("result") and callback_data["result"].get("metadata") else 0,
                                "was_video_file": callback_data["result"]["metadata"].get("was_video_file", False) if callback_data.get("result") and callback_data["result"].get("metadata") else False,
                                "original_video_duration": callback_data["result"]["metadata"].get("original_video_duration") if callback_data.get("result") and callback_data["result"].get("metadata") else None,
                                "segments_excluded": True,
                                "segment_count": len(callback_data["result"]["segments"]) if callback_data.get("result") and callback_data["result"].get("segments") else 0
                            }
                        } if callback_data.get("result") else None,
                        "error_message": callback_data["error_message"],
                        "source": "wav2vec2-service"
                    }
                    response = await client.post(
                        f"{self.backend_url}/api/internal/transcription-callback",
                        json=minimal_callback,
                        headers=headers
                    )
                else:
                    response = await client.post(
                        f"{self.backend_url}/api/internal/transcription-callback",
                        json=callback_data,
                        headers=headers
                    )
                
                if response.status_code == 200:
                    logger.info(f"Callback sent successfully: HTTP {response.status_code}")
                    return True
                elif response.status_code in [404, 405]:
                    # Endpoint not found or method not allowed - log as error but don't retry
                    logger.error(f"Callback endpoint issue: HTTP {response.status_code} - {response.text[:100]}")
                    return False
                else:
                    # Other HTTP errors - may be transient, allow retry
                    logger.warning(f"Callback failed with HTTP {response.status_code}: {response.text[:100]}")
                    return False
                    
        except httpx.TimeoutException as e:
            logger.warning(f"Callback timed out after {self.timeout}s: {e}")
            return False
        except httpx.ConnectError as e:
            logger.warning(f"Cannot connect to backend for callback: {e}")
            return False
        except httpx.ReadError as e:
            logger.warning(f"Callback read error (connection closed): {e}")
            return False
        except httpx.WriteError as e:
            logger.warning(f"Callback write error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected callback error ({type(e).__name__}): {e}")
            return False
    
    async def notify_completion_async(
        self, 
        transcription_id: Optional[str], 
        result: Dict[str, Any], 
        error: Optional[str] = None
    ):
        """
        Fire-and-forget async notification
        Used when we don't want to block the main response
        """
        try:
            await self.notify_completion(transcription_id, result, error)
        except Exception as e:
            logger.error(f"Async callback failed: {e}")

    async def check_backend_health(self) -> bool:
        """
        Check if backend is reachable for debugging connection issues
        """
        try:
            timeout_config = httpx.Timeout(
                connect=3.0, 
                read=5.0, 
                write=3.0, 
                pool=5.0
            )
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.get(f"{self.backend_url}/api/internal/health")
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"Backend health check failed: {e}")
            return False


# Global callback service instance
callback_service = CallbackService()