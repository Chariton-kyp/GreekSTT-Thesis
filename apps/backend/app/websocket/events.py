"""WebSocket event handlers for transcription progress."""

import logging
from datetime import datetime
from flask_socketio import SocketIO, emit, disconnect
from flask import request, has_request_context
from flask_jwt_extended import decode_token, JWTManager
from app.websocket.manager import get_progress_manager
from app.utils.correlation_logger import get_correlation_logger

logger = get_correlation_logger(__name__)


def register_websocket_events(socketio: SocketIO, jwt_manager: JWTManager):
    """Register WebSocket event handlers."""
    
    @socketio.on('connect')
    def handle_connect(auth=None):
        """Handle client connection with optional JWT authentication."""
        try:
            # Check if we have a request context
            if has_request_context():
                sid = request.sid
            else:
                # Fallback if no request context
                sid = 'unknown'
            
            # Simple connection handler that avoids complex auth during handshake
            logger.info(f"WebSocket client connected | sid={sid}")
            
            # Send simple connection confirmation
            emit('connected', {
                'message': 'Successfully connected to progress updates',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return True
                
        except Exception as e:
            logger.error(f"WebSocket connection error | error={str(e)}")
            # Still return True to allow connection
            return True
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        try:
            # Check if we have a request context
            if has_request_context():
                sid = request.sid
            else:
                sid = 'unknown'
            
            progress_manager = get_progress_manager()
            if progress_manager and sid != 'unknown':
                progress_manager.cleanup_client(sid)
            
            logger.info(f"WebSocket client disconnected | sid={sid}")
            
        except Exception as e:
            logger.error(f"WebSocket disconnect error | error={str(e)}")
    
    @socketio.on('join_transcription')
    def handle_join_transcription(data):
        """Handle request to join transcription progress room."""
        try:
            transcription_id = data.get('transcription_id')
            if not transcription_id:
                emit('error', {'message': 'transcription_id is required'})
                return
            
            # Simple authentication - get user ID from token if provided
            user_id = 'anonymous'
            token = data.get('token')
            
            if token:
                try:
                    if token.startswith('Bearer '):
                        token = token[7:]
                    decoded_token = decode_token(token)
                    user_id = decoded_token['sub']
                except Exception as e:
                    logger.warning(f"Token decode error in join_transcription: {str(e)}")
                    # Continue with anonymous user
            
            # Join the transcription room
            progress_manager = get_progress_manager()
            if progress_manager:
                success = progress_manager.join_transcription_room(
                    user_id=str(user_id),
                    transcription_id=transcription_id,
                    sid=request.sid
                )
                
                if success:
                    emit('room_joined', {
                        'transcription_id': transcription_id,
                        'message': 'Successfully joined transcription room'
                    })
                else:
                    emit('error', {'message': 'Failed to join transcription room'})
            else:
                emit('error', {'message': 'Progress manager not available'})
                
        except Exception as e:
            logger.error(f"Join transcription error | sid={request.sid} | error={str(e)}")
            emit('error', {'message': 'Failed to join transcription updates'})
    
    @socketio.on('leave_transcription')
    def handle_leave_transcription(data):
        """Handle request to leave transcription progress room."""
        try:
            transcription_id = data.get('transcription_id')
            if not transcription_id:
                emit('error', {'message': 'transcription_id is required'})
                return
            
            progress_manager = get_progress_manager()
            if progress_manager:
                success = progress_manager.leave_transcription_room(
                    transcription_id=transcription_id,
                    sid=request.sid
                )
                
                if success:
                    emit('room_left', {
                        'transcription_id': transcription_id,
                        'message': 'Successfully left transcription updates'
                    })
                else:
                    emit('error', {'message': 'Failed to leave transcription room'})
            else:
                emit('error', {'message': 'Progress manager not available'})
                
        except Exception as e:
            logger.error(f"Leave transcription error | sid={request.sid} | error={str(e)}")
            emit('error', {'message': 'Failed to leave transcription updates'})
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping for connection testing."""
        emit('pong', {'timestamp': datetime.utcnow().isoformat()})
    
    logger.info("WebSocket event handlers registered successfully")