"""Cache management and monitoring routes."""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.cache.redis_service import get_transcription_cache
import logging

logger = logging.getLogger(__name__)

cache_bp = Blueprint('cache', __name__, url_prefix='/api/cache')


@cache_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_cache_stats():
    """Get Redis cache statistics."""
    try:
        cache = get_transcription_cache()
        stats = cache.get_cache_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve cache statistics',
            'error': str(e)
        }), 500


@cache_bp.route('/invalidate/user', methods=['POST'])
@jwt_required()
def invalidate_user_cache():
    """Invalidate all cached transcriptions for current user."""
    try:
        user_id = get_jwt_identity()
        cache = get_transcription_cache()
        
        deleted_count = cache.invalidate_user_cache(user_id)
        
        return jsonify({
            'success': True,
            'message': f'Invalidated {deleted_count} cached transcriptions',
            'deleted_count': deleted_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error invalidating user cache: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to invalidate user cache',
            'error': str(e)
        }), 500


@cache_bp.route('/invalidate/<int:transcription_id>', methods=['DELETE'])
@jwt_required()
def invalidate_transcription_cache(transcription_id):
    """Invalidate cache for specific transcription."""
    try:
        user_id = get_jwt_identity()
        cache = get_transcription_cache()
        
        success = cache.invalidate_transcription(transcription_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Cache invalidated for transcription {transcription_id}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'No cached data found for transcription {transcription_id}'
            }), 404
        
    except Exception as e:
        logger.error(f"Error invalidating transcription cache: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to invalidate transcription cache',
            'error': str(e)
        }), 500


@cache_bp.route('/extend-ttl/<int:transcription_id>', methods=['POST'])
@jwt_required()
def extend_cache_ttl(transcription_id):
    """Extend TTL for cached transcription."""
    try:
        user_id = get_jwt_identity()
        cache = get_transcription_cache()
        
        success = cache.extend_ttl(transcription_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'TTL extended for transcription {transcription_id}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'No cached data found for transcription {transcription_id}'
            }), 404
        
    except Exception as e:
        logger.error(f"Error extending cache TTL: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to extend cache TTL',
            'error': str(e)
        }), 500