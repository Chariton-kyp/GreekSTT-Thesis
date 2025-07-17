"""
Configuration for GreekSTT wav2vec2 Service
Settings for wav2vec2 transcription service
"""
import os


class Config:
    """Configuration class for wav2vec2 service"""
    
    # App info
    APP_TITLE = "GreekSTT wav2vec2 Service"
    APP_DESCRIPTION = "Academic ASR service for wav2vec2 Greek model"
    APP_VERSION = "1.0.0-academic"
    
    # API
    API_HOST = "0.0.0.0"
    API_PORT = 8002
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = True
    
    # Device detection
    DEVICE = "auto"  # auto, cuda, cpu
    
    # Models
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


config = Config()