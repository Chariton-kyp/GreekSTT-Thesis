"""
Whisper Model Implementation for Academic Research  
Using faster-whisper for Greek language processing
"""
import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class WhisperModel:
    """Whisper model using faster-whisper"""
    
    def __init__(self):
        self.model = None
        self.device = self._detect_device()
        self.model_name = "large-v3"
        self.implementation = None
        
    def _detect_device(self) -> str:
        """Detect available device for faster-whisper"""
        try:
            import torch
            if torch.cuda.is_available():
                # Test cuDNN compatibility
                try:
                    test_tensor = torch.randn(1, 1, 4, 4).cuda()
                    test_conv = torch.nn.Conv2d(1, 1, 3, padding=1).cuda()
                    _ = test_conv(test_tensor)
                    logger.info("CUDA and cuDNN working")
                    
                    # Test faster-whisper GPU compatibility
                    try:
                        from faster_whisper import WhisperModel
                        import ctranslate2
                        
                        logger.info(f"ctranslate2 version: {ctranslate2.__version__}")
                        
                        test_model = WhisperModel(
                            "tiny", 
                            device="cuda", 
                            compute_type="float16",
                            num_workers=1
                        )
                        
                        del test_model
                        import gc
                        gc.collect()
                        torch.cuda.empty_cache()
                        logger.info("faster-whisper GPU compatible")
                        return "cuda"
                    except Exception as fw_error:
                        logger.warning(f"faster-whisper GPU failed: {fw_error}")
                        if "cudnn" in str(fw_error).lower():
                            logger.info("cuDNN issue detected")
                        return "cpu"
                        
                except Exception as e:
                    logger.warning(f"CUDA available but cuDNN failed: {e}")
                    return "cpu"
            else:
                logger.info("CUDA not available")
                return "cpu"
        except ImportError:
            logger.info("PyTorch not available")
            return "cpu"
    
    async def load(self) -> None:
        """Load faster-whisper model"""
        try:
            logger.info("Loading faster-whisper 1.1.1")
            await self._load_faster_whisper()
            
        except Exception as e:
            logger.error(f"faster-whisper failed to load: {e}")
            raise RuntimeError(f"faster-whisper loading failed: {e}")
    
    async def _load_faster_whisper(self) -> None:
        """Load faster-whisper implementation"""
        from faster_whisper import WhisperModel
        import gc
        
        # Clean up any previous memory before loading
        gc.collect()
        if self.device == "cuda":
            try:
                import torch
                torch.cuda.empty_cache()
            except ImportError:
                pass
        
        logger.info(f"Loading faster-whisper {self.model_name} on {self.device} (PRIMARY)")
        
        # High quality settings - use float16 for better accuracy (was int8)
        if self.device == "cuda":
            # Use float16 for better quality (more memory but worth it for accuracy)
            compute_type = "float16"  # Better quality than int8
            # GPU optimizations for CUDA 12
            gpu_kwargs = {
                "device": self.device,
                "compute_type": compute_type,
                "num_workers": 1,  # Single worker for stability
                "cpu_threads": 2,  # Minimal CPU threads to assist GPU
            }
            logger.info(f"Using float16 precision for better quality (higher memory usage but better accuracy)")
        else:
            compute_type = "int8"  # Keep int8 for CPU processing
            gpu_kwargs = {
                "device": self.device,
                "compute_type": compute_type,
                "cpu_threads": 4,  # Limit CPU threads
                "num_workers": 1
            }
        
        # IMPORTANT: Use WhisperModel, NOT BatchedInferencePipeline (has segment bugs)
        self.model = WhisperModel(
            self.model_name,
            **gpu_kwargs
        )
        self.implementation = "faster-whisper"
        
        logger.info("faster-whisper model loaded successfully")
    
    def unload(self) -> None:
        """Unload Whisper model from memory"""
        try:
            if self.model:
                logger.info(f"Unloading {getattr(self, 'implementation', 'Whisper')} model from GPU memory...")
                
                # Store device for cleanup
                device_type = self.device
                
                # Implementation-specific cleanup
                if hasattr(self.model, '__dict__'):
                    # Clear internal model attributes if accessible
                    for attr_name in list(self.model.__dict__.keys()):
                        if 'model' in attr_name.lower() or 'weight' in attr_name.lower():
                            try:
                                delattr(self.model, attr_name)
                            except:
                                pass
                
                # Delete model
                del self.model
                self.model = None
                if hasattr(self, 'implementation'):
                    self.implementation = None
                
                # Import garbage collection
                import gc
                
                # Thorough garbage collection (5 passes)
                for i in range(5):
                    collected = gc.collect()
                    if collected == 0 and i > 2:  # Stop early if nothing to collect
                        break
                
                # Clear GPU cache if using CUDA with maximum aggression
                if device_type == "cuda":
                    try:
                        import torch
                        
                        # Multiple cleanup passes for thorough memory release
                        for i in range(3):
                            torch.cuda.empty_cache()
                            torch.cuda.synchronize()  # Wait for all operations
                            gc.collect()
                        
                        # Force PyTorch to release cached memory
                        if hasattr(torch.cuda, 'reset_max_memory_allocated'):
                            torch.cuda.reset_max_memory_allocated()
                        if hasattr(torch.cuda, 'reset_max_memory_cached'):
                            torch.cuda.reset_max_memory_cached()
                        
                        # Final aggressive cleanup
                        torch.cuda.empty_cache()
                        
                        # Log memory status
                        try:
                            allocated = torch.cuda.memory_allocated() / 1024**3
                            cached = torch.cuda.memory_reserved() / 1024**3
                            logger.info(f"GPU memory after cleanup: {allocated:.2f}GB allocated, {cached:.2f}GB cached")
                        except:
                            logger.info("GPU cache cleared")
                            
                    except ImportError:
                        pass
                
                logger.info("Whisper model unloaded")
            else:
                logger.info("Whisper model was not loaded")
                
        except Exception as e:
            logger.error(f"Error unloading Whisper model: {e}")
            # Force cleanup even if error occurred
            self.model = None
            if hasattr(self, 'implementation'):
                self.implementation = None
            import gc
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except:
                pass
    
    async def transcribe(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        """Transcribe audio file using faster-whisper"""
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        start_time = time.time()
        
        # Log audio duration for reference
        try:
            import librosa
            audio_duration = librosa.get_duration(path=audio_path)
            duration_minutes = audio_duration / 60
            logger.info(f"Audio duration: {audio_duration:.1f}s ({duration_minutes:.1f} min)")
            
        except Exception as e:
            logger.warning(f"Duration detection failed: {e}")
        
        logger.info(f"Transcribing with faster-whisper: {Path(audio_path).name}")
        
        try:
            return await self._transcribe_faster_whisper(audio_path, start_time, **kwargs)
                
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ faster-whisper failed after {processing_time:.0f}ms: {e}")
            raise
    
    async def _transcribe_faster_whisper(self, audio_path: str, start_time: float, **kwargs) -> Dict[str, Any]:
        """Transcribe using faster-whisper with video conversion"""
        from app.utils.audio_converter import AudioConverter
        
        # Audio conversion for video containers
        temp_audio_path = None
        processing_path = audio_path
        original_video_duration = None
        
        preprocessed_audio_path = None
        
        try:
            # If it's a video file, get the original duration first
            if AudioConverter.is_video_container(audio_path):
                from app.utils.audio_converter import get_video_duration
                original_video_duration = get_video_duration(audio_path)
                logger.info(f"📹 Original video duration: {original_video_duration:.2f}s ({original_video_duration/60:.1f}min)")
            
            # Check if we need to convert video to audio
            temp_audio_path = AudioConverter.smart_convert(audio_path, target_sample_rate=16000)
            if temp_audio_path:
                processing_path = temp_audio_path
                logger.info(f"🎬 Using converted audio file for faster-whisper processing")
                
            # Apply anti-hallucination preprocessing to remove silence at start
            from app.utils.audio_converter import preprocess_audio_for_whisper
            preprocessed_audio_path = preprocess_audio_for_whisper(processing_path, target_sample_rate=16000)
            if preprocessed_audio_path != processing_path:
                processing_path = preprocessed_audio_path
                logger.info(f"🧹 Using preprocessed audio to prevent start-of-audio hallucinations")
                
        except Exception as e:
            logger.warning(f"Audio conversion/preprocessing failed, using original file: {e}")
            # Continue with original file if conversion fails
        
        try:
            # Anti-hallucination settings based on 2024 research
            settings = {
                "language": "el",  # Greek language code
                "task": "transcribe",
                "beam_size": 10,  # Keep user requested beam_size=10 for accuracy
                "best_of": 1,  # Single hypothesis to avoid repetitive patterns
                "patience": 1.0,
                "length_penalty": 1.0,
                "temperature": 0.0,  # Single temperature for more deterministic results
                
                # CRITICAL: Anti-hallucination parameters based on research
                "compression_ratio_threshold": 2.0,  # Balanced for Greek text (was too strict at 1.35)
                "no_speech_threshold": 0.2,  # Lower = more aggressive silence detection (was 0.5)
                "hallucination_silence_threshold": 2.5,  # Skip long silences when hallucinating
                "condition_on_previous_text": False,  # MOST IMPORTANT: Prevents 90% of hallucinations
                
                # VAD settings for preventing start-of-audio hallucinations
                "vad_filter": True,  # Essential for hallucination prevention
                "vad_parameters": {
                    "threshold": 0.5,
                    "min_speech_duration_ms": 500,  # Longer minimum to avoid noise
                    "max_speech_duration_s": 30,  # Split long segments to prevent context poisoning
                    "min_silence_duration_ms": 2000,  # Longer silence detection
                    "speech_pad_ms": 400,  # More padding for context
                },
                
                # Greek language optimization
                "initial_prompt": "",  # NO initial prompt to avoid hallucination anchoring
                "word_timestamps": True,  # Enable for natural pause detection
                "max_new_tokens": None,  # Let it find natural breaks
                "chunk_length": None,  # Process full audio to find natural pauses
            }
            
            settings.update(kwargs)
            
            # Pre-transcription memory cleanup for consistent results
            import gc
            gc.collect()
            if self.device == "cuda":
                try:
                    import torch
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()  # Ensure all operations complete
                except ImportError:
                    pass
            
            logger.info("Pre-transcription cleanup complete, starting processing...")
            
            # Transcribe with memory management
            try:
                segments_generator, info = self.model.transcribe(processing_path, **settings)
                
                # CRITICAL: Process segments in order as they come
                segments = []
                segment_index = 0
                
                for segment in segments_generator:
                    # Log each segment as it's generated
                    logger.info(f"Segment {segment_index}: [{segment.start:.2f}s - {segment.end:.2f}s] = '{segment.text.strip()}'")
                    segments.append(segment)
                    segment_index += 1
                    
                logger.info(f"Generated {len(segments)} segments from audio")
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                raise
            
            # Debug: Check segment integrity
            logger.info("Checking segment order and gaps:")
            prev_end = 0.0
            for i, seg in enumerate(segments):
                gap = seg.start - prev_end
                if gap > 0.5:  # More than 0.5s gap
                    logger.warning(f"  Large gap detected: {gap:.2f}s between segments {i-1} and {i}")
                if seg.start < prev_end:
                    logger.error(f"  OVERLAPPING segments! Seg {i} starts at {seg.start:.2f}s but previous ended at {prev_end:.2f}s")
                prev_end = seg.end
            
            # Process results with periodic memory cleanup
            text_parts = []
            segment_list = []
            chunk_counter = 0
            
            # Check if segments are already in correct chronological order
            # faster-whisper should generate segments in correct order by default
            order_check_failed = False
            prev_start = -1.0
            for i, seg in enumerate(segments):
                if seg.start < prev_start:
                    order_check_failed = True
                    logger.warning(f"  Segment {i} out of order: {seg.start:.2f}s < previous {prev_start:.2f}s")
                prev_start = seg.start
            
            # Only sort if there's actually an ordering problem
            if order_check_failed:
                logger.warning("SEGMENTS OUT OF ORDER - applying chronological sorting")
                segments_before = [(i, s.start, s.text[:30] + "...") for i, s in enumerate(segments)]
                segments = sorted(segments, key=lambda s: s.start)
                segments_after = [(i, s.start, s.text[:30] + "...") for i, s in enumerate(segments)]
                
                logger.warning("Before sorting:")
                for i, start, text in segments_before[:5]:  # Show first 5
                    logger.warning(f"    Seg {i}: {start:.2f}s = '{text}'")
                logger.warning("After sorting:")
                for i, start, text in segments_after[:5]:  # Show first 5
                    logger.warning(f"    Seg {i}: {start:.2f}s = '{text}'")
            else:
                logger.info("Segments already in correct chronological order - no sorting needed")
            
            # Remove overlapping segments (keep the first one)
            filtered_segments = []
            last_end_time = -1.0
            overlap_count = 0
            
            for i, segment in enumerate(segments):
                # Skip if this segment starts before the last one ended (overlap)
                if segment.start < last_end_time - 0.1:  # 0.1s tolerance
                    overlap_count += 1
                    logger.warning(f"  Removing overlapping segment {i}: [{segment.start:.2f}s-{segment.end:.2f}s] '{segment.text.strip()}'")
                    logger.warning(f"     (Previous segment ended at {last_end_time:.2f}s)")
                    continue
                    
                filtered_segments.append(segment)
                last_end_time = segment.end
            
            segments = filtered_segments
            logger.info(f"Filtering complete: {len(segments)} segments remain (removed {overlap_count} overlapping)")
            
            # Process segments with natural break detection
            segments = self._process_with_natural_breaks(segments)
            logger.info(f"Natural break processing complete: {len(segments)} final segments")
            
            for segment in segments:
                # Anti-hallucination: Skip segments with repetitive patterns
                segment_text = segment.text.strip()
                
                # Check for repetitive watermarks like "Υπότιτλοι AUTHORWAVE"
                if self._is_repetitive_hallucination(segment_text):
                    logger.warning(f"Skipping hallucination segment: '{segment_text[:50]}...'")
                    continue
                    
                text_parts.append(segment_text)
                segment_list.append({
                    "text": segment_text,
                    "start": segment.start,
                    "end": segment.end,
                    "confidence": getattr(segment, 'avg_logprob', 0.9)
                })
                
                # Aggressive memory cleanup every 10 segments to prevent accumulation
                chunk_counter += 1
                if chunk_counter % 10 == 0:
                    import gc
                    gc.collect()
                    if self.device == "cuda":
                        try:
                            import torch
                            torch.cuda.empty_cache()
                        except ImportError:
                            pass
            
            full_text = " ".join(text_parts).strip()
            
            # Remove AUTHORWAVE watermarks from final text
            full_text = self._clean_authorwave_from_text(full_text)
            
            # Final hallucination check on complete text
            if self._is_only_hallucination(full_text):
                logger.warning("Entire transcription appears to be hallucination, returning empty")
                full_text = ""
                segment_list = []
            
            # Debug: Log segment order in final result
            logger.info("Final segment order verification:")
            for i, seg in enumerate(segment_list[:5]):  # Show first 5 segments
                logger.info(f"    Final Seg {i}: [{seg['start']:.2f}s-{seg['end']:.2f}s] = '{seg['text'][:50]}{'...' if len(seg['text']) > 50 else ''}'")
            
            # Log final assembled text (first 200 chars)
            logger.info(f"Final transcription ({len(full_text)} chars): '{full_text[:200]}{'...' if len(full_text) > 200 else ''}'")
            logger.info(f"Segments in final output: {len(segment_list)}")
            
            # Debug: Check if final text matches expected order
            if segment_list and len(segment_list) > 1:
                first_segment_text = segment_list[0]['text'].strip()
                if first_segment_text and not full_text.startswith(first_segment_text[:20]):
                    logger.error("SEGMENT ORDER MISMATCH!")
                    logger.error(f"    First segment: '{first_segment_text[:50]}'")
                    logger.error(f"    Full text starts: '{full_text[:50]}'")
                    logger.error(f"    Expected match but texts don't align!")
                
            processing_time = (time.time() - start_time) * 1000
            
            # Calculate average confidence as accuracy estimate
            avg_confidence = sum(seg["confidence"] for seg in segment_list) / len(segment_list) if segment_list else 0.0
            estimated_accuracy = min(95.0, max(60.0, avg_confidence * 100))
            
            # Use original video duration if available, otherwise use processed duration
            final_duration = original_video_duration if original_video_duration and original_video_duration > 0 else info.duration
            
            result = {
                "text": full_text,
                "segments": segment_list,
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": final_duration,
                "model": f"whisper-{self.model_name}",
                "metadata": {
                    "processing_time_ms": processing_time,
                    "device": self.device,
                    "implementation": "whisper",
                    "version": "1.1.1",
                    "academic_mode": True,
                    "accuracy": round(estimated_accuracy, 1),
                    "avg_confidence": round(avg_confidence, 3),
                    "segment_count": len(segment_list),
                    "greek_optimized": True,
                    "anti_hallucination": True,
                    "vad_enabled": True,  # Enabled with natural break parameters
                    "natural_breaks": True,  # Using pause detection for segments
                    "repetition_filter": True,
                    "segment_sorting": True,
                    "overlap_removal": True,
                    "word_timestamps": True,
                    "single_implementation": True,
                    "original_video_duration": original_video_duration,  # Store original duration
                    "was_video_file": AudioConverter.is_video_container(audio_path)
                }
            }
            
            # Add video-specific metadata if this was a video conversion
            if AudioConverter.is_video_container(audio_path):
                result["metadata"]["was_video_converted"] = temp_audio_path is not None
                result["metadata"]["actual_audio_duration"] = final_duration
                if original_video_duration:
                    result["metadata"]["video_duration_source"] = "original_file"
                    logger.info(f"Using original video duration: {final_duration:.2f}s for final result")
            
            logger.info(f"faster-whisper complete: {len(full_text)} chars in {processing_time:.0f}ms")
            return result
            
        finally:
            # Cleanup temporary audio files if created
            if temp_audio_path:
                AudioConverter.cleanup_temp_file(temp_audio_path)
            if preprocessed_audio_path and preprocessed_audio_path != audio_path and preprocessed_audio_path != temp_audio_path:
                AudioConverter.cleanup_temp_file(preprocessed_audio_path)
    
    def _is_repetitive_hallucination(self, text: str) -> bool:
        """
        Detect common Whisper hallucinations and repetitive patterns
        Fixed to be less aggressive and preserve valid Greek content
        """
        if not text or len(text.strip()) < 2:
            return True
            
        text_lower = text.lower().strip()
        
        # Detect AUTHORWAVE watermarks and common hallucination patterns
        watermark_patterns = [
            "υπότιτλοι authorwave",
            "υποτιτλοι authorwave",
            "subtitles authorwave", 
            "subtitles by authorwave",
            "transcribed by authorwave",
            "powered by authorwave",
            "www.authorwave",
            "authorwave.com",
            "subscribe to authorwave",
            "like and subscribe",
            "follow us on",
            "visit our website"
        ]
        
        # Check for watermark patterns (exact match or starts/contains)
        for pattern in watermark_patterns:
            if (text_lower == pattern or 
                text_lower.startswith(pattern) or 
                text_lower.endswith(pattern) or
                (len(pattern) > 10 and pattern in text_lower)):  # For longer patterns like "υπότιτλοι authorwave"
                return True
        
        # Special check for AUTHORWAVE variations
        if "authorwave" in text_lower:
            return True
        
        # Only flag if same word repeats 4+ times consecutively (not 3)
        words = text_lower.split()
        if len(words) >= 4:
            for i in range(len(words) - 3):
                if words[i] == words[i+1] == words[i+2] == words[i+3] and len(words[i]) > 2:
                    return True
        
        # Only flag very obvious filler sounds (not valid Greek words)
        if len(text.strip()) <= 5 and text_lower in ["...", "μμμ", "εεε", "ααα", "ωωω", "thank you"]:
            return True
        
        # Flag if segment is just single character repeated
        if len(set(text_lower.replace(" ", ""))) == 1 and len(text_lower.replace(" ", "")) > 3:
            return True
            
        return False
    
    def _clean_authorwave_from_text(self, text: str) -> str:
        """
        Remove AUTHORWAVE watermarks from final transcription text
        """
        if not text:
            return text
            
        # Patterns to remove from the beginning of transcription
        watermark_patterns = [
            r"Υπότιτλοι\s+AUTHORWAVE\s*",
            r"υπότιτλοι\s+authorwave\s*",
            r"Subtitles\s+AUTHORWAVE\s*",
            r"subtitles\s+authorwave\s*",
            r"AUTHORWAVE\s*",
            r"authorwave\s*"
        ]
        
        import re
        cleaned_text = text
        
        for pattern in watermark_patterns:
            # Remove from beginning of text (case insensitive)
            cleaned_text = re.sub(f"^{pattern}", "", cleaned_text, flags=re.IGNORECASE).strip()
            # Remove standalone occurrences
            cleaned_text = re.sub(f"\\b{pattern}\\b", " ", cleaned_text, flags=re.IGNORECASE).strip()
        
        # Clean up extra whitespace
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        if cleaned_text != text:
            logger.info("Cleaned AUTHORWAVE watermark from transcription")
            logger.debug(f"   Before: '{text[:100]}...'")
            logger.debug(f"   After:  '{cleaned_text[:100]}...'")
        
        return cleaned_text
    
    def _is_only_hallucination(self, text: str) -> bool:
        """
        Check if the entire transcription is just hallucination
        """
        if not text:
            return False
            
        # Remove all hallucination patterns and see if anything is left
        cleaned_text = text.lower()
        
        # Remove known hallucination patterns
        hallucination_phrases = [
            "υπότιτλοι authorwave",
            "υποτιτλοι authorwave",
            "subtitles by",
            "transcribed by",
            "powered by"
        ]
        
        for phrase in hallucination_phrases:
            cleaned_text = cleaned_text.replace(phrase, "")
        
        # Remove punctuation and whitespace
        cleaned_text = cleaned_text.strip()
        
        # If nothing meaningful is left, it's all hallucination
        if len(cleaned_text) < 5:  # Less than 5 characters remaining
            return True
            
        # Check if it's just repetition of the same short phrase
        words = cleaned_text.split()
        if len(set(words)) <= 2:  # Only 1-2 unique words
            return True
            
        return False
    
    def _process_with_natural_breaks(self, segments: list) -> list:
        """
        Process segments to respect natural speech breaks
        Uses word timestamps to detect pauses and merge/split segments accordingly
        """
        if not segments:
            return segments
            
        processed_segments = []
        current_text = []
        current_start = None
        current_end = None
        
        for segment in segments:
            # If segment has word timestamps, use them for better processing
            if hasattr(segment, 'words') and segment.words:
                for i, word in enumerate(segment.words):
                    # Start new segment if needed
                    if current_start is None:
                        current_start = word.start
                        
                    # Check for natural pause (gap between words)
                    if i > 0:
                        prev_word = segment.words[i-1]
                        pause_duration = word.start - prev_word.end
                        
                        # Natural break detected (300ms+ pause or punctuation)
                        if pause_duration > 0.3 or prev_word.word.rstrip().endswith(('.', '!', '?', ';')):
                            # Save current segment
                            if current_text:
                                processed_segments.append({
                                    'start': current_start,
                                    'end': prev_word.end,
                                    'text': ' '.join(current_text)
                                })
                                logger.debug(f"  📍 Natural break segment: [{current_start:.2f}-{prev_word.end:.2f}] after '{prev_word.word}'")
                            
                            # Start new segment
                            current_text = [word.word]
                            current_start = word.start
                        else:
                            current_text.append(word.word)
                    else:
                        current_text.append(word.word)
                    
                    current_end = word.end
            else:
                # No word timestamps - use segment as-is but check duration
                if segment.end - segment.start > 30.0:  # Too long, needs splitting
                    logger.warning(f"  ⚠️ Long segment without word timestamps: {segment.end - segment.start:.1f}s")
                
                # Check if we should merge with previous
                if processed_segments and segment.start - current_end < 0.2:  # Less than 200ms gap
                    # Merge with previous
                    processed_segments[-1]['end'] = segment.end
                    processed_segments[-1]['text'] += ' ' + segment.text.strip()
                    logger.debug(f"  🔗 Merged segment due to small gap")
                else:
                    # Add as new segment
                    processed_segments.append({
                        'start': segment.start,
                        'end': segment.end,
                        'text': segment.text.strip()
                    })
                current_end = segment.end
                
        # Don't forget last segment if using word timestamps
        if current_text and current_start is not None:
            processed_segments.append({
                'start': current_start,
                'end': current_end,
                'text': ' '.join(current_text)
            })
        
        # Convert back to segment-like objects
        class ProcessedSegment:
            def __init__(self, start, end, text):
                self.start = start
                self.end = end
                self.text = text
                
        return [ProcessedSegment(**seg) for seg in processed_segments]
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current GPU memory usage"""
        try:
            import torch
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
                try:
                    import torch
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                    gpu_cleaned = True
                except ImportError:
                    pass
            
            result = {
                "status": "success",
                "collected_objects": collected_objects,
                "gpu_cache_cleared": gpu_cleaned,
            }
            
            # Add memory stats if available
            memory_stats = self.get_memory_usage()
            if "error" not in memory_stats:
                result["memory_after_cleanup"] = memory_stats
            
            logger.info(f"Force cleanup: {collected_objects} objects collected, GPU cache: {gpu_cleaned}")
            return result
            
        except Exception as e:
            logger.error(f"Force cleanup failed: {e}")
            return {"status": "error", "message": str(e)}
