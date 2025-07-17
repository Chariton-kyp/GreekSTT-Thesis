"""
Audio converter for video containers
Converts video files to WAV format optimized for ASR processing
"""
import logging
import tempfile
import os
from pathlib import Path
from typing import Optional, Tuple
import subprocess

logger = logging.getLogger(__name__)


class AudioConverter:
    """Smart audio converter for video containers"""
    
    VIDEO_FORMATS = {'.mkv', '.mp4', '.avi', '.mov', '.webm'}
    
    @classmethod
    def is_video_container(cls, file_path: str) -> bool:
        """Check if file is a video container"""
        return Path(file_path).suffix.lower() in cls.VIDEO_FORMATS
    
    @classmethod
    def convert_to_wav(cls, video_path: str, target_sample_rate: int = 16000) -> str:
        """Convert video file to WAV format for ASR processing"""
        try:
            temp_dir = tempfile.gettempdir()
            temp_wav = tempfile.NamedTemporaryFile(
                suffix='.wav', 
                dir=temp_dir, 
                delete=False
            )
            temp_wav_path = temp_wav.name
            temp_wav.close()
            
            file_ext = Path(video_path).suffix.lower()
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            
            logger.info(f"Converting {file_ext} to WAV: {file_size_mb:.1f}MB -> {temp_wav_path}")
            
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',
                '-acodec', 'pcm_s16le',
                '-ar', str(target_sample_rate),
                '-ac', '1',
                '-y',
                '-loglevel', 'error',
                temp_wav_path
            ]
            
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                if os.path.exists(temp_wav_path):
                    os.unlink(temp_wav_path)
                
                if "Unknown filter" in result.stderr or "codec" in result.stderr:
                    logger.warning("FFmpeg options not supported, trying basic conversion...")
                    return cls._convert_basic_fallback(video_path, target_sample_rate)
                
                error_msg = f"FFmpeg conversion failed: {result.stderr}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Verify output file
            if not os.path.exists(temp_wav_path) or os.path.getsize(temp_wav_path) == 0:
                if os.path.exists(temp_wav_path):
                    os.unlink(temp_wav_path)
                raise RuntimeError("FFmpeg produced empty output file")
            
            output_size_mb = os.path.getsize(temp_wav_path) / (1024 * 1024)
            
            # Get actual audio duration from converted file
            actual_duration, actual_sample_rate = get_audio_info(temp_wav_path)
            
            logger.info(f"Audio conversion successful: {output_size_mb:.1f}MB WAV file created")
            logger.info(f"Audio duration: {actual_duration:.2f}s ({actual_duration/60:.1f}min)")
            
            return temp_wav_path
            
        except subprocess.TimeoutExpired:
            if os.path.exists(temp_wav_path):
                os.unlink(temp_wav_path)
            error_msg = "FFmpeg conversion timed out (>5 minutes)"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        except Exception as e:
            if 'temp_wav_path' in locals() and os.path.exists(temp_wav_path):
                os.unlink(temp_wav_path)
            error_msg = f"Audio conversion failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    @classmethod
    def _convert_basic_fallback(cls, video_path: str, target_sample_rate: int = 16000) -> str:
        """
        Basic FFmpeg conversion without advanced filters (fallback)
        
        Args:
            video_path: Path to video file
            target_sample_rate: Target sample rate
            
        Returns:
            Path to temporary WAV file
        """
        try:
            temp_dir = tempfile.gettempdir()
            temp_wav = tempfile.NamedTemporaryFile(
                suffix='.wav', 
                dir=temp_dir, 
                delete=False
            )
            temp_wav_path = temp_wav.name
            temp_wav.close()
            
            logger.info("🔄 Using basic FFmpeg conversion (no filters applied)")
            
            # Basic FFmpeg conversion - no filters applied
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', video_path,           # Input video file
                '-vn',                      # No video (audio only)
                '-acodec', 'pcm_s16le',    # PCM 16-bit little-endian (WAV standard)
                '-ar', str(target_sample_rate),  # Sample rate
                '-ac', '1',                 # Mono channel
                '-y',                       # Overwrite output file
                '-loglevel', 'error',       # Only show errors
                temp_wav_path
            ]
            
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                if os.path.exists(temp_wav_path):
                    os.unlink(temp_wav_path)
                
                error_msg = f"Basic FFmpeg conversion failed: {result.stderr}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Verify output file
            if not os.path.exists(temp_wav_path) or os.path.getsize(temp_wav_path) == 0:
                if os.path.exists(temp_wav_path):
                    os.unlink(temp_wav_path)
                raise RuntimeError("Basic FFmpeg produced empty output file")
            
            output_size_mb = os.path.getsize(temp_wav_path) / (1024 * 1024)
            logger.info(f"✅ Basic audio conversion successful: {output_size_mb:.1f}MB WAV file created")
            
            return temp_wav_path
            
        except Exception as e:
            if 'temp_wav_path' in locals() and os.path.exists(temp_wav_path):
                os.unlink(temp_wav_path)
            error_msg = f"Basic audio conversion failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    @classmethod
    def convert_with_pydub_fallback(cls, video_path: str, target_sample_rate: int = 16000) -> str:
        """
        Fallback conversion using pydub (slower but more reliable)
        
        Args:
            video_path: Path to video file
            target_sample_rate: Target sample rate
            
        Returns:
            Path to temporary WAV file
        """
        try:
            from pydub import AudioSegment
            
            logger.info("🔄 Using pydub fallback for audio conversion")
            
            # Load audio using pydub (supports many formats via FFmpeg)
            audio = AudioSegment.from_file(video_path)
            
            # Convert to mono and resample
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_frame_rate(target_sample_rate)  # Resample
            
            # Create temporary file
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_wav_path = temp_wav.name
            temp_wav.close()
            
            # Export as WAV
            audio.export(temp_wav_path, format="wav")
            
            output_size_mb = os.path.getsize(temp_wav_path) / (1024 * 1024)
            logger.info(f"✅ Pydub conversion successful: {output_size_mb:.1f}MB WAV file")
            
            return temp_wav_path
            
        except Exception as e:
            if 'temp_wav_path' in locals() and os.path.exists(temp_wav_path):
                os.unlink(temp_wav_path)
            error_msg = f"Pydub conversion failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    @classmethod
    def smart_convert(cls, file_path: str, target_sample_rate: int = 16000) -> Optional[str]:
        """
        Smart conversion with automatic fallback
        
        Args:
            file_path: Path to input file
            target_sample_rate: Target sample rate
            
        Returns:
            Path to temporary WAV file if conversion needed, None if not needed
        """
        if not cls.is_video_container(file_path):
            logger.debug(f"File {Path(file_path).suffix} is not a video container - no conversion needed")
            return None
        
        try:
            # Try FFmpeg first (primary method)
            return cls.convert_to_wav(file_path, target_sample_rate)
        except RuntimeError as e:
            logger.warning(f"FFmpeg conversion failed: {e}")
            logger.info("🔄 Attempting pydub fallback...")
            
            try:
                # Fallback to pydub
                return cls.convert_with_pydub_fallback(file_path, target_sample_rate)
            except RuntimeError as fallback_error:
                logger.error(f"Both FFmpeg and pydub conversion failed")
                raise RuntimeError(f"All conversion methods failed: FFmpeg={e}, pydub={fallback_error}")
    
    @classmethod
    def cleanup_temp_file(cls, temp_path: Optional[str]) -> None:
        """Safely cleanup temporary file"""
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.debug(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary file {temp_path}: {e}")


def get_audio_info(file_path: str) -> Tuple[float, int]:
    """
    Get audio duration and sample rate using FFprobe
    
    Args:
        file_path: Path to audio/video file
        
    Returns:
        Tuple of (duration_seconds, sample_rate)
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            '-select_streams', 'a:0',  # First audio stream
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            logger.warning(f"FFprobe failed for {file_path}: {result.stderr}")
            # Try fallback method for duration
            return get_duration_fallback(file_path), 16000
        
        import json
        data = json.loads(result.stdout)
        
        if 'streams' not in data or not data['streams']:
            logger.warning(f"No audio streams found in {file_path}")
            # Try fallback method for duration
            return get_duration_fallback(file_path), 16000
        
        stream = data['streams'][0]
        duration = float(stream.get('duration', 0))
        sample_rate = int(stream.get('sample_rate', 16000))
        
        # If duration is 0 or missing, try to get it from format info
        if duration <= 0:
            duration = get_duration_from_format(file_path)
        
        return duration, sample_rate
        
    except Exception as e:
        logger.warning(f"Failed to get audio info for {file_path}: {e}")
        # Try fallback method for duration
        fallback_duration = get_duration_fallback(file_path)
        return fallback_duration, 16000


def get_video_duration(file_path: str) -> float:
    """
    Get video duration specifically, with multiple fallback methods
    
    Args:
        file_path: Path to video file
        
    Returns:
        Duration in seconds
    """
    # First try to get duration from video stream
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            
            # Try to get duration from format first (most reliable for videos)
            if 'format' in data and 'duration' in data['format']:
                duration = float(data['format']['duration'])
                if duration > 0:
                    logger.info(f"📊 Video duration from format: {duration:.2f}s ({duration/60:.1f}min)")
                    return duration
            
            # Try to get duration from video stream
            if 'streams' in data:
                for stream in data['streams']:
                    if stream.get('codec_type') == 'video' and 'duration' in stream:
                        duration = float(stream['duration'])
                        if duration > 0:
                            logger.info(f"📊 Video duration from video stream: {duration:.2f}s ({duration/60:.1f}min)")
                            return duration
                    
                # Try audio stream if video stream doesn't have duration
                for stream in data['streams']:
                    if stream.get('codec_type') == 'audio' and 'duration' in stream:
                        duration = float(stream['duration'])
                        if duration > 0:
                            logger.info(f"📊 Video duration from audio stream: {duration:.2f}s ({duration/60:.1f}min)")
                            return duration
    
    except Exception as e:
        logger.warning(f"FFprobe format analysis failed for {file_path}: {e}")
    
    # Fallback method
    return get_duration_fallback(file_path)


def get_duration_from_format(file_path: str) -> float:
    """
    Get duration from format info (fallback method)
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            
            if 'format' in data and 'duration' in data['format']:
                duration = float(data['format']['duration'])
                if duration > 0:
                    return duration
                    
    except Exception as e:
        logger.debug(f"Format duration extraction failed: {e}")
    
    return 0.0


def get_duration_fallback(file_path: str) -> float:
    """
    Fallback method to get duration using different FFprobe approach
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            duration = float(result.stdout.strip())
            logger.debug(f"Fallback duration method: {duration:.2f}s")
            return duration
            
    except Exception as e:
        logger.debug(f"Fallback duration method failed: {e}")
    
    return 0.0


def preprocess_audio_for_whisper(audio_path: str, target_sample_rate: int = 16000) -> str:
    """
    Preprocess audio to prevent hallucinations at the beginning
    
    - Removes silence from start and end
    - Applies gentle noise reduction
    - Normalizes audio levels
    - Returns path to preprocessed audio file
    
    Args:
        audio_path: Path to input audio file
        target_sample_rate: Target sample rate (default 16000 for Whisper)
        
    Returns:
        Path to preprocessed temporary audio file
    """
    try:
        import librosa
        import numpy as np
        import tempfile
        import soundfile as sf
        
        logger.info(f"🔧 Preprocessing audio to prevent start-of-audio hallucinations: {Path(audio_path).name}")
        
        # Load audio with target sample rate
        y, sr = librosa.load(audio_path, sr=target_sample_rate)
        original_duration = len(y) / sr
        
        # 1. Trim silence from beginning and end (aggressive for start)
        # Use lower top_db threshold for more aggressive silence removal at start
        y_trimmed, (start_idx, end_idx) = librosa.effects.trim(
            y, 
            top_db=20,  # More aggressive than default 60dB
            frame_length=2048,
            hop_length=512
        )
        
        trimmed_start = start_idx / sr
        new_duration = len(y_trimmed) / sr
        
        logger.info(f"🔇 Trimmed {trimmed_start:.2f}s of silence from start (duration: {original_duration:.2f}s → {new_duration:.2f}s)")
        
        # 2. Apply gentle noise reduction using spectral gating
        # Only if the audio is very quiet (potential noise issues)
        rms_energy = np.sqrt(np.mean(y_trimmed**2))
        if rms_energy < 0.01:  # Very quiet audio
            logger.info("🔊 Applying gentle noise reduction for very quiet audio")
            # Simple noise gate: reduce very low amplitude sections
            noise_threshold = np.max(np.abs(y_trimmed)) * 0.1  # 10% of max amplitude
            y_trimmed = np.where(np.abs(y_trimmed) < noise_threshold, 
                               y_trimmed * 0.1, y_trimmed)
        
        # 3. Gentle normalization (not aggressive to avoid artifacts)
        max_amplitude = np.max(np.abs(y_trimmed))
        if max_amplitude > 0:
            # Normalize to 85% of max to avoid clipping but ensure good signal level
            target_max = 0.85
            y_trimmed = y_trimmed * (target_max / max_amplitude)
        
        # 4. Add small fade-in to avoid sudden starts (prevents clicks)
        fade_samples = min(int(0.01 * sr), len(y_trimmed) // 10)  # 10ms or 10% of audio
        if fade_samples > 0:
            fade_in = np.linspace(0, 1, fade_samples)
            y_trimmed[:fade_samples] *= fade_in
        
        # 5. Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        # Save as 16-bit WAV for optimal Whisper compatibility
        sf.write(temp_path, y_trimmed, sr, subtype='PCM_16')
        
        # Verify output
        output_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
        logger.info(f"✅ Audio preprocessing complete: {output_size_mb:.1f}MB clean WAV created")
        logger.info(f"📊 Preprocessing stats: Removed {trimmed_start:.2f}s start silence, duration now {new_duration:.2f}s")
        
        return temp_path
        
    except Exception as e:
        logger.warning(f"Audio preprocessing failed, using original file: {e}")
        return audio_path


def detect_speech_start(audio_path: str, sample_rate: int = 16000) -> float:
    """
    Detect when actual speech starts in the audio file
    
    Args:
        audio_path: Path to audio file
        sample_rate: Sample rate for analysis
        
    Returns:
        Time in seconds when speech is detected to start
    """
    try:
        import librosa
        import numpy as np
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=sample_rate)
        
        # Use multiple detection methods
        
        # Method 1: Energy-based detection
        frame_length = 2048
        hop_length = 512
        
        # Calculate short-time energy
        energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        
        # Calculate spectral centroid (higher for speech)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
        
        # Calculate zero crossing rate (speech has moderate ZCR)
        zcr = librosa.feature.zero_crossing_rate(y, frame_length=frame_length, hop_length=hop_length)[0]
        
        # Combined speech detection
        # Speech typically has: moderate energy, higher spectral centroid, moderate ZCR
        energy_threshold = np.percentile(energy, 75)  # 75th percentile
        centroid_threshold = np.percentile(spectral_centroid, 60)  # 60th percentile
        zcr_threshold = np.percentile(zcr, 40)  # 40th percentile (speech is not too high ZCR)
        
        # Find frames that meet speech criteria
        speech_frames = (
            (energy > energy_threshold) & 
            (spectral_centroid > centroid_threshold) & 
            (zcr > zcr_threshold)
        )
        
        # Find first speech frame
        if np.any(speech_frames):
            first_speech_frame = np.argmax(speech_frames)
            speech_start_time = librosa.frames_to_time(first_speech_frame, sr=sr, hop_length=hop_length)
            logger.debug(f"Speech detected starting at {speech_start_time:.2f}s")
            return speech_start_time
        else:
            logger.debug("No clear speech detected, using silence trimming")
            return 0.0
            
    except Exception as e:
        logger.debug(f"Speech detection failed: {e}")
        return 0.0