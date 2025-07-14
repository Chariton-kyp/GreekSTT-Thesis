"""
Configuration for GreekSTT ASR Service
Settings for Whisper + wav2vec2 transcription
"""
import os


class Config:
    """Configuration class for ASR service"""
    
    # App info
    APP_TITLE = "GreekSTT ASR Service"
    APP_DESCRIPTION = "Academic ASR service for Whisper and wav2vec2 models"
    APP_VERSION = "1.0.0-academic"
    
    # API
    API_HOST = "0.0.0.0"
    API_PORT = 8001
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = True
    
    # Device detection
    DEVICE = "auto"  # auto, cuda, cpu
    
    # Models
    WHISPER_MODEL = "large-v3"
    WAV2VEC2_MODEL = "lighteternal/wav2vec2-large-xlsr-53-greek"
    
    # Language
    LANGUAGE = "el"
    
    # Processing
    MAX_FILE_SIZE_MB = 100  # 100MB max
    TEMP_DIR = "/tmp"
    
    # Logging
    LOG_LEVEL = "INFO"
    
    # Academic mode
    ACADEMIC_MODE = True


# Global config instance
config = Config()