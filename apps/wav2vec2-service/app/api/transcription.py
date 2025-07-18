"""
wav2vec2 ASR API endpoints for GreekSTT Research Platform
Handles only wav2vec2 transcription
"""
import logging
import tempfile
import os
from typing import Dict, Any, List, Tuple
from pathlib import Path
import numpy as np

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse

from app.utils.audio_converter import AudioConverter

try:
    import torch
except ImportError:
    torch = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["wav2vec2 Transcription"])


async def transcribe_with_wav2vec2(processor, model, device: str, audio_path: str, filename: str) -> Dict[str, Any]:
    """Transcribe audio with wav2vec2 model using VAD-based intelligent chunking
    
    Args:
        processor: wav2vec2 processor instance
        model: wav2vec2 model instance
        device: Target device (cuda/cpu)
        audio_path: Path to audio file
        filename: Original filename for result metadata
        
    Returns:
        Dict containing transcription results and metadata
    """
    import time
    import librosa
    import torch
    import numpy as np
    from typing import List, Tuple
    
    start_time = time.time()
    logger.info(f"Starting wav2vec2 transcription for {filename} at {start_time}")
    
    audio_array, sample_rate = librosa.load(audio_path, sr=16000)
    duration = len(audio_array) / sample_rate
    
    logger.info(f"Audio loaded: duration={duration:.2f}s, sample_rate={sample_rate}")
    
    if duration <= 30.0:
        logger.info("Using single chunk processing (≤30s)")
        result = await _transcribe_single_wav2vec2(processor, model, device, audio_array, duration, filename)
    else:
        logger.info("Using long audio processing (>30s)")
        result = await _transcribe_long_wav2vec2(processor, model, device, audio_array, duration, filename)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Calculate Real-Time Factor (RTF)
    rtf = processing_time / duration if duration > 0 else 0
    
    result["processing_time"] = processing_time
    result["metadata"]["processing_time_seconds"] = processing_time
    
    logger.info(f"wav2vec2 transcription completed:")
    logger.info(f"  - Audio duration: {duration:.2f}s")
    logger.info(f"  - Processing time: {processing_time:.2f}s")
    logger.info(f"  - RTF (Real-Time Factor): {rtf:.3f}")
    logger.info(f"  - Speed: {duration/processing_time:.1f}x faster than real-time" if processing_time > 0 else "  - Speed: N/A")
    logger.info(f"  - Text length: {len(result['text'])} characters")
    
    return result


async def _transcribe_single_wav2vec2(processor, model, device: str, audio_array: np.ndarray, duration: float, filename: str) -> Dict[str, Any]:
    """Transcribe single audio file (≤30 seconds)
    
    Args:
        processor: wav2vec2 processor instance
        model: wav2vec2 model instance
        device: Target device (cuda/cpu)
        audio_array: Audio data as numpy array
        duration: Audio duration in seconds
        filename: Original filename for result metadata
        
    Returns:
        Dict containing transcription results and metadata
    """
    import torch
    
    input_dict = processor(
        audio_array, 
        return_tensors="pt", 
        sampling_rate=16000
    )
    
    input_values = input_dict.input_values.to(device)
    
    with torch.no_grad():
        logits = model(input_values).logits
    
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.decode(predicted_ids[0])
    
    probabilities = torch.softmax(logits, dim=-1)
    confidence = torch.max(probabilities, dim=-1).values.mean().item()
    
    del input_values, logits, probabilities, predicted_ids
    import gc
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
    
    transcription = _clean_wav2vec2_transcription(transcription)
    
    estimated_accuracy = min(95.0, max(60.0, confidence * 100))
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
        "filename": filename,
        "metadata": {
            "model": "wav2vec2-large-xlsr-53-greek",
            "service": "wav2vec2-service",
            "device": device,
            "accuracy": round(estimated_accuracy, 1),
            "memory_managed": True,
            "single_processing": True,
            "vad_chunking": False,
            "duration_seconds": duration,
            "greek_optimized": True
        }
    }
    
    return result


async def _transcribe_long_wav2vec2(processor, model, device: str, audio_array: np.ndarray, duration: float, filename: str) -> Dict[str, Any]:
    """Transcribe long audio file (>30 seconds) using VAD-based chunking"""
    import torch
    
    # Detect speech segments using VAD (consistent with original asr-service)
    speech_segments = _detect_speech_segments_wav2vec2(audio_array, sample_rate=16000)
    
    if not speech_segments:
        # No speech detected, return empty transcription
        return {
            "text": "",
            "segments": [],
            "language": "el",
            "language_probability": 0.99,
            "duration": duration,
            "filename": filename,
            "metadata": {
                "model": "wav2vec2-large-xlsr-53-greek",
                "service": "wav2vec2-service",
                "device": device,
                "vad_chunking": True,
                "segments_detected": 0,
                "duration_seconds": duration,
                "greek_optimized": True
            }
        }
    
    # Merge short segments (consistent with original asr-service max_duration=25.0)
    merged_segments = _merge_short_segments_wav2vec2(speech_segments, max_duration=25.0, min_duration=2.0)
    
    transcriptions = []
    all_segments = []
    
    # Process each segment
    for start_idx, end_idx in merged_segments:
        segment_audio = audio_array[start_idx:end_idx]
        segment_duration = len(segment_audio) / 16000
        
        # Process segment
        input_dict = processor(
            segment_audio, 
            return_tensors="pt", 
            sampling_rate=16000
        )
        
        input_values = input_dict.input_values.to(device)
        
        with torch.no_grad():
            logits = model(input_values).logits
        
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = processor.decode(predicted_ids[0])
        
        # Calculate confidence
        probabilities = torch.softmax(logits, dim=-1)
        confidence = torch.max(probabilities, dim=-1).values.mean().item()
        
        # Cleanup
        del input_values, logits, probabilities, predicted_ids
        
        # Clean transcription
        transcription = _clean_wav2vec2_transcription(transcription)
        
        if transcription.strip():  # Only add non-empty transcriptions
            transcriptions.append(transcription)
            all_segments.append({
                "start": start_idx / 16000,
                "end": end_idx / 16000,
                "text": transcription,
                "confidence": round(confidence, 3)
            })
    
    # Cleanup after all segments
    import gc
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
    
    # Combine all transcriptions
    full_text = " ".join(transcriptions)
    
    # Build result
    result = {
        "text": full_text,
        "segments": all_segments,
        "language": "el",
        "language_probability": 0.99,
        "duration": duration,
        "filename": filename,
        "metadata": {
            "model": "wav2vec2-large-xlsr-53-greek",
            "service": "wav2vec2-service",
            "device": device,
            "vad_chunking": True,
            "segments_detected": len(speech_segments),
            "segments_merged": len(merged_segments),
            "segments_processed": len(transcriptions),
            "duration_seconds": duration,
            "greek_optimized": True
        }
    }
    
    return result


def _clean_wav2vec2_transcription(text: str) -> str:
    """Clean transcription following model recommendations (consistent with original asr-service)"""
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Convert to lowercase (as recommended)
    text = text.lower()
    
    # Basic Greek text normalization
    import unicodedata
    text = unicodedata.normalize('NFC', text)
    
    return text.strip()


def _detect_speech_segments_wav2vec2(audio_array: np.ndarray, sample_rate: int = 16000) -> List[Tuple[int, int]]:
    """Detect speech segments using energy-based VAD (Voice Activity Detection)"""
    try:
        # Try webrtcvad first (more accurate)
        import webrtcvad
        return _webrtc_vad_wav2vec2(audio_array, sample_rate)
    except ImportError:
        # Fallback to energy-based VAD
        return _energy_based_vad_wav2vec2(audio_array, sample_rate)


def _energy_based_vad_wav2vec2(audio_array: np.ndarray, sample_rate: int) -> List[Tuple[int, int]]:
    """Fallback energy-based VAD implementation"""
    import numpy as np
    
    # Calculate energy in frames
    frame_length = int(0.025 * sample_rate)  # 25ms frames
    hop_length = int(0.010 * sample_rate)    # 10ms hop
    
    energy = []
    for i in range(0, len(audio_array) - frame_length, hop_length):
        frame = audio_array[i:i + frame_length]
        energy.append(np.sum(frame ** 2))
    
    # Threshold for speech detection
    energy = np.array(energy)
    threshold = np.mean(energy) * 1.5
    
    # Find speech segments
    is_speech = energy > threshold
    segments = []
    
    start = None
    for i, speech in enumerate(is_speech):
        if speech and start is None:
            start = i * hop_length
        elif not speech and start is not None:
            end = i * hop_length
            segments.append((start, end))
            start = None
    
    # Handle case where audio ends with speech
    if start is not None:
        segments.append((start, len(audio_array)))
    
    return segments


def _webrtc_vad_wav2vec2(audio_array: np.ndarray, sample_rate: int) -> List[Tuple[int, int]]:
    """More accurate VAD using webrtcvad (if available)"""
    import webrtcvad
    import numpy as np
    
    vad = webrtcvad.Vad(2)  # Aggressiveness level 2
    
    # Convert to 16-bit PCM
    audio_int16 = (audio_array * 32767).astype(np.int16)
    
    # Process in 30ms frames (webrtcvad requirement)
    frame_duration = 30  # ms
    frame_length = int(sample_rate * frame_duration / 1000)
    
    segments = []
    start = None
    
    for i in range(0, len(audio_int16) - frame_length, frame_length):
        frame = audio_int16[i:i + frame_length].tobytes()
        
        try:
            is_speech = vad.is_speech(frame, sample_rate)
            
            if is_speech and start is None:
                start = i
            elif not is_speech and start is not None:
                segments.append((start, i))
                start = None
        except Exception:
            # If webrtcvad fails, skip this frame
            continue
    
    # Handle case where audio ends with speech
    if start is not None:
        segments.append((start, len(audio_int16)))
    
    return segments


def _merge_short_segments_wav2vec2(segments: List[Tuple[int, int]], max_duration: float = 25.0, min_duration: float = 2.0, sample_rate: int = 16000) -> List[Tuple[int, int]]:
    """Merge short segments and split long ones (consistent with original asr-service)"""
    if not segments:
        return []
    
    merged = []
    current_start, current_end = segments[0]
    
    for start, end in segments[1:]:
        current_duration = (current_end - current_start) / sample_rate
        gap_duration = (start - current_end) / sample_rate
        new_duration = (end - current_start) / sample_rate
        
        # Merge if:
        # 1. Current segment is too short
        # 2. Gap is small (≤1 second)
        # 3. Combined duration doesn't exceed max_duration
        if (current_duration < min_duration or gap_duration <= 1.0) and new_duration <= max_duration:
            current_end = end
        else:
            # Check if current segment meets minimum duration
            if current_duration >= min_duration:
                merged.append((current_start, current_end))
            current_start, current_end = start, end
    
    # Add the last segment if it meets minimum duration
    final_duration = (current_end - current_start) / sample_rate
    if final_duration >= min_duration:
        merged.append((current_start, current_end))
    
    return merged


@router.post("/transcribe")
async def transcribe_wav2vec2(
    file: UploadFile = File(...),
    request: Request = None
) -> JSONResponse:
    """Transcribe audio using wav2vec2 only"""
    
    # Extract transcription_id from headers for callback support
    transcription_id = request.headers.get("X-Transcription-ID") if request else None
    
    logger.info(f"wav2vec2 endpoint received file: '{file.filename}' | content_type: {file.content_type}")
    if transcription_id:
        logger.info(f"Transcription ID: {transcription_id} (callback enabled)")
    
    # Validate file
    if not file.filename:
        logger.error("No filename provided")
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file format (audio + video containers with audio)
    allowed_formats = {
        # Pure audio formats
        '.wav', '.mp3', '.m4a', '.flac', '.ogg', '.opus', '.wma', '.aac',
        # Video containers with audio (librosa can extract audio)
        '.webm', '.mkv', '.mp4', '.avi', '.mov'
    }
    file_ext = Path(file.filename).suffix.lower()
    logger.info(f"File extension detected: '{file_ext}' from filename '{file.filename}'")
    
    if file_ext not in allowed_formats:
        logger.error(f"Unsupported format: '{file_ext}' | filename: '{file.filename}'")
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported format: {file_ext}. Supported: {allowed_formats}"
        )
    
    # Save temp file and process
    temp_file = None
    converted_audio_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        logger.info(f"Processing {file.filename} with wav2vec2")
        
        # Check if we need to convert video to audio
        processing_path = temp_path
        if AudioConverter.is_video_container(temp_path):
            logger.info(f"🎬 Video file detected, converting to audio...")
            converted_audio_path = AudioConverter.smart_convert(temp_path)
            if converted_audio_path:
                processing_path = converted_audio_path
                logger.info(f"✅ Using converted audio: {processing_path}")
        
        # Use pre-loaded wav2vec2 model from app state
        processor = getattr(request.app.state, 'wav2vec2_processor', None)
        model = getattr(request.app.state, 'wav2vec2_model', None)
        device = getattr(request.app.state, 'device', 'cpu')
        
        if processor is None or model is None:
            # Fallback to manual loading if pre-loading failed
            logger.warning("⚠️ Pre-loaded models not found, loading manually...")
            from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
            import torch
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            processor = Wav2Vec2Processor.from_pretrained(
                "lighteternal/wav2vec2-large-xlsr-53-greek",
                cache_dir="/app/models/wav2vec2"
            )
            model = Wav2Vec2ForCTC.from_pretrained(
                "lighteternal/wav2vec2-large-xlsr-53-greek",
                cache_dir="/app/models/wav2vec2"
            ).to(device)
        
        # Transcribe with wav2vec2 model
        result = await transcribe_with_wav2vec2(processor, model, device, processing_path, file.filename)
        result["filename"] = file.filename
        result["metadata"]["transformers_version"] = "4.36.0"
        result["metadata"]["service"] = "wav2vec2-service"
        
        # Add video file metadata and duration info
        if AudioConverter.is_video_container(temp_path):
            # Get original video duration first
            from app.utils.audio_converter import get_video_duration
            original_duration = get_video_duration(temp_path)
            
            # If we converted audio, also get the converted audio duration
            if converted_audio_path:
                from app.utils.audio_converter import get_audio_info
                converted_duration, actual_sample_rate = get_audio_info(converted_audio_path)
                result["metadata"]["was_video_converted"] = True
                result["metadata"]["converted_audio_duration"] = converted_duration
            else:
                result["metadata"]["was_video_converted"] = False
            
            # Use original video duration as primary
            result["metadata"]["original_video_duration"] = original_duration
            result["metadata"]["actual_audio_duration"] = original_duration  # For backward compatibility
            result["metadata"]["was_video_file"] = True
            result["metadata"]["original_video_file"] = file.filename
            result["metadata"]["video_duration_source"] = "original_file"
            
            logger.info(f"📊 Video file metadata: original duration {original_duration:.2f}s ({original_duration/60:.1f}min)")
        
        # Send callback if transcription_id provided (fire-and-forget)
        if transcription_id:
            from app.services.callback_service import callback_service
            import asyncio
            asyncio.create_task(
                callback_service.notify_completion_async(transcription_id, result)
            )
            logger.info(f"✅ Callback queued for transcription {transcription_id}")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"wav2vec2 transcription failed: {e}")
        
        # Send error callback if transcription_id provided
        if transcription_id:
            from app.services.callback_service import callback_service
            import asyncio
            asyncio.create_task(
                callback_service.notify_completion_async(
                    transcription_id, 
                    {}, 
                    f"Transcription failed: {str(e)}"
                )
            )
            logger.info(f"❌ Error callback queued for transcription {transcription_id}")
        
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    finally:
        # Cleanup original temp file
        if temp_file and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        # Cleanup converted audio file
        if converted_audio_path:
            AudioConverter.cleanup_temp_file(converted_audio_path)


@router.post("/models/unload")
async def unload_wav2vec2_model() -> JSONResponse:
    """Unload wav2vec2 model to free GPU memory"""
    
    try:
        from app.services.transcription import get_asr_service
        asr_service = get_asr_service()
        
        results = {
            "wav2vec2_unloaded": False,
            "memory_before": {},
            "memory_after": {}
        }
        
        # Get memory before cleanup
        if asr_service.wav2vec2_model:
            results["memory_before"] = asr_service.wav2vec2_model.get_memory_usage()
        
        # Unload wav2vec2
        if asr_service.wav2vec2_model and asr_service.wav2vec2_model.is_loaded():
            asr_service.wav2vec2_model.unload()
            results["wav2vec2_unloaded"] = True
            logger.info("✅ wav2vec2 model unloaded")
        
        # Get memory after cleanup
        if asr_service.wav2vec2_model:
            results["memory_after"] = asr_service.wav2vec2_model.get_memory_usage()
        
        return JSONResponse(content={
            "status": "success",
            "message": "wav2vec2 model unloaded successfully",
            "details": results
        })
        
    except Exception as e:
        logger.error(f"Failed to unload wav2vec2 model: {e}")
        raise HTTPException(status_code=500, detail=f"Unload failed: {str(e)}")


@router.post("/models/force-cleanup")
async def force_memory_cleanup() -> JSONResponse:
    """Force aggressive memory cleanup without unloading models"""
    
    try:
        from app.services.transcription import get_asr_service
        asr_service = get_asr_service()
        
        cleanup_results = []
        
        # Cleanup wav2vec2 if loaded
        if asr_service.wav2vec2_model and asr_service.wav2vec2_model.is_loaded():
            wav2vec_cleanup = asr_service.wav2vec2_model.force_memory_cleanup()
            wav2vec_cleanup["model"] = "wav2vec2"
            cleanup_results.append(wav2vec_cleanup)
        
        # Global cleanup if no models loaded
        if not cleanup_results:
            import gc
            import torch
            collected = gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            cleanup_results.append({
                "model": "global",
                "status": "success",
                "collected_objects": collected,
                "gpu_cache_cleared": torch.cuda.is_available()
            })
        
        return JSONResponse(content={
            "status": "success",
            "message": "Memory cleanup completed",
            "cleanup_results": cleanup_results
        })
        
    except Exception as e:
        logger.error(f"Force cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.get("/memory/status")
async def memory_status() -> JSONResponse:
    """Get current GPU memory status"""
    
    try:
        from app.services.transcription import get_asr_service
        asr_service = get_asr_service()
        
        status = {
            "models_loaded": {
                "wav2vec2": asr_service.wav2vec2_model and asr_service.wav2vec2_model.is_loaded()
            }
        }
        
        # Get memory usage from wav2vec2 model
        memory_usage = {"error": "No models loaded"}
        if asr_service.wav2vec2_model:
            memory_usage = asr_service.wav2vec2_model.get_memory_usage()
        
        status["gpu_memory"] = memory_usage
        
        # Add quantization info
        quantization_info = {
            "wav2vec2": "float32",  # Standard precision with garbage collection
            "memory_optimization": "wav2vec2_focused"
        }
        status["quantization"] = quantization_info
        
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"Memory status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Memory status failed: {str(e)}")


@router.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint"""
    
    try:
        health = {
            "status": "healthy",
            "service": "wav2vec2-service",
            "models": {
                "wav2vec2": "available"
            },
            "transformers_version": "4.36.0",
            "academic_mode": True,
            "memory_management": "wav2vec2_optimized",
            "quantization": {
                "wav2vec2": "float32"
            }
        }
        return JSONResponse(content=health)
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )