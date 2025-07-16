"""
wav2vec2 Greek Model Implementation - Simple with Garbage Collection
Based on lighteternal/wav2vec2-large-xlsr-53-greek HuggingFace model
"""
import logging
import time
import torch
import librosa
import numpy as np
from typing import Dict, Any, List, Tuple
from pathlib import Path
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

logger = logging.getLogger(__name__)


class Wav2Vec2Model:
    """Simple wav2vec2 implementation with aggressive garbage collection"""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.device = self._get_device()
        self.model_name = "lighteternal/wav2vec2-large-xlsr-53-greek"
        
    def _get_device(self) -> str:
        """Detect optimal device"""
        if torch.cuda.is_available():
            logger.info("Using CUDA for wav2vec2")
            return "cuda"
        else:
            logger.info("Using CPU for wav2vec2")
            return "cpu"
    
    async def load(self) -> None:
        """Load wav2vec2 model"""
        try:
            import gc
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            logger.info(f"Loading wav2vec2 model: {self.model_name}")
            
            self.processor = Wav2Vec2Processor.from_pretrained(self.model_name)
            self.model = Wav2Vec2ForCTC.from_pretrained(self.model_name)
            
            self.model = self.model.to(self.device)
            self.model.eval()
            
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            logger.info(f"✅ wav2vec2 loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load wav2vec2: {e}")
            raise
    
    def unload(self) -> None:
        """Unload model with aggressive garbage collection"""
        try:
            if self.model is not None:
                logger.info("🗑️ Unloading wav2vec2 model...")
                del self.model
                self.model = None
                
            if self.processor is not None:
                del self.processor
                self.processor = None
            
            # Aggressive garbage collection
            import gc
            for i in range(3):
                collected = gc.collect()
                if collected == 0:
                    break
                
            # Clean up GPU memory if using CUDA
            if self.device == "cuda":
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                
            logger.info("✅ wav2vec2 model unloaded with garbage collection")
            
        except Exception as e:
            logger.error(f"❌ Error unloading wav2vec2: {e}")
            # Force cleanup even if error occurred
            self.model = None
            self.processor = None
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    async def transcribe(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        """Transcribe audio using wav2vec2 with garbage collection"""
        if not self.model or not self.processor:
            raise RuntimeError("Model not loaded")
        
        start_time = time.time()
        logger.info(f"Transcribing with wav2vec2: {Path(audio_path).name}")
        
        # Pre-transcription memory cleanup
        import gc
        gc.collect()
        if self.device == "cuda":
            torch.cuda.empty_cache()
        
        # Audio conversion for video containers
        from app.utils.audio_converter import AudioConverter
        
        temp_audio_path = None
        processing_path = audio_path
        
        try:
            # Check if we need to convert video to audio
            temp_audio_path = AudioConverter.convert_to_wav(audio_path, target_sample_rate=16000)
            if temp_audio_path:
                processing_path = temp_audio_path
                logger.info(f"🎬 Using converted audio file for wav2vec2 processing")
            
            # Load and preprocess audio
            audio_array, sample_rate = librosa.load(processing_path, sr=16000, mono=True)
            duration = len(audio_array) / 16000
            
            logger.info(f"Audio loaded for wav2vec2: {len(audio_array)} samples, duration: {duration:.2f}s")
            
            # Chunking for large audio files (prevent OOM)
            if duration > 30.0:  # Chunk anything longer than 30 seconds
                logger.info(f"Large audio detected ({duration:.1f}s) - using VAD-based chunking")
                return await self._transcribe_vad_chunked(audio_array, duration, start_time)
            else:
                return await self._transcribe_single(audio_array, duration, start_time)
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ wav2vec2 transcription failed after {processing_time:.0f}ms: {e}")
            raise
        finally:
            # Cleanup temporary audio file if created
            if temp_audio_path:
                AudioConverter.cleanup_temp_file(temp_audio_path)
            
            # Final cleanup after transcription
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
    
    def _clean_transcription(self, text: str) -> str:
        """Clean transcription following model recommendations"""
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Convert to lowercase (as recommended)
        text = text.lower()
        
        # Basic Greek text normalization
        import unicodedata
        text = unicodedata.normalize('NFC', text)
        
        return text.strip()
    
    async def _transcribe_single(self, audio_array: np.ndarray, duration: float, start_time: float) -> Dict[str, Any]:
        """Transcribe single audio file (≤30 seconds)"""
        # Process audio using processor
        input_dict = self.processor(
            audio_array, 
            return_tensors="pt", 
            sampling_rate=16000
        )
        
        # Move to device (standard approach)
        input_values = input_dict.input_values.to(self.device)
        
        # Run inference
        with torch.no_grad():
            logits = self.model(input_values).logits
        
        # CTC Decoding - get predictions
        predicted_ids = torch.argmax(logits, dim=-1)
        
        # Decode using processor
        transcription = self.processor.decode(predicted_ids[0])
        
        # Calculate confidence score
        probabilities = torch.softmax(logits, dim=-1)
        confidence = torch.max(probabilities, dim=-1).values.mean().item()
        
        # Immediate cleanup of large tensors
        del input_values, logits, probabilities, predicted_ids
        import gc
        gc.collect()
        if self.device == "cuda":
            torch.cuda.empty_cache()
        
        # Clean up transcription
        transcription = self._clean_transcription(transcription)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Calculate average confidence as accuracy estimate
        estimated_accuracy = min(95.0, max(60.0, confidence * 100))
        
        # Build result
        result = {
            "text": transcription,
            "segments": [{
                "start": 0.0,
                "end": duration,
                "text": transcription,
                "confidence": round(confidence, 3)
            }],
            "language": "el",
            "language_probability": 0.99,
            "duration": duration,
            "model": "wav2vec2-large-xlsr-53-greek",
            "metadata": {
                "processing_time_ms": round(processing_time, 1),
                "device": self.device,
                "accuracy": round(estimated_accuracy, 1),
                "memory_managed": True,
                "single_processing": True,
                "wer_expectation": "10.50%",
                "cer_expectation": "2.88%"
            }
        }
        
        logger.info(f"✅ wav2vec2 single transcription complete: '{transcription}' ({len(transcription)} chars)")
        return result
    
    def _detect_speech_segments(self, audio_array: np.ndarray, sample_rate: int = 16000) -> List[Tuple[int, int]]:
        """Detect speech segments using energy-based VAD (Voice Activity Detection)"""
        try:
            # Try webrtcvad first (more accurate)
            import webrtcvad
            return self._webrtc_vad(audio_array, sample_rate)
        except ImportError:
            # Fallback to energy-based VAD
            return self._energy_based_vad(audio_array, sample_rate)
    
    def _webrtc_vad(self, audio_array: np.ndarray, sample_rate: int) -> List[Tuple[int, int]]:
        """WebRTC VAD implementation (most accurate)"""
        import webrtcvad
        
        # Convert to 16-bit PCM
        audio_int16 = (audio_array * 32767).astype(np.int16)
        
        vad = webrtcvad.Vad(2)  # Aggressiveness level 2 (0-3)
        
        frame_duration = 30  # ms
        frame_length = int(sample_rate * frame_duration / 1000)
        
        segments = []
        current_start = None
        
        for i in range(0, len(audio_int16) - frame_length, frame_length):
            frame = audio_int16[i:i + frame_length].tobytes()
            
            try:
                is_speech = vad.is_speech(frame, sample_rate)
                
                if is_speech and current_start is None:
                    current_start = i
                elif not is_speech and current_start is not None:
                    # End of speech segment
                    segments.append((current_start, i))
                    current_start = None
            except:
                # Frame issue, continue
                continue
        
        # Handle last segment
        if current_start is not None:
            segments.append((current_start, len(audio_int16)))
        
        return segments
    
    def _energy_based_vad(self, audio_array: np.ndarray, sample_rate: int) -> List[Tuple[int, int]]:
        """Energy-based VAD fallback"""
        # Calculate frame energy
        frame_length = int(sample_rate * 0.025)  # 25ms frames
        hop_length = int(sample_rate * 0.010)    # 10ms hop
        
        # Calculate RMS energy for each frame
        energies = []
        for i in range(0, len(audio_array) - frame_length, hop_length):
            frame = audio_array[i:i + frame_length]
            energy = np.sqrt(np.mean(frame ** 2))
            energies.append(energy)
        
        # Threshold based on median energy
        energies = np.array(energies)
        threshold = np.median(energies) * 1.5  # Adaptive threshold
        
        # Find speech segments
        is_speech = energies > threshold
        
        segments = []
        current_start = None
        
        for i, speech in enumerate(is_speech):
            frame_start = i * hop_length
            
            if speech and current_start is None:
                current_start = frame_start
            elif not speech and current_start is not None:
                # End of speech segment
                segments.append((current_start, frame_start))
                current_start = None
        
        # Handle last segment
        if current_start is not None:
            segments.append((current_start, len(audio_array)))
        
        return segments
    
    def _merge_short_segments(self, segments: List[Tuple[int, int]], min_duration: float = 2.0, max_duration: float = 25.0, sample_rate: int = 16000) -> List[Tuple[int, int]]:
        """Merge short segments and split long ones for optimal processing"""
        min_samples = int(min_duration * sample_rate)
        max_samples = int(max_duration * sample_rate)
        
        merged_segments = []
        
        i = 0
        while i < len(segments):
            start, end = segments[i]
            current_duration = end - start
            
            # If segment is too short, try to merge with next segments
            if current_duration < min_samples and i < len(segments) - 1:
                # Look ahead to merge segments
                j = i + 1
                while j < len(segments) and (end - start) < max_samples:
                    next_start, next_end = segments[j]
                    # Merge if gap is small (< 1 second)
                    gap = next_start - end
                    if gap < sample_rate:  # 1 second gap
                        end = next_end
                        j += 1
                    else:
                        break
                
                merged_segments.append((start, end))
                i = j
            
            # If segment is too long, split it
            elif current_duration > max_samples:
                # Split into chunks at silence points if possible
                chunk_start = start
                while chunk_start < end:
                    chunk_end = min(chunk_start + max_samples, end)
                    merged_segments.append((chunk_start, chunk_end))
                    chunk_start = chunk_end
                i += 1
            
            # Segment is just right
            else:
                merged_segments.append((start, end))
                i += 1
        
        return merged_segments
    
    async def _transcribe_vad_chunked(self, audio_array: np.ndarray, duration: float, start_time: float) -> Dict[str, Any]:
        """VAD-based smart chunking - chunks at speech boundaries without overlap"""
        logger.info(f"🎯 VAD-based smart chunking for {duration:.1f}s audio")
        
        # Detect speech segments
        logger.info("🔍 Detecting speech segments...")
        speech_segments = self._detect_speech_segments(audio_array)
        logger.info(f"Found {len(speech_segments)} initial speech segments")
        
        # Merge and optimize segments
        optimized_segments = self._merge_short_segments(speech_segments)
        logger.info(f"Optimized to {len(optimized_segments)} processing chunks")
        
        text_parts = []
        segment_list = []
        chunk_counter = 0
        
        for segment_start, segment_end in optimized_segments:
            chunk_counter += 1
            
            # Extract audio chunk
            chunk_audio = audio_array[segment_start:segment_end]
            chunk_duration = len(chunk_audio) / 16000
            
            # Skip very short chunks (< 0.5 seconds)
            if chunk_duration < 0.5:
                logger.debug(f"Skipping short chunk {chunk_counter} ({chunk_duration:.2f}s)")
                continue
            
            try:
                logger.debug(f"Processing chunk {chunk_counter}/{len(optimized_segments)} ({chunk_duration:.2f}s)")
                
                # Process chunk with memory management
                input_dict = self.processor(
                    chunk_audio, 
                    return_tensors="pt", 
                    sampling_rate=16000
                )
                
                input_values = input_dict.input_values.to(self.device)
                
                with torch.no_grad():
                    logits = self.model(input_values).logits
                
                predicted_ids = torch.argmax(logits, dim=-1)
                chunk_text = self.processor.decode(predicted_ids[0])
                
                # Calculate confidence
                probabilities = torch.softmax(logits, dim=-1)
                confidence = torch.max(probabilities, dim=-1).values.mean().item()
                
                # Immediate cleanup after each chunk
                del input_values, logits, probabilities, predicted_ids
                import gc
                gc.collect()
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                
                chunk_text = self._clean_transcription(chunk_text)
                
                if chunk_text.strip():  # Only add non-empty chunks
                    text_parts.append(chunk_text)
                    
                    # Calculate timing in seconds
                    time_start = segment_start / 16000
                    time_end = segment_end / 16000
                    
                    segment_list.append({
                        "start": time_start,
                        "end": time_end,
                        "text": chunk_text,
                        "confidence": round(confidence, 3)
                    })
                    
                    logger.debug(f"✅ Chunk {chunk_counter}: '{chunk_text[:50]}...' ({confidence:.3f})")
                
                # Extra cleanup every 5 chunks
                if chunk_counter % 5 == 0:
                    for i in range(2):
                        gc.collect()
                        if self.device == "cuda":
                            torch.cuda.empty_cache()
                    
                    # Progress logging
                    progress = (chunk_counter / len(optimized_segments)) * 100
                    logger.info(f"🔄 VAD Progress: {progress:.1f}% ({chunk_counter}/{len(optimized_segments)} chunks)")
                
            except Exception as chunk_error:
                logger.warning(f"⚠️ VAD Chunk {chunk_counter} failed: {chunk_error} - skipping")
                # Continue with next chunk even if one fails
        
        # Final cleanup
        for i in range(3):
            import gc
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
        
        full_text = " ".join(text_parts).strip()
        processing_time = (time.time() - start_time) * 1000
        
        # Calculate average confidence
        avg_confidence = sum(seg["confidence"] for seg in segment_list) / len(segment_list) if segment_list else 0.0
        estimated_accuracy = min(95.0, max(60.0, avg_confidence * 100))
        
        result = {
            "text": full_text,
            "segments": segment_list,
            "language": "el",
            "language_probability": 0.99,
            "duration": duration,
            "model": "wav2vec2-large-xlsr-53-greek",
            "metadata": {
                "processing_time_ms": round(processing_time, 1),
                "device": self.device,
                "accuracy": round(estimated_accuracy, 1),
                "avg_confidence": round(avg_confidence, 3),
                "memory_managed": True,
                "vad_chunked_processing": True,
                "speech_segments_detected": len(speech_segments),
                "optimized_chunks_processed": len(segment_list),
                "vad_method": "webrtc" if self._has_webrtcvad() else "energy_based",
                "wer_expectation": "10.50%",
                "cer_expectation": "2.88%"
            }
        }
        
        logger.info(f"🚀 VAD-based transcription complete: {len(segment_list)} smart chunks, '{full_text[:100]}...' ({len(full_text)} chars)")
        return result
    
    def _has_webrtcvad(self) -> bool:
        """Check if webrtcvad is available"""
        try:
            import webrtcvad
            return True
        except ImportError:
            return False
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None and self.processor is not None
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current GPU memory usage"""
        try:
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated() / 1024**3  # GB
                cached = torch.cuda.memory_reserved() / 1024**3     # GB
                total = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
                return {
                    "allocated_gb": round(allocated, 2),
                    "cached_gb": round(cached, 2),
                    "total_gb": round(total, 2),
                    "free_gb": round(total - cached, 2),
                    "utilization_percent": round((cached / total) * 100, 1)
                }
            else:
                return {"error": "CUDA not available"}
        except Exception as e:
            return {"error": str(e)}
    
    def force_memory_cleanup(self) -> Dict[str, Any]:
        """Force aggressive memory cleanup without unloading model"""
        try:
            import gc
            
            # Multiple garbage collection passes
            collected_objects = 0
            for i in range(3):
                collected = gc.collect()
                collected_objects += collected
                if collected == 0:
                    break
            
            # GPU cache cleanup
            gpu_cleaned = False
            if self.device == "cuda":
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                gpu_cleaned = True
            
            result = {
                "status": "success",
                "collected_objects": collected_objects,
                "gpu_cache_cleared": gpu_cleaned,
            }
            
            # Add memory stats if available
            memory_stats = self.get_memory_usage()
            if "error" not in memory_stats:
                result["memory_after_cleanup"] = memory_stats
            
            logger.info(f"🧹 wav2vec2 force cleanup: {collected_objects} objects collected, GPU cache: {gpu_cleaned}")
            return result
            
        except Exception as e:
            logger.error(f"❌ wav2vec2 force cleanup failed: {e}")
            return {"status": "error", "message": str(e)}