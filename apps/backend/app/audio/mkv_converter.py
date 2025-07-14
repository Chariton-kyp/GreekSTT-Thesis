"""
Simple MKV to M4A converter using FFmpeg.
"""

import os
import tempfile
import subprocess
from werkzeug.datastructures import FileStorage
from app.utils.correlation_logger import get_correlation_logger

logger = get_correlation_logger(__name__)


class MkvConverter:
    """Handle MKV to M4A conversion using FFmpeg."""
    
    @staticmethod
    def convert_mkv_to_m4a(file: FileStorage) -> tuple[str, str]:
        """
        Convert MKV file to M4A format.
        
        Args:
            file: The uploaded MKV file
            
        Returns:
            tuple: (output_path, original_filename)
        """
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.mkv', delete=False) as tmp_input:
            file.save(tmp_input.name)
            input_path = tmp_input.name
            
        output_path = input_path.replace('.mkv', '.m4a')
        output_filename = file.filename.replace('.mkv', '.m4a').replace('.MKV', '.m4a')
        
        try:
            logger.info(f"Converting MKV to M4A: {file.filename}")
            
            # FFmpeg command for conversion
            cmd = [
                'ffmpeg',
                '-i', input_path,           # Input file
                '-vn',                      # No video
                '-acodec', 'aac',          # AAC audio codec
                '-b:a', '192k',            # Audio bitrate
                '-movflags', '+faststart',  # Optimize for streaming
                '-y',                       # Overwrite output
                output_path
            ]
            
            # Run conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg conversion failed: {result.stderr}")
                
            # Verify output exists
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise Exception("Conversion produced empty file")
                
            logger.info(f"Successfully converted {file.filename} to M4A")
            
            # Clean up input file
            os.unlink(input_path)
            
            return output_path, output_filename
            
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg conversion timed out")
            # Clean up
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
            raise Exception("Conversion timed out after 10 minutes")
            
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            # Clean up
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
            raise
            
    @staticmethod
    def check_ffmpeg_available() -> bool:
        """Check if FFmpeg is available in the system."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False