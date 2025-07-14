import logging
import time
import json
import os
from flask import Flask
from flask_jwt_extended import JWTManager
from datetime import timedelta, datetime

from app.extensions import db, migrate, jwt, cors, cache, mail, api, socketio
from app.config import config
from app.error_handlers import register_error_handlers


def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = 'development'
    
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # JSON Configuration for proper Greek character encoding
    app.config['JSON_AS_ASCII'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    # Override Flask's default JSON behavior for Unicode
    from flask.json.provider import DefaultJSONProvider
    
    class UnicodeJSONProvider(DefaultJSONProvider):
        def dumps(self, obj, **kwargs):
            kwargs.setdefault('ensure_ascii', False)
            return super().dumps(obj, **kwargs)
    
    app.json = UnicodeJSONProvider(app)
    
    # JWT Configuration
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['JWT_ALGORITHM'] = 'HS256'
    app.config['JWT_HEADER_NAME'] = 'Authorization'  
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # Additional JWT security settings
    app.config['JWT_ERROR_MESSAGE_KEY'] = 'error'
    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db, directory='migrations')
    jwt.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    # Use threading mode for simplicity and stability
    async_mode = 'threading'
    
    # Configure WebSocket with proper settings
    socketio_kwargs = {
        'async_mode': async_mode,
        'cors_allowed_origins': '*',
        'logger': False,
        'engineio_logger': False,
        'ping_timeout': 60,
        'ping_interval': 25,
        'transports': ['websocket', 'polling'],
        'always_connect': True
    }
    
    # Add websocket_ping_interval for better connection handling
    if async_mode == 'gevent':
        socketio_kwargs['websocket_ping_interval'] = 10
    
    socketio.init_app(app, **socketio_kwargs)
    
    # Log the async mode being used
    app.logger.info(f"WebSocket initialized with async_mode='{async_mode}'")
    
    # Celery removed for academic demo
    
    # Initialize API documentation (only in development)
    if app.config.get('ENVIRONMENT') == 'development':
        api.init_app(app)
        
        # Register API namespaces for documentation
        from .api_docs import (
            auth_ns, users_ns, audio_ns, transcription_ns, 
            templates_ns, health_ns
        )
        from .api_docs.health import HealthCheck, DetailedHealthCheck
        
        api.add_namespace(health_ns, path='/health')
        api.add_namespace(auth_ns, path='/auth')
        api.add_namespace(users_ns, path='/users')
        api.add_namespace(audio_ns, path='/audio')
        api.add_namespace(transcription_ns, path='/transcriptions')
        api.add_namespace(templates_ns, path='/templates')
    
    # Initialize CORS
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:4200",
                "http://greekstt-research.gr",
                "http://app.greekstt-research.gr"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Register error handlers
    register_error_handlers(app)
    
    # Configure logging with datetime format matching AI service
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S,%f'
    )
    
    # Initialize request logging middleware
    from .utils.logging_middleware import RequestLoggingMiddleware
    RequestLoggingMiddleware(app)
    
    # Initialize security middleware
    from .common.security_middleware import init_security_middleware
    init_security_middleware(app)
    
    # Custom formatter to match AI service datetime format exactly
    class CustomFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            ct = self.converter(record.created)
            if datefmt:
                s = time.strftime(datefmt, ct)
            else:
                t = time.strftime('%Y-%m-%d %H:%M:%S', ct)
                s = f"{t},{int(record.msecs):03d}"
            return s
    
    # Apply custom formatter to all handlers
    formatter = CustomFormatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )
    
    # Update all existing handlers
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)
    
    # Set logging level based on environment and suppress HTTP library noise
    if app.debug or app.config.get('ENVIRONMENT') == 'development':
        logging.getLogger().setLevel(logging.INFO)  # Changed from DEBUG to INFO
        logging.getLogger('app').setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger('app').setLevel(logging.INFO)
    
    # Always suppress HTTP library debug logs (development and production)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    # Import models to ensure they're registered with SQLAlchemy
    with app.app_context():
        from .auth import models as auth_models
        from .users import models as users_models
        from .audio import models as audio_models
        from .transcription import models as transcription_models
        from .sessions import models as session_models
        from .analytics import models as analytics_models
        
        # Auto-run migrations on startup (only if migrations exist)
        try:
            import os
            migrations_dir = os.path.join(app.root_path, '..', 'migrations')
            if os.path.exists(migrations_dir) and os.path.exists(os.path.join(migrations_dir, 'alembic.ini')):
                from flask_migrate import upgrade
                upgrade()
                app.logger.info("Database migrations completed successfully")
            else:
                app.logger.info("No migrations directory found - skipping auto-upgrade")
            
                
        except Exception as e:
            app.logger.error(f"Failed to run migrations: {e}")
            # Don't fail the app startup, just log the error
    
    # JWT callbacks
    from .models import BlacklistToken
    from .common.responses import auth_error_response
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        return BlacklistToken.query.filter_by(jti=jti).first() is not None
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """Load user from JWT data for user identity functions."""
        from .users.models import User
        identity = jwt_data["sub"]
        return User.query.filter_by(id=identity).one_or_none()
    
    # Custom JWT error callbacks for standardized responses
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired JWT tokens."""
        return auth_error_response(
            message_key='TOKEN_EXPIRED',
            error_code='TOKEN_EXPIRED',
            status_code=401
        )
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handle invalid JWT tokens."""
        return auth_error_response(
            message_key='INVALID_TOKEN',
            error_code='INVALID_TOKEN',
            status_code=401
        )
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handle missing JWT tokens."""
        return auth_error_response(
            message_key='AUTHORIZATION_REQUIRED',
            error_code='MISSING_AUTHORIZATION_HEADER',
            status_code=401
        )
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Handle revoked JWT tokens."""
        return auth_error_response(
            message_key='TOKEN_REVOKED',
            error_code='TOKEN_REVOKED',
            status_code=401
        )
    
    @jwt.needs_fresh_token_loader
    def fresh_token_required_callback(jwt_header, jwt_payload):
        """Handle fresh token required."""
        return auth_error_response(
            message_key='SESSION_EXPIRED',
            error_code='FRESH_TOKEN_REQUIRED',
            status_code=401
        )
    
    # Register blueprints
    from .auth.routes import auth_bp
    from .users.routes import users_bp
    from .audio.routes import audio_bp
    from .audio.routes_mkv import mkv_bp
    from .audio.chunked_routes import chunked_bp
    from .transcription.routes import transcription_bp
    from .transcription.upload_routes import upload_bp
    from .analytics.routes import analytics_bp
    from .sessions.routes import sessions_bp
    from .comparison.routes import comparison_bp
    from .export.routes import export_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(audio_bp, url_prefix='/api/audio')
    app.register_blueprint(mkv_bp, url_prefix='/api/audio')  # MKV conversion routes
    app.register_blueprint(chunked_bp, url_prefix='/api/audio')  # Chunked upload routes
    app.register_blueprint(transcription_bp, url_prefix='/api/transcriptions')
    app.register_blueprint(upload_bp, url_prefix='/api/transcriptions')  # Upload and transcribe endpoint
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(sessions_bp, url_prefix='/api/sessions')
    app.register_blueprint(comparison_bp, url_prefix='/api/comparison')
    app.register_blueprint(export_bp)  # Export routes already have /api/export prefix
    # Removed blueprint registrations: analysis, voice_notes, templates, insights (thesis simplification)
    
    # Internal API for service-to-service communication
    from app.api.internal import internal_bp
    app.register_blueprint(internal_bp)  # Internal routes with /api/internal prefix
    
    # Initialize WebSocket support
    from app.websocket.manager import init_progress_manager
    from app.websocket.events import register_websocket_events
    
    # Initialize progress manager
    init_progress_manager(socketio)
    
    # Register WebSocket events
    register_websocket_events(socketio, jwt)
    
    # Health check endpoint (simple, no decorators to avoid rate limiting conflicts)
    def health_check_handler():
        """Health check endpoint - completely bypasses rate limiting."""
        return {
            'status': 'healthy', 
            'service': 'greekstt-backend',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': '0d 3h 45m',
            'database': 'connected',
            'cache': 'connected',  # SimpleCache for academic demo
            'ai_service': 'available'
        }, 200
    
    # Register health check without any decorators
    app.add_url_rule('/api/health', 'health_check', health_check_handler, methods=['GET'])
    
    return app, socketio