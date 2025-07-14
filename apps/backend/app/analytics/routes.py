"""Research analytics routes for thesis project."""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.analytics.services import research_analytics_service
from app.utils.correlation_logger import get_correlation_logger

analytics_bp = Blueprint('analytics', __name__)
logger = get_correlation_logger(__name__)


@analytics_bp.route('/research/dashboard', methods=['GET'])
@jwt_required()
def get_research_dashboard():
    """Get research dashboard statistics."""
    try:
        stats = research_analytics_service.get_research_dashboard_stats()
        return jsonify({
            'success': True,
            'data': stats
        }), 200
    except Exception as e:
        logger.error(f"Error getting research dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load dashboard statistics'
        }), 500


@analytics_bp.route('/research/comparisons', methods=['GET'])
@jwt_required()
def get_model_comparisons():
    """Get model comparison data for charts."""
    try:
        data = research_analytics_service.get_model_comparison_data()
        return jsonify({
            'success': True,
            'data': data
        }), 200
    except Exception as e:
        logger.error(f"Error getting comparison data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load comparison data'
        }), 500


@analytics_bp.route('/research/recent', methods=['GET'])
@jwt_required()
def get_recent_stats():
    """Get recent transcription statistics."""
    try:
        stats = research_analytics_service.get_recent_transcriptions_stats(days=7)
        return jsonify({
            'success': True,
            'data': stats
        }), 200
    except Exception as e:
        logger.error(f"Error getting recent stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load recent statistics'
        }), 500


@analytics_bp.route('/research/model/<model_name>', methods=['GET'])
@jwt_required()
def get_model_stats(model_name):
    """Get statistics for a specific model."""
    try:
        if model_name not in ['whisper', 'wav2vec2']:
            return jsonify({
                'success': False,
                'error': 'Invalid model name'
            }), 400
        
        stats = {
            'usage_count': research_analytics_service.get_model_usage(model_name),
            'avg_accuracy': research_analytics_service.get_avg_accuracy(model_name),
            'avg_wer': research_analytics_service.get_avg_wer(model_name),
            'avg_cer': research_analytics_service.get_avg_cer(model_name),
            'avg_processing_time': research_analytics_service.get_avg_processing_time(model_name)
        }
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
    except Exception as e:
        logger.error(f"Error getting model stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load model statistics'
        }), 500


@analytics_bp.route('/users/me', methods=['GET'])
@jwt_required()
def get_user_analytics():
    """Get user-specific analytics (for frontend compatibility)."""
    try:
        from flask_jwt_extended import get_jwt_identity
        user_id = get_jwt_identity()
        
        # Return basic user analytics structure expected by frontend
        user_analytics = {
            'userTranscriptions': research_analytics_service.get_user_transcription_count(user_id),
            'userWhisperUsage': research_analytics_service.get_user_model_usage(user_id, 'whisper'),
            'userWav2vecUsage': research_analytics_service.get_user_model_usage(user_id, 'wav2vec2'),
            'userComparisonAnalyses': research_analytics_service.get_user_comparison_count(user_id),
            'userAvgAccuracy': research_analytics_service.get_user_avg_accuracy(user_id),
            'userAvgProcessingTime': research_analytics_service.get_user_avg_processing_time(user_id),
            'personalBestAccuracy': research_analytics_service.get_user_best_accuracy(user_id),
            'recentTranscriptions': research_analytics_service.get_user_recent_transcriptions(user_id, limit=5),
            'weeklyActivity': research_analytics_service.get_user_weekly_activity(user_id),
            'preferredModel': research_analytics_service.get_user_preferred_model(user_id),
            'mostUsedAudioFormat': research_analytics_service.get_user_most_used_format(user_id),
            'averageFileSize': research_analytics_service.get_user_avg_file_size(user_id),
            'researchProgress': {
                'samplesAnalyzed': research_analytics_service.get_user_transcription_count(user_id),
                'modelsCompared': research_analytics_service.get_user_comparison_count(user_id),
                'insightsGenerated': research_analytics_service.get_user_insights_count(user_id)
            }
        }
        
        return jsonify(user_analytics), 200
    except Exception as e:
        logger.error(f"Error getting user analytics: {str(e)}")
        return jsonify({
            'error': 'Failed to load user analytics'
        }), 500


@analytics_bp.route('/users/me/dashboard-stats', methods=['GET'])
@jwt_required()
def get_user_dashboard_stats():
    """Get user dashboard statistics (for frontend compatibility)."""
    try:
        from flask_jwt_extended import get_jwt_identity
        user_id = get_jwt_identity()
        
        # Return user analytics structure expected by dashboard
        user_analytics = {
            'userTranscriptions': research_analytics_service.get_user_transcription_count(user_id),
            'userWhisperUsage': research_analytics_service.get_user_model_usage(user_id, 'whisper'),
            'userWav2vecUsage': research_analytics_service.get_user_model_usage(user_id, 'wav2vec2'),
            'userComparisonAnalyses': research_analytics_service.get_user_comparison_count(user_id),
            'userAvgAccuracy': research_analytics_service.get_user_avg_accuracy(user_id),
            'userAvgProcessingTime': research_analytics_service.get_user_avg_processing_time(user_id),
            'personalBestAccuracy': research_analytics_service.get_user_best_accuracy(user_id),
            'recentTranscriptions': research_analytics_service.get_user_recent_transcriptions(user_id, limit=5),
            'weeklyActivity': research_analytics_service.get_user_weekly_activity(user_id),
            'preferredModel': research_analytics_service.get_user_preferred_model(user_id),
            'mostUsedAudioFormat': research_analytics_service.get_user_most_used_format(user_id),
            'averageFileSize': research_analytics_service.get_user_avg_file_size(user_id),
            'researchProgress': {
                'samplesAnalyzed': research_analytics_service.get_user_transcription_count(user_id),
                'modelsCompared': research_analytics_service.get_user_comparison_count(user_id),
                'insightsGenerated': research_analytics_service.get_user_insights_count(user_id)
            }
        }
        
        return jsonify({'stats': user_analytics}), 200
    except Exception as e:
        logger.error(f"Error getting user dashboard stats: {str(e)}")
        return jsonify({
            'error': 'Failed to load user dashboard statistics'
        }), 500


@analytics_bp.route('/system', methods=['GET'])
@jwt_required()
def get_system_analytics():
    """Get system-wide analytics (for frontend compatibility)."""
    try:
        from flask import request
        from flask_jwt_extended import get_jwt_identity
        
        user_id = get_jwt_identity()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get user-specific system analytics (thesis focus on individual user data)
        system_analytics = research_analytics_service.get_user_system_analytics(
            user_id, start_date, end_date
        )
        
        return jsonify(system_analytics), 200
    except Exception as e:
        logger.error(f"Error getting system analytics: {str(e)}")
        return jsonify({
            'error': 'Failed to load system analytics'
        }), 500