"""Flask extensions initialization."""

import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_caching import Cache
from flask_mail import Mail
from flask_restx import Api
from flask_socketio import SocketIO

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
mail = Mail()

# Determine async mode based on environment
running_under_debugpy = os.environ.get('RUNNING_UNDER_DEBUGPY', 'false').lower() == 'true'
async_mode = 'threading' if running_under_debugpy else 'eventlet'

socketio = SocketIO(cors_allowed_origins="*", async_mode=async_mode)

# API Documentation (Flask-RESTX)
api = Api(
    title='GreekSTT Research Platform API',
    version='1.0.0',
    description='''
    GreekSTT Research Platform Audio Transcription Service API
    
    ## Authentication
    Most endpoints require JWT authentication. Include the JWT token in the Authorization header:
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    
    ## Features
    - User authentication and management
    - Audio file upload and processing
    - AI-powered transcription with Greek optimization
    - Academic research features for model comparison
    - Research analytics and usage tracking
    
    ''',
    doc='/docs/',  # Swagger UI endpoint
    prefix='/api',
    security='JWT',
    authorizations={
        'JWT': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Type in the *\'Value\'* input box below: **\'Bearer &lt;JWT&gt;\'**, where JWT is the token'
        }
    }
)

# Cache configuration - Using SimpleCache (in-memory) instead of Redis
cache = Cache(config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes
})


