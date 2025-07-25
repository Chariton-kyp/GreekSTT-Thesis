"""
Whisper ASR API endpoints for GreekSTT Research Platform
"""
import logging
import tempfile
import os
from typing import Dict, Any
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse

from app.utils.audio_converter import AudioConverter

try:
    import torch
except ImportError:
    torch = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Whisper Transcription"])


async def transcribe_with_whisper(whisper_model, audio_path: str, filename: str) -> Dict[str, Any]:
    """Transcribe audio with Whisper model
    
    Args:
        whisper_model: Loaded Whisper model instance
        audio_path: Path to audio file
        filename: Original filename for result metadata
        
    Returns:
        Dict containing transcription results and metadata
    """
    import time
    import os
    
    # Get audio duration for RTF calculation
    try:
        import librosa
        audio_duration = librosa.get_duration(filename=audio_path)
        logger.info(f"Audio duration: {audio_duration:.2f} seconds")
    except Exception as e:
        logger.warning(f"Could not get audio duration: {e}")
        audio_duration = 0
    
    start_time = time.time()
    logger.info(f"Starting Whisper transcription for {filename} at {start_time}")
    
    segments, info = whisper_model.transcribe(
        audio_path,
        beam_size=10,
        best_of=1,
        temperature=0.0,
        language="el",
        condition_on_previous_text=False,
        initial_prompt="",
        compression_ratio_threshold=2.0,
        no_speech_threshold=0.2,
        vad_filter=True,
        vad_parameters={
            "threshold": 0.5,
            "min_speech_duration_ms": 500,
            "max_speech_duration_s": 30,
            "min_silence_duration_ms": 2000,
            "speech_pad_ms": 400,
        },
        word_timestamps=True,
        task="transcribe"
    )
    
    # Process segments and extract text (this can take time for long audio)
    full_text = ""
    word_level_timestamps = []
    
    for segment in segments:
        full_text += segment.text + " "
        
        if hasattr(segment, 'words') and segment.words:
            for word in segment.words:
                word_level_timestamps.append({
                    "word": word.word,
                    "start": word.start,
                    "end": word.end,
                    "probability": word.probability
                })
    
    full_text = full_text.strip()
    
    # Calculate TOTAL processing time (including post-processing)
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Calculate Real-Time Factor (RTF)
    rtf = processing_time / audio_duration if audio_duration > 0 else 0
    
    result = {
        "text": full_text,
        "language": "el",
        "language_probability": info.language_probability,
        "duration": info.duration,
        "processing_time": processing_time,
        "filename": filename,
        "metadata": {
            "model": "whisper-large-v3",
            "service": "whisper-service",
            "beam_size": 10,
            "best_of": 1,
            "temperature": 0.0,
            "condition_on_previous_text": False,
            "vad_filter": True,
            "anti_hallucination_enabled": True,
            "greek_optimized": True,
            "detection_language": info.language,
            "duration_seconds": info.duration,
            "processing_time_seconds": processing_time
        }
    }
    
    if word_level_timestamps:
        result["word_timestamps"] = word_level_timestamps
    
    # Log final results with CORRECT processing time
    logger.info(f"Whisper transcription completed:")
    logger.info(f"  - Audio duration: {audio_duration:.2f}s")
    logger.info(f"  - Processing time: {processing_time:.2f}s")
    logger.info(f"  - RTF (Real-Time Factor): {rtf:.3f}")
    logger.info(f"  - Speed: {audio_duration/processing_time:.1f}x faster than real-time" if processing_time > 0 else "  - Speed: N/A")
    logger.info(f"  - Text length: {len(full_text)} characters")
    
    return result


@router.post("/transcribe")
async def transcribe_whisper(
    file: UploadFile = File(...),
    request: Request = None
) -> JSONResponse:
    """Transcribe audio using Whisper large-v3"""
    
    transcription_id = request.headers.get("X-Transcription-ID") if request else None
    
    logger.info(f"Whisper endpoint received file: '{file.filename}' | content_type: {file.content_type}")
    if transcription_id:
        logger.info(f"Transcription ID: {transcription_id} (callback enabled)")
    
    if not file.filename:
        logger.error("No filename provided")
        raise HTTPException(status_code=400, detail="No file provided")
    
    allowed_formats = {
        '.wav', '.mp3', '.m4a', '.flac', '.ogg', '.opus', '.wma', '.aac',
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
    
    temp_file = None
    temp_path = None
    converted_audio_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        logger.info(f"Processing {file.filename} with Whisper")
        
        processing_path = temp_path
        if AudioConverter.is_video_container(temp_path):
            logger.info("Video file detected, converting to audio...")
            converted_audio_path = AudioConverter.smart_convert(temp_path)
            if converted_audio_path:
                processing_path = converted_audio_path
                logger.info(f"Using converted audio: {processing_path}")
        
        whisper_model = getattr(request.app.state, 'whisper_model', None)
        
        if whisper_model is None:
            logger.warning("Pre-loaded model not found, loading manually...")
            from faster_whisper import WhisperModel
            import torch
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            
            whisper_model = WhisperModel(
                "large-v3",
                device=device,
                compute_type=compute_type,
                download_root="/app/models/whisper",
                num_workers=1
            )
        
        result = await transcribe_with_whisper(whisper_model, processing_path, file.filename)
        result["filename"] = file.filename
        result["metadata"]["transformers_version"] = "4.36.0"
        result["metadata"]["service"] = "whisper-service"
        
        if AudioConverter.is_video_container(temp_path):
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
            
            logger.info(f"Video file metadata: original duration {original_duration:.2f}s ({original_duration/60:.1f}min)")
        
        # Send callback if transcription_id provided (fire-and-forget)
        if transcription_id:
            from app.services.callback_service import callback_service
            import asyncio
            asyncio.create_task(
                callback_service.notify_completion_async(transcription_id, result)
            )
            logger.info(f"Callback queued for transcription {transcription_id}")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        
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
            logger.info(f"Error callback queued for transcription {transcription_id}")
        
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    finally:
        # Clean up temporary files
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.info(f"Cleaned up temp file: {temp_path}")
            except Exception as cleanup_error:
                logger.error(f"Failed to clean up temp file {temp_path}: {cleanup_error}")
        
        if converted_audio_path:
            try:
                AudioConverter.cleanup_temp_file(converted_audio_path)
                logger.info(f"Cleaned up converted audio file: {converted_audio_path}")
            except Exception as cleanup_error:
                logger.error(f"Failed to clean up converted audio file {converted_audio_path}: {cleanup_error}")


@router.post("/models/unload")
async def unload_whisper_model() -> JSONResponse:
    """Unload Whisper model to free GPU memory"""
    
    try:
        from app.services.transcription import get_asr_service
        asr_service = get_asr_service()
        
        results = {
            "whisper_unloaded": False,
            "memory_before": {},
            "memory_after": {}
        }
        
        # Get memory before cleanup
        if asr_service.whisper_model:
            results["memory_before"] = asr_service.whisper_model.get_memory_usage()
        
        # Unload Whisper
        if asr_service.whisper_model and asr_service.whisper_model.is_loaded():
            asr_service.whisper_model.unload()
            results["whisper_unloaded"] = True
            logger.info("Whisper model unloaded")
        
        # Get memory after cleanup
        if asr_service.whisper_model:
            results["memory_after"] = asr_service.whisper_model.get_memory_usage()
        
        return JSONResponse(content={
            "status": "success",
            "message": "Whisper model unloaded successfully",
            "details": results
        })
        
    except Exception as e:
        logger.error(f"Failed to unload Whisper model: {e}")
        raise HTTPException(status_code=500, detail=f"Unload failed: {str(e)}")


@router.post("/models/force-cleanup")
async def force_memory_cleanup() -> JSONResponse:
    """Perform aggressive memory cleanup operations"""
    
    try:
        from app.services.transcription import get_asr_service
        asr_service = get_asr_service()
        
        cleanup_results = []
        
        # Cleanup Whisper if loaded
        if asr_service.whisper_model and asr_service.whisper_model.is_loaded():
            whisper_cleanup = asr_service.whisper_model.force_memory_cleanup()
            whisper_cleanup["model"] = "whisper"
            cleanup_results.append(whisper_cleanup)
        
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
                "whisper": asr_service.whisper_model and asr_service.whisper_model.is_loaded()
            }
        }
        
        # Get memory usage from whisper model
        memory_usage = {"error": "No models loaded"}
        if asr_service.whisper_model:
            memory_usage = asr_service.whisper_model.get_memory_usage()
        
        status["gpu_memory"] = memory_usage
        
        # Add quantization info
        quantization_info = {
            "whisper": "float16",  # Updated to float16 for better quality
            "memory_optimization": "whisper_focused"
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
            "service": "whisper-service",
            "models": {
                "whisper": "available"
            },
            "transformers_version": "4.36.0",
            "academic_mode": True,
            "memory_management": "whisper_optimized",
            "quantization": {
                "whisper": "float16"
            }
        }
        
        # Add GPU memory info if available
        if torch and torch.cuda.is_available():
            torch.cuda.synchronize()
            health["gpu_memory"] = {
                "allocated_gb": round(torch.cuda.memory_allocated() / 1024**3, 2),
                "reserved_gb": round(torch.cuda.memory_reserved() / 1024**3, 2),
                "total_gb": round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2)
            }
        
        return JSONResponse(content=health)
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@router.get("/memory")
async def get_memory_status() -> JSONResponse:
    """Get detailed GPU memory status"""
    
    try:
        memory_info = {
            "service": "whisper-service",
            "timestamp": None,
            "cpu_memory": "Not implemented",
            "gpu_memory": None
        }
        
        if torch and torch.cuda.is_available():
            torch.cuda.synchronize()
            
            allocated = torch.cuda.memory_allocated() / 1024**3
            reserved = torch.cuda.memory_reserved() / 1024**3
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            memory_info["gpu_memory"] = {
                "device": torch.cuda.get_device_name(0),
                "allocated_gb": round(allocated, 2),
                "reserved_gb": round(reserved, 2),
                "total_gb": round(total, 2),
                "free_gb": round(total - allocated, 2),
                "utilization_percent": round((allocated / total) * 100, 1),
                "memory_fraction": 0.6,  # 60% allocation for Whisper
                "notes": "ctranslate2 memory allocation may not be fully reflected in PyTorch metrics"
            }
        else:
            memory_info["gpu_memory"] = {
                "status": "GPU not available",
                "device": "CPU"
            }
        
        return JSONResponse(content=memory_info)
    
    except Exception as e:
        logger.error(f"Memory status check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )