"""Academic model comparison service for GreekSTT Research Platform."""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import httpx
from datetime import datetime

from app.utils.correlation_logger import get_correlation_logger

logger = get_correlation_logger(__name__)


class ModelComparisonService:
    
    def __init__(self):
        self.asr_service_url = "http://asr-service:8001"
        self.timeout = 3600
    
    def _check_ai_service_health(self):
        try:
            import requests
            asr_response = requests.get(f"{self.asr_service_url}/api/v1/health", timeout=5)
            return asr_response.status_code == 200
        except Exception:
            return False
        
    async def process_whisper_only(self, audio_file: bytes, language: str = "el", 
                                   title: str = "Whisper Transcription", description: str = "", 
                                   user_id: str = None, academic_mode: bool = True) -> Dict[str, Any]:
        try:
            logger.info("Processing audio with Whisper model only", {
                'audio_size': len(audio_file),
                'language': language
            })
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"file": ("audio.mp3", audio_file, "audio/mpeg")}
                
                response = await client.post(
                    f"{self.ai_service_url}/api/v1/transcribe/whisper",
                    files=files
                )
                response.raise_for_status()
                
                result = response.json()
                result['processing_metadata'] = {
                    'model': 'whisper',
                    'processed_at': datetime.utcnow().isoformat(),
                    'academic_research': True
                }
                
                logger.info("Whisper processing completed", {
                    'text_length': len(result.get('text', '')),
                    'confidence': result.get('confidence'),
                    'processing_time': result.get('processing_time')
                })
                
                return result
                
        except Exception as e:
            logger.error("Whisper processing failed", {'error': str(e)})
            raise Exception(f"Failed to process with Whisper: {str(e)}")
    
    async def process_wav2vec_only(self, audio_file: bytes, language: str = "el",
                                   title: str = "wav2vec2 Transcription", description: str = "",
                                   user_id: str = None, academic_mode: bool = True) -> Dict[str, Any]:
        try:
            logger.info("Processing audio with wav2vec2 model only", {
                'audio_size': len(audio_file),
                'language': language
            })
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"file": ("audio.mp3", audio_file, "audio/mpeg")}
                
                response = await client.post(
                    f"{self.ai_service_url}/api/v1/transcribe/wav2vec2",
                    files=files
                )
                response.raise_for_status()
                
                result = response.json()
                result['processing_metadata'] = {
                    'model': 'wav2vec2',
                    'processed_at': datetime.utcnow().isoformat(),
                    'academic_research': True
                }
                
                logger.info("wav2vec2 processing completed", {
                    'text_length': len(result.get('text', '')),
                    'confidence': result.get('confidence'),
                    'processing_time': result.get('processing_time')
                })
                
                return result
                
        except Exception as e:
            logger.error("wav2vec2 processing failed", {'error': str(e)})
            raise Exception(f"Failed to process with wav2vec2: {str(e)}")
    
    async def compare_models(self, audio_file: bytes, language: str = "el",
                             title: str = "Model Comparison", description: str = "",
                             user_id: str = None, academic_mode: bool = True) -> Dict[str, Any]:
        try:
            logger.info("Starting academic model comparison", {
                'audio_size': len(audio_file),
                'language': language
            })
            
            whisper_task = self.process_whisper_only(audio_file, language)
            wav2vec_task = self.process_wav2vec_only(audio_file, language)
            
            whisper_result, wav2vec_result = await asyncio.gather(
                whisper_task, wav2vec_task, return_exceptions=True
            )
            
            if isinstance(whisper_result, Exception):
                logger.error("Whisper failed in comparison", {'error': str(whisper_result)})
                whisper_result = {"error": str(whisper_result), "text": "", "confidence": 0}
                
            if isinstance(wav2vec_result, Exception):
                logger.error("wav2vec2 failed in comparison", {'error': str(wav2vec_result)})
                wav2vec_result = {"error": str(wav2vec_result), "text": "", "confidence": 0}
            
            comparison_analysis = self._analyze_model_comparison(whisper_result, wav2vec_result)
            
            result = {
                'whisper_result': whisper_result,
                'wav2vec_result': wav2vec_result,
                'comparison_analysis': comparison_analysis,
                'academic_insights': self._generate_academic_insights(whisper_result, wav2vec_result),
                'research_metadata': {
                    'comparison_type': 'side_by_side',
                    'models_compared': ['whisper', 'wav2vec2'],
                    'analysis_date': datetime.utcnow().isoformat(),
                    'research_purpose': 'academic_comparison'
                }
            }
            
            logger.info("Academic model comparison completed", {
                'whisper_success': 'error' not in whisper_result,
                'wav2vec_success': 'error' not in wav2vec_result,
                'comparison_metrics_count': len(comparison_analysis)
            })
            
            return result
            
        except Exception as e:
            logger.error("Model comparison failed", {'error': str(e)})
            raise Exception(f"Failed to compare models: {str(e)}")
    
    def _analyze_model_comparison(self, whisper_result: Dict, wav2vec_result: Dict) -> Dict[str, Any]:
        """
        try:
            whisper_text = whisper_result.get('text', '').strip()
            wav2vec_text = wav2vec_result.get('text', '').strip()
            
            # Text similarity analysis
            text_similarity = self._calculate_text_similarity(whisper_text, wav2vec_text)
            
            # Performance comparison
            whisper_time = whisper_result.get('processing_time', 0)
            wav2vec_time = wav2vec_result.get('processing_time', 0)
            
            # Confidence comparison
            whisper_confidence = whisper_result.get('confidence', 0)
            wav2vec_confidence = wav2vec_result.get('confidence', 0)
            
            return {
                'text_similarity_score': text_similarity,
                'length_comparison': {
                    'whisper_length': len(whisper_text),
                    'wav2vec_length': len(wav2vec_text),
                    'length_difference': abs(len(whisper_text) - len(wav2vec_text))
                },
                'performance_comparison': {
                    'whisper_processing_time': whisper_time,
                    'wav2vec_processing_time': wav2vec_time,
                    'speed_ratio': wav2vec_time / whisper_time if whisper_time > 0 else 0
                },
                'confidence_comparison': {
                    'whisper_confidence': whisper_confidence,
                    'wav2vec_confidence': wav2vec_confidence,
                    'confidence_difference': abs(whisper_confidence - wav2vec_confidence)
                },
                'greek_specific_metrics': self._analyze_greek_accuracy(whisper_text, wav2vec_text)
            }
            
        except Exception as e:
            logger.error("Comparison analysis failed", {'error': str(e)})
            return {'error': f'Analysis failed: {str(e)}'}
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        if not text1 or not text2:
            return 0.0
            
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _analyze_greek_accuracy(self, whisper_text: str, wav2vec_text: str) -> Dict[str, Any]:
        """Analyze Greek-specific accuracy metrics."""
        try:
            # Count Greek diacritics
            greek_diacritics = ['ά', 'έ', 'ή', 'ί', 'ό', 'ύ', 'ώ', 'ΐ', 'ΰ']
            
            whisper_diacritics = sum(1 for char in whisper_text if char in greek_diacritics)
            wav2vec_diacritics = sum(1 for char in wav2vec_text if char in greek_diacritics)
            
            # Count Greek letters
            whisper_greek_chars = sum(1 for char in whisper_text if '\u0370' <= char <= '\u03FF')
            wav2vec_greek_chars = sum(1 for char in wav2vec_text if '\u0370' <= char <= '\u03FF')
            
            return {
                'diacritic_usage': {
                    'whisper_diacritics': whisper_diacritics,
                    'wav2vec_diacritics': wav2vec_diacritics,
                    'diacritic_difference': abs(whisper_diacritics - wav2vec_diacritics)
                },
                'greek_character_count': {
                    'whisper_greek_chars': whisper_greek_chars,
                    'wav2vec_greek_chars': wav2vec_greek_chars,
                    'greek_char_difference': abs(whisper_greek_chars - wav2vec_greek_chars)
                },
                'language_detection': {
                    'whisper_greek_ratio': whisper_greek_chars / len(whisper_text) if whisper_text else 0,
                    'wav2vec_greek_ratio': wav2vec_greek_chars / len(wav2vec_text) if wav2vec_text else 0
                }
            }
            
        except Exception as e:
            logger.error("Greek accuracy analysis failed", {'error': str(e)})
            return {'error': f'Greek analysis failed: {str(e)}'}
    
    def _generate_academic_insights(self, whisper_result: Dict, wav2vec_result: Dict) -> List[str]:
        """Generate academic insights from comparison results."""
        insights = []
        
        try:
            whisper_text = whisper_result.get('text', '')
            wav2vec_text = wav2vec_result.get('text', '')
            
            # Performance insights
            whisper_time = whisper_result.get('processing_time', 0)
            wav2vec_time = wav2vec_result.get('processing_time', 0)
            
            if whisper_time > 0 and wav2vec_time > 0:
                if whisper_time < wav2vec_time:
                    insights.append(f"Whisper processed {wav2vec_time/whisper_time:.1f}x faster than wav2vec2")
                else:
                    insights.append(f"wav2vec2 processed {whisper_time/wav2vec_time:.1f}x faster than Whisper")
            
            # Text length insights
            if len(whisper_text) > len(wav2vec_text) * 1.2:
                insights.append("Whisper produced significantly more detailed transcription")
            elif len(wav2vec_text) > len(whisper_text) * 1.2:
                insights.append("wav2vec2 produced significantly more detailed transcription")
            else:
                insights.append("Both models produced similar length transcriptions")
            
            # Confidence insights
            whisper_conf = whisper_result.get('confidence', 0)
            wav2vec_conf = wav2vec_result.get('confidence', 0)
            
            if whisper_conf > wav2vec_conf + 0.1:
                insights.append("Whisper shows higher confidence in transcription accuracy")
            elif wav2vec_conf > whisper_conf + 0.1:
                insights.append("wav2vec2 shows higher confidence in transcription accuracy")
            
            # Greek-specific insights
            if 'ά' in whisper_text or 'έ' in whisper_text:
                insights.append("Greek diacritics detected - suitable for formal Greek text analysis")
                
            return insights
            
        except Exception as e:
            logger.error("Insight generation failed", {'error': str(e)})
            return ["Academic analysis insights unavailable due to processing error"]
    
    


# Singleton instance for use across the application
model_comparison_service = ModelComparisonService()