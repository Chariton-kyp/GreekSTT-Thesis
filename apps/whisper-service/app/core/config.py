"""
Configuration for GreekSTT Whisper Service
Settings for Whisper transcription service
"""
import os


class Config:
    """Configuration class for Whisper service"""
    
    # App info
    APP_TITLE = "GreekSTT Whisper Service"
    APP_DESCRIPTION = "Academic ASR service for Whisper model"
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