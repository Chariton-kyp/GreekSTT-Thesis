"""Health check API documentation."""

from flask import current_app
from flask_restx import Resource
from datetime import datetime
import psutil
import os

from app.api_docs import health_ns
from app.api_docs.models import health_model, error_model
from app.extensions import db, cache


@health_ns.route('')
class HealthCheck(Resource):
    """Health check endpoint for monitoring service status."""
    
    @health_ns.doc('health_check')
    @health_ns.marshal_with(health_model)
    @health_ns.response(200, 'Service is healthy')
    @health_ns.response(503, 'Service is unhealthy', error_model)
    def get(self):
        """
        Get service health status.
        
        Returns comprehensive health information including:
        - Service status and uptime
        - Database connectivity
        - Cache functionality  
        - AI service availability
        - System resources
        """
        try:
            health_data = {
                'status': 'healthy',
                'service': 'greekstt-research-backend',
                'version': '1.0.0',
                'timestamp': datetime.utcnow(),
                'uptime': self._get_uptime(),
                'database': self._check_database(),
                'cache': self._check_cache(),
                'ai_service': self._check_ai_service()
            }
            
            # Determine overall health
            ai_status = health_data['ai_service']
            ai_healthy = True
            
            # Handle new separated services format
            if isinstance(ai_status, dict):
                ai_healthy = ai_status.get('overall') == 'available'
            else:
                ai_healthy = ai_status == 'available'
            
            if any(status in ['unhealthy', 'unavailable'] for status in [
                health_data['database'], 
                health_data['cache']
            ]) or not ai_healthy:
                health_data['status'] = 'degraded'
                return health_data, 503
            
            return health_data, 200
            
        except Exception as e:
            current_app.logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'service': 'greekstt-research-backend',
                'timestamp': datetime.utcnow(),
                'error': str(e)
            }, 503
    
    def _get_uptime(self):
        """Get service uptime."""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = datetime.now().timestamp() - boot_time
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            return f"{days}d {hours}h {minutes}m"
        except:
            return "unknown"
    
    def _check_database(self):
        """Check database connectivity."""
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            return 'connected'
        except Exception as e:
            current_app.logger.error(f"Database health check failed: {str(e)}")
            return 'unhealthy'
    
    def _check_cache(self):
        """Check cache functionality."""
        try:
            # Test cache read/write with SimpleCache
            cache.set('health_check', 'ok', timeout=5)
            result = cache.get('health_check')
            return 'connected' if result == 'ok' else 'degraded'
        except Exception as e:
            current_app.logger.error(f"Cache health check failed: {str(e)}")
            return 'unhealthy'
    
    def _check_ai_service(self):
        """Check separated AI services availability."""
        try:
            # Import here to avoid circular imports
            import httpx
            
            asr_url = current_app.config.get('ASR_SERVICE_URL', 'http://asr-service:8001')
            
            asr_status = 'unavailable'
            
            # Check ASR service
            try:
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(f"{asr_url}/api/v1/health")
                    if response.status_code == 200:
                        asr_status = 'available'
                    else:
                        asr_status = 'degraded'
            except Exception:
                asr_status = 'unavailable'
            
            # Return ASR service status
            return {
                'asr_service': asr_status,
                'overall': asr_status
            }
            
        except Exception as e:
            current_app.logger.warning(f"AI services health check failed: {str(e)}")
            return 'unavailable'


@health_ns.route('/detailed')
class DetailedHealthCheck(Resource):
    """Detailed health check with system metrics."""
    
    @health_ns.doc('detailed_health_check')
    @health_ns.response(200, 'Detailed health information')
    def get(self):
        """
        Get detailed health status with system metrics.
        
        Returns extended health information including:
        - CPU and memory usage
        - Disk usage
        - Network statistics
        - Service-specific metrics
        """
        try:
            # Get basic health data
            basic_health = HealthCheck().get()[0]
            
            # Add detailed system metrics
            detailed_data = {
                **basic_health,
                'system': {
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory': {
                        'total': psutil.virtual_memory().total,
                        'available': psutil.virtual_memory().available,
                        'percent': psutil.virtual_memory().percent
                    },
                    'disk': {
                        'total': psutil.disk_usage('/').total,
                        'used': psutil.disk_usage('/').used,
                        'free': psutil.disk_usage('/').free,
                        'percent': psutil.disk_usage('/').percent
                    }
                },
                'environment': {
                    'flask_env': current_app.config.get('FLASK_ENV'),
                    'debug': current_app.debug,
                    'testing': current_app.testing
                }
            }
            
            return detailed_data, 200
            
        except Exception as e:
            current_app.logger.error(f"Detailed health check failed: {str(e)}")
            return {'error': str(e)}, 500