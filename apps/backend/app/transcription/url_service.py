"""URL processing service for video metadata extraction and audio download."""

import os
import yt_dlp
import ffmpeg
import tempfile
import shutil
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from flask import current_app

logger = logging.getLogger(__name__)


class URLProcessingService:
    """Service for processing video URLs and extracting metadata."""
    
    def __init__(self):
        self.supported_platforms = {
            'youtube.com': 'youtube',
            'youtu.be': 'youtube',
            'vimeo.com': 'vimeo',
        }
    
    def extract_metadata(self, url: str) -> Dict[str, Any]:
        """Extract video metadata without downloading."""
        logger.info(f"Extracting metadata from URL: {url}")
        
        try:
            # Validate URL format
            if not self._is_valid_url(url):
                raise ValueError("Invalid URL format")
            
            # Configure yt-dlp options for metadata extraction
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'format': 'best[height<=720]/best',  # Prefer reasonable quality
                'writesubtitles': False,
                'writeautomaticsub': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                except Exception as e:
                    logger.error(f"yt-dlp extraction failed: {str(e)}")
                    raise ValueError(f"Failed to extract video information: {str(e)}")
                
                if not info:
                    raise ValueError("No video information could be extracted")
                
                # Extract and format metadata
                metadata = {
                    'title': self._clean_title(info.get('title', 'Unknown Video')),
                    'duration': info.get('duration', 0),
                    'duration_string': self._format_duration(info.get('duration', 0)),
                    'thumbnail': info.get('thumbnail'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'description': info.get('description', '')[:500],  # Limit description length
                    'platform': self._detect_platform(url),
                    'original_url': url,
                    'video_id': info.get('id'),
                    'formats_available': len(info.get('formats', [])),
                    'has_audio': self._has_audio_stream(info),
                    'quality_info': self._get_quality_info(info)
                }
                
                logger.info(f"Successfully extracted metadata for: {metadata['title']} ({metadata['duration_string']})")
                return metadata
                
        except Exception as e:
            logger.error(f"Metadata extraction failed for URL {url}: {str(e)}")
            raise ValueError(f"Failed to process URL: {str(e)}")
    
    def download_audio(self, url: str, user_id: int, title: str = None) -> str:
        """Download video and extract audio, return path to audio file."""
        logger.info(f"Starting audio download from URL: {url}")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"greekstt-research_download_{user_id}_")
        
        try:
            # Configure yt-dlp for audio extraction
            audio_path = os.path.join(temp_dir, "audio.%(ext)s")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': audio_path,
                'extractaudio': True,
                'audioformat': 'mp3',
                'audioquality': '192',
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=True)
                    downloaded_files = ydl.prepare_filename(info)
                    
                    # Find the actual downloaded file
                    audio_file = None
                    for file in os.listdir(temp_dir):
                        if file.startswith("audio."):
                            audio_file = os.path.join(temp_dir, file)
                            break
                    
                    if not audio_file or not os.path.exists(audio_file):
                        raise FileNotFoundError("Downloaded audio file not found")
                    
                    # Convert to MP3 if needed using ffmpeg
                    final_audio_path = os.path.join(temp_dir, "final_audio.mp3")
                    
                    if not audio_file.endswith('.mp3'):
                        logger.info("Converting audio to MP3 format")
                        (
                            ffmpeg
                            .input(audio_file)
                            .output(final_audio_path, acodec='mp3', audio_bitrate='192k')
                            .overwrite_output()
                            .run(quiet=True, capture_stdout=True)
                        )
                        audio_file = final_audio_path
                    
                    # Verify the file is valid
                    if os.path.getsize(audio_file) == 0:
                        raise ValueError("Downloaded audio file is empty")
                    
                    logger.info(f"Successfully downloaded and converted audio: {os.path.getsize(audio_file)} bytes")
                    return audio_file
                    
                except Exception as e:
                    logger.error(f"Audio download failed: {str(e)}")
                    raise ValueError(f"Failed to download audio: {str(e)}")
                    
        except Exception as e:
            # Cleanup on failure
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise e
    
    def cleanup_temp_file(self, file_path: str):
        """Clean up temporary files."""
        try:
            if os.path.exists(file_path):
                temp_dir = os.path.dirname(file_path)
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {str(e)}")
    
    def is_supported_url(self, url: str) -> bool:
        """Check if URL is from a supported platform."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return any(platform in domain for platform in self.supported_platforms.keys())
        except:
            return False
    
    def get_supported_platforms(self) -> Dict[str, str]:
        """Get list of supported platforms."""
        return {
            'youtube': 'YouTube',
            'vimeo': 'Vimeo',
        }
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            for platform_domain, platform_name in self.supported_platforms.items():
                if platform_domain in domain:
                    return platform_name
                    
            return 'unknown'
        except:
            return 'unknown'
    
    def _format_duration(self, seconds: Optional[int]) -> str:
        """Format duration in MM:SS or HH:MM:SS format."""
        if seconds is None or seconds <= 0:
            return "00:00"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _clean_title(self, title: str) -> str:
        """Clean and validate video title."""
        if not title:
            return "Unknown Video"
        
        # Remove excessive whitespace and limit length
        cleaned = " ".join(title.split())
        if len(cleaned) > 200:
            cleaned = cleaned[:197] + "..."
        
        return cleaned
    
    def _has_audio_stream(self, info: Dict) -> bool:
        """Check if video has audio streams."""
        formats = info.get('formats', [])
        for fmt in formats:
            if fmt.get('acodec') and fmt.get('acodec') != 'none':
                return True
        return False
    
    def _get_quality_info(self, info: Dict) -> Dict[str, Any]:
        """Extract quality information from video info."""
        formats = info.get('formats', [])
        
        # Find best audio and video quality
        best_audio_bitrate = 0
        best_video_height = 0
        
        for fmt in formats:
            # Audio quality
            if fmt.get('abr'):
                best_audio_bitrate = max(best_audio_bitrate, fmt.get('abr', 0))
            
            # Video quality
            if fmt.get('height'):
                best_video_height = max(best_video_height, fmt.get('height', 0))
        
        return {
            'best_audio_bitrate': best_audio_bitrate,
            'best_video_height': best_video_height,
            'total_formats': len(formats)
        }