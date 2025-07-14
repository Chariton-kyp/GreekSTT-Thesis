"""AI Service client for transcription - Updated for separated services."""

import requests
import logging
import time
import uuid
import os
import asyncio
import concurrent.futures
import httpx
from typing import Dict, Any, Optional
from flask import current_app
from app.services.asr_client import asr_client


class AIServiceClient:
    """Client for communicating with separated ASR and LLM services."""
    
    def __init__(self):
        self.asr_client = asr_client
        self.logger = logging.getLogger(__name__)
    
    def _get_config(self):
        """Configuration no longer needed for separated services."""
        pass
    
    async def transcribe_audio(self, audio_file_path: str, 
                             language: str = 'el',
                             model: str = 'whisper',
                             request_id: Optional[str] = None,
                             original_filename: Optional[str] = None,
                             transcription_id: Optional[str] = None) -> Dict[str, Any]:
        """Send audio file to separated ASR service for transcription."""
        
        # Generate full GUID correlation ID for tracking
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Get file info for logging - use original filename if provided
        filename = original_filename or os.path.basename(audio_file_path)
        file_size = os.path.getsize(audio_file_path) if os.path.exists(audio_file_path) else 0
        
        # Validate file exists before proceeding
        if not os.path.exists(audio_file_path):
            self.logger.error(f"[{request_id}] ❌ Audio file not found: {audio_file_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        self.logger.info(f"[{request_id}] 🚀 BACKEND→ASR: Starting transcription request")
        self.logger.info(f"[{request_id}] 📁 File: {filename} ({file_size/1024/1024:.2f} MB)")
        self.logger.info(f"[{request_id}] 🌐 Language: {language} | Model: {model}")
        
        start_time = time.time()
        
        try:
            # Read audio file
            with open(audio_file_path, 'rb') as f:
                audio_bytes = f.read()
            
            # Send to appropriate ASR service endpoint based on model
            if model == 'whisper':
                result = await self.asr_client.transcribe_whisper(audio_bytes, filename, transcription_id)
            elif model == 'wav2vec2':
                result = await self.asr_client.transcribe_wav2vec2(audio_bytes, filename, transcription_id)
            elif model == 'compare':
                result = await self.asr_client.compare_models(audio_bytes, filename, transcription_id)
            else:
                # Default to whisper
                result = await self.asr_client.transcribe_whisper(audio_bytes, filename, transcription_id)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"[{request_id}] ✅ ASR transcription completed in {processing_time:.2f}s")
            self.logger.info(f"[{request_id}] 📝 Result: {len(result.get('text', ''))} characters")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"[{request_id}] ❌ ASR transcription failed: {str(e)} ({processing_time:.2f}s)")
            raise
    
    def transcribe_both_models(self, audio_file_path: str, 
                              language: str = 'el',
                              request_id: Optional[str] = None,
                              original_filename: Optional[str] = None) -> Dict[str, Any]:
        """Process audio with both Whisper and wav2vec2 models in parallel."""
        if not request_id:
            request_id = str(uuid.uuid4())
        
        self.logger.info(f"[{request_id}] 🎯 Starting parallel processing with both models")
        start_time = time.time()
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both model requests simultaneously  
            whisper_future = executor.submit(
                self._transcribe_single_model,
                audio_file_path, language, 'whisper', f"{request_id}-whisper", original_filename
            )
            wav2vec_future = executor.submit(
                self._transcribe_single_model, 
                audio_file_path, language, 'wav2vec2', f"{request_id}-wav2vec", original_filename
            )
            
            # Wait for both to complete
            whisper_result = whisper_future.result()
            wav2vec_result = wav2vec_future.result()
        
        total_duration = time.time() - start_time
        
        # Combine results
        combined_result = {
            'whisper_text': whisper_result.get('text', ''),
            'whisper_confidence': whisper_result.get('confidence', 0.0),
            'whisper_segments': whisper_result.get('segments', []),
            'whisper_metadata': whisper_result.get('metadata', {}),
            
            'wav2vec_text': wav2vec_result.get('text', ''),
            'wav2vec_confidence': wav2vec_result.get('confidence', 0.0),
            'wav2vec_segments': wav2vec_result.get('segments', []),
            'wav2vec_metadata': wav2vec_result.get('metadata', {}),
            
            'comparison_metrics': self._calculate_comparison_metrics(
                whisper_result, wav2vec_result
            ),
            
            'metadata': {
                'model': 'both',
                'total_processing_time_ms': total_duration * 1000,
                'whisper_processing_time_ms': whisper_result.get('metadata', {}).get('processing_time_ms', 0),
                'wav2vec_processing_time_ms': wav2vec_result.get('metadata', {}).get('processing_time_ms', 0),
                'request_id': request_id,
                'language': language
            }
        }
        
        self.logger.info(f"[{request_id}] ✅ Parallel processing completed in {total_duration:.2f}s")
        return combined_result
    
    def _transcribe_single_model(self, audio_file_path: str, language: str, 
                                model: str, request_id: str, 
                                original_filename: Optional[str] = None) -> Dict[str, Any]:
        """Helper method to transcribe with a single model."""
        # Run async transcription in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.transcribe_audio(audio_file_path, language, model, request_id, original_filename)
            )
        finally:
            loop.close()
    
    def _calculate_comparison_metrics(self, whisper_result: Dict, wav2vec_result: Dict) -> Dict[str, Any]:
        """Calculate comparison metrics between the two models."""
        whisper_text = whisper_result.get('text', '')
        wav2vec_text = wav2vec_result.get('text', '')
        
        # Basic comparison metrics
        metrics = {
            'whisper_word_count': len(whisper_text.split()),
            'wav2vec_word_count': len(wav2vec_text.split()),
            'whisper_char_count': len(whisper_text),
            'wav2vec_char_count': len(wav2vec_text),
            'text_similarity': self._calculate_text_similarity(whisper_text, wav2vec_text),
            'confidence_difference': abs(
                whisper_result.get('confidence', 0) - wav2vec_result.get('confidence', 0)
            ),
            'processing_time_ratio': self._calculate_time_ratio(whisper_result, wav2vec_result)
        }
        
        return metrics
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate basic text similarity (Jaccard similarity of words)."""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_time_ratio(self, whisper_result: Dict, wav2vec_result: Dict) -> float:
        """Calculate processing time ratio (whisper_time / wav2vec_time)."""
        whisper_time = whisper_result.get('metadata', {}).get('processing_time_ms', 1)
        wav2vec_time = wav2vec_result.get('metadata', {}).get('processing_time_ms', 1)
        
        return whisper_time / wav2vec_time if wav2vec_time > 0 else 1.0
    
    async def check_health(self) -> bool:
        """Check if separated AI services are healthy."""
        health_check_start = time.time()
        
        try:
            # Check ASR service only
            asr_health = await self.asr_client.health_check()
            
            health_duration = time.time() - health_check_start
            
            asr_healthy = asr_health.get('status') != 'error'
            
            if asr_healthy:
                self.logger.info(f"✅ ASR service healthy ({health_duration*1000:.0f}ms)")
                return True
            else:
                self.logger.error(f"❌ ASR service unhealthy ({health_duration*1000:.0f}ms)")
                return False
                
        except Exception as e:
            health_duration = time.time() - health_check_start
            self.logger.error(f"❌ AI service health check error: {str(e)} ({health_duration*1000:.0f}ms)")
            return False
    
    async def get_models(self) -> Dict[str, Any]:
        """Get available models from separated AI services."""
        models_request_start = time.time()
        self.logger.info(f"🤖 Requesting available models from separated AI services")
        
        try:
            # Return static model information for separated services
            models_data = {
                'models': [
                    {
                        'name': 'whisper-large-v3',
                        'type': 'asr',
                        'language': 'el',
                        'service': 'asr-service',
                        'description': 'OpenAI Whisper Large V3 optimized for Greek'
                    },
                    {
                        'name': 'wav2vec2-greek',
                        'type': 'asr', 
                        'language': 'el',
                        'service': 'asr-service',
                        'description': 'Facebook wav2vec2 trained on Greek corpus'
                    }
                ],
                'total_models': 2,
                'services': {
                    'asr-service': ['whisper-large-v3', 'wav2vec2-greek']
                }
            }
            
            models_duration = time.time() - models_request_start
            self.logger.info(f"🤖 Models retrieved successfully ({models_duration*1000:.0f}ms): {len(models_data.get('models', []))} models available")
            
            return models_data
            
        except Exception as e:
            models_duration = time.time() - models_request_start
            self.logger.error(f"❌ Get models error: {str(e)} ({models_duration*1000:.0f}ms)")
            raise