"""Common utility functions."""

import os
import secrets
import string
import uuid
from datetime import datetime
from typing import Optional, Tuple
import magic
from mutagen import File as MutagenFile
from werkzeug.utils import secure_filename


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracking."""
    return str(uuid.uuid4())


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename preserving the extension."""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    random_string = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(8))
    _, ext = os.path.splitext(original_filename)
    return f"{timestamp}_{random_string}{ext}"


def allowed_audio_file(filename: str, allowed_extensions: set) -> bool:
    """Check if the file has an allowed audio extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def allowed_video_file(filename: str, allowed_extensions: set) -> bool:
    """Check if the file has an allowed video extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def allowed_media_file(filename: str, audio_extensions: set, video_extensions: set) -> bool:
    """Check if the file has an allowed audio or video extension."""
    return allowed_audio_file(filename, audio_extensions) or \
           allowed_video_file(filename, video_extensions)


def get_audio_duration(file_path: str) -> Optional[float]:
    """Get the duration of an audio file in seconds."""
    try:
        audio = MutagenFile(file_path)
        if audio is not None and audio.info:
            return audio.info.length
    except Exception:
        pass
    return None


def get_file_mimetype(file_path: str) -> str:
    """Get the MIME type of a file."""
    mime = magic.Magic(mime=True)
    return mime.from_file(file_path)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    import hashlib
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()


def paginate_query(query, page: int, per_page: int) -> Tuple[list, dict]:
    """Paginate a SQLAlchemy query."""
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    pagination_info = {
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
        'per_page': per_page,
        'has_prev': paginated.has_prev,
        'has_next': paginated.has_next
    }
    
    return paginated.items, pagination_info


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe storage, preserving Greek characters."""
    import re
    
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Custom sanitization that preserves Greek characters
    # Remove dangerous characters but keep Greek letters, Latin letters, digits, dots, dashes, underscores
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)  # Remove truly dangerous chars
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)  # Remove control characters
    filename = filename.strip('. ')  # Remove leading/trailing dots and spaces
    
    # If filename is empty after sanitization, generate a random one
    if not filename:
        filename = f"audio_{secrets.token_hex(8)}.mp3"
    
    return filename