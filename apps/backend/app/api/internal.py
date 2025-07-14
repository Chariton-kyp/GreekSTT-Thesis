"""
Internal API endpoints for service-to-service communication
"""
import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.transcription.models import Transcription
from app.websocket.manager import get_progress_manager
from app.utils.correlation_logger import get_correlation_logger

logger = get_correlation_logger(__name__)

internal_bp = Blueprint('internal', __name__, url_prefix='/api/internal')


@internal_bp.route('/transcription-callback', methods=['POST'])
def transcription_callback():
    """
    Receive transcription completion callbacks from ASR service
    """
    try:
        data = request.get_json()
        
        if not data:
            logger.error("No data received in callback")
            return jsonify({"error": "No data provided"}), 400
        
        transcription_id = data.get('transcription_id')
        status = data.get('status')
        result = data.get('result')
        error_message = data.get('error_message')
        source = data.get('source', 'unknown')
        
        if not transcription_id:
            logger.error("No transcription_id in callback data")
            return jsonify({"error": "transcription_id required"}), 400
        
        logger.info(f"📞 Received callback for transcription {transcription_id} | status: {status} | source: {source}")
        
        # Find the transcription in database
        transcription = Transcription.query.get(transcription_id)
        if not transcription:
            logger.error(f"Transcription {transcription_id} not found in database")
            return jsonify({"error": "Transcription not found"}), 404
        
        # Update transcription based on callback
        if status == 'completed' and result:
            # Success case
            transcription.status = 'completed'
            transcription.completed_at = datetime.now(timezone.utc)
            transcription.text = result.get('text', '')
            transcription.language = result.get('language', 'el')
            transcription.confidence_score = result.get('metadata', {}).get('avg_confidence', 0.0)
            transcription.duration_seconds = result.get('duration', 0.0)
            
            # Count words
            if transcription.text:
                transcription.word_count = len(transcription.text.split())
            
            # Store processing metadata
            transcription.processing_metadata = result.get('metadata', {})
            # Keep the existing model_used value (set by the upload process)
            
            # Update duration for both audio and video files from transcription result
            metadata = result.get('metadata', {})
            result_duration = result.get('duration', 0)
            
            if transcription.audio_file and result_duration > 0:
                old_duration = transcription.audio_file.duration_seconds or 0
                
                # For video files, prefer original video duration
                if metadata.get('was_video_file'):
                    video_duration = (metadata.get('original_video_duration') or 
                                    metadata.get('actual_audio_duration') or 
                                    result_duration)
                    
                    transcription.audio_file.duration_seconds = video_duration
                    transcription.duration_seconds = video_duration
                    
                    duration_source = metadata.get('video_duration_source', 'processed_audio')
                    logger.info(f"📊 Updated video duration from {duration_source}: {old_duration:.2f}s → {video_duration:.2f}s ({video_duration/60:.1f}min)")
                else:
                    # For audio files, use the result duration
                    transcription.audio_file.duration_seconds = result_duration
                    transcription.duration_seconds = result_duration
                    
                    if abs(old_duration - result_duration) > 1.0:  # Only log if significant difference
                        logger.info(f"📊 Updated audio duration: {old_duration:.2f}s → {result_duration:.2f}s ({result_duration/60:.1f}min)")
            
            # Clear any previous error
            transcription.error_message = None
            
            logger.info(f"✅ Transcription {transcription_id} marked as completed | {len(transcription.text)} chars")
            
        elif status == 'failed':
            # Failure case
            transcription.status = 'failed'
            transcription.completed_at = datetime.now(timezone.utc)
            transcription.error_message = error_message or "Processing failed (callback)"
            
            logger.warning(f"❌ Transcription {transcription_id} marked as failed | error: {error_message}")
        
        else:
            logger.error(f"Invalid callback status: {status}")
            return jsonify({"error": "Invalid status"}), 400
        
        # Save to database
        db.session.commit()
        
        # Send WebSocket notification to frontend
        try:
            progress_manager = get_progress_manager()
            if progress_manager:
                if status == 'completed':
                    progress_manager.broadcast_completion(
                        transcription_id=str(transcription_id),
                        result_data={
                            'text': transcription.text,
                            'confidence': transcription.confidence_score or 0.0,
                            'processing_time': result.get('metadata', {}).get('processing_time_ms', 0)
                        }
                    )
                else:
                    progress_manager.broadcast_error(
                        transcription_id=str(transcription_id),
                        error_message=transcription.error_message
                    )
            else:
                logger.warning("Progress manager not available for WebSocket notification")
        except Exception as ws_error:
            logger.warning(f"WebSocket notification failed: {ws_error}")
        
        return jsonify({
            "status": "success",
            "message": f"Transcription {transcription_id} updated to {status}",
            "transcription_id": transcription_id
        }), 200
        
    except Exception as e:
        logger.error(f"Callback processing failed: {e}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500


@internal_bp.route('/health', methods=['GET'])
def internal_health():
    """Health check for internal API"""
    return jsonify({
        "status": "healthy",
        "service": "backend-internal-api",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200