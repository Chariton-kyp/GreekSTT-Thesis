"""Application configuration."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    JSON_AS_ASCII = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret')
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/app/uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_FILE_SIZE', 8192)) * 1024 * 1024
    MAX_AUDIO_FILE_SIZE = int(os.environ.get('MAX_AUDIO_FILE_SIZE', 8192)) * 1024 * 1024
    MAX_VIDEO_FILE_SIZE = int(os.environ.get('MAX_VIDEO_FILE_SIZE', 8192)) * 1024 * 1024
    ALLOWED_AUDIO_EXTENSIONS = set(os.environ.get('ALLOWED_AUDIO_EXTENSIONS', 'wav,mp3,m4a,flac,ogg,wma,aac,opus,webm').split(','))
    ALLOWED_VIDEO_EXTENSIONS = set(os.environ.get('ALLOWED_VIDEO_EXTENSIONS', 'mkv,mp4,avi,mov,wmv').split(','))
    
    
    MAX_BATCH_UPLOAD_SIZE = int(os.environ.get('MAX_BATCH_UPLOAD_SIZE', 10))
    MAX_BATCH_SIZE_BYTES = int(os.environ.get('MAX_BATCH_SIZE_BYTES', 20480)) * 1024 * 1024
    
    MAX_DURATION_HOURS = int(os.environ.get('MAX_DURATION_HOURS', 10))
    MAX_PROCESSING_TIME_SECONDS = int(os.environ.get('MAX_PROCESSING_TIME_SECONDS', 14400))
    
    # MailHog Integration for Academic Demo
    MAIL_SERVER = os.environ.get('MAIL_SERVER', os.environ.get('SMTP_HOST', 'mailhog'))
    MAIL_PORT = int(os.environ.get('MAIL_PORT', os.environ.get('SMTP_PORT', 1025)))
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('FROM_EMAIL', 'noreply@greekstt-research.local'))
    MAIL_DEBUG = False
    
    BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5001')
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'support@greekstt-research.local')
    
    ASR_SERVICE_URL = os.environ.get('ASR_SERVICE_URL', 'http://asr-service:8001')
    AI_SERVICE_API_KEY = os.environ.get('AI_SERVICE_API_KEY')
    AI_SERVICE_TIMEOUT = 3600
    
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:4200')
    
    BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5001')
    
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'research@greekstt.local')
    
    PLATFORM_NAME = 'GreekSTT Comparison Platform'
    ACADEMIC_MODE = True
    EMAIL_MODE = 'academic_demo'
    MAILHOG_HOST = os.environ.get('MAILHOG_HOST', 'mailhog')
    MAILHOG_PORT = int(os.environ.get('MAILHOG_PORT', 1025))
    
    ACADEMIC_UNLIMITED_ACCESS = True  # Unlimited access for academic research
    ACADEMIC_RESEARCH_MODE = True  # Research mode enabled
    
    ENABLE_RESEARCH_TRACKING = False
    ENABLE_EMAIL_VERIFICATION = os.environ.get('ENABLE_EMAIL_VERIFICATION', 'true').lower() == 'true'
    ENABLE_MODEL_COMPARISON = True
    ENABLE_RESEARCH_ANALYTICS = True
    
    ACCOUNT_LOCKOUT_ENABLED = os.environ.get('ACCOUNT_LOCKOUT_ENABLED', 'true').lower() == 'true'
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
    LOCKOUT_DURATION_MINUTES = int(os.environ.get('LOCKOUT_DURATION_MINUTES', 15))
    
    ENABLE_SESSION_MANAGEMENT = os.environ.get('ENABLE_SESSION_MANAGEMENT', 'true').lower() == 'true'
    MAX_CONCURRENT_SESSIONS = int(os.environ.get('MAX_CONCURRENT_SESSIONS', 2))
    SESSION_DURATION_DAYS = int(os.environ.get('SESSION_DURATION_DAYS', 30))
    ENABLE_NEW_DEVICE_NOTIFICATIONS = os.environ.get('ENABLE_NEW_DEVICE_NOTIFICATIONS', 'true').lower() == 'true'
    SESSION_SECURITY_THRESHOLD = int(os.environ.get('SESSION_SECURITY_THRESHOLD', 3))
    ENABLE_SESSION_HIJACK_DETECTION = os.environ.get('ENABLE_SESSION_HIJACK_DETECTION', 'true').lower() == 'true'
    
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENVIRONMENT = 'development'
    FLASK_ENV = 'development'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/greekstt-research')
    
    ENABLE_RESEARCH_TRACKING = True
    ACADEMIC_UNLIMITED_ACCESS = True
    ACADEMIC_RESEARCH_MODE = True
    
    ACCOUNT_LOCKOUT_ENABLED = os.environ.get('ACCOUNT_LOCKOUT_ENABLED', 'true').lower() == 'true'
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
    LOCKOUT_DURATION_MINUTES = int(os.environ.get('LOCKOUT_DURATION_MINUTES', 15))
    
    ENABLE_SESSION_MANAGEMENT = os.environ.get('ENABLE_SESSION_MANAGEMENT', 'true').lower() == 'true'
    MAX_CONCURRENT_SESSIONS = int(os.environ.get('MAX_CONCURRENT_SESSIONS', 5))
    SESSION_DURATION_DAYS = int(os.environ.get('SESSION_DURATION_DAYS', 7))
    ENABLE_NEW_DEVICE_NOTIFICATIONS = os.environ.get('ENABLE_NEW_DEVICE_NOTIFICATIONS', 'false').lower() == 'true'
    SESSION_SECURITY_THRESHOLD = int(os.environ.get('SESSION_SECURITY_THRESHOLD', 5))
    
    RESTX_MASK_SWAGGER = False
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        import logging
        logging.basicConfig(level=logging.DEBUG)


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    ENVIRONMENT = 'testing'
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'postgresql://postgres:postgres@db:5432/test_greekstt-research')
    WTF_CSRF_ENABLED = False
    
    ENABLE_EMAIL_VERIFICATION = False
    ENABLE_RESEARCH_TRACKING = False
    ACADEMIC_UNLIMITED_ACCESS = True
    ACADEMIC_RESEARCH_MODE = True
    
    ACCOUNT_LOCKOUT_ENABLED = False
    MAX_LOGIN_ATTEMPTS = 999
    LOCKOUT_DURATION_MINUTES = 0
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    ENVIRONMENT = 'production'
    
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    ENABLE_RESEARCH_TRACKING = False
    ENABLE_EMAIL_VERIFICATION = os.environ.get('ENABLE_EMAIL_VERIFICATION', 'true').lower() == 'true'
    ACADEMIC_UNLIMITED_ACCESS = True
    ACADEMIC_RESEARCH_MODE = True
    
    RESTX_MASK_SWAGGER = True
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        import logging
        from logging.handlers import SysLogHandler
        syslog = SysLogHandler()
        syslog.setLevel(logging.WARNING)
        app.logger.addHandler(syslog)


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}