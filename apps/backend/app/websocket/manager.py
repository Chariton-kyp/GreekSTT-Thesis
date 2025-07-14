"""WebSocket manager for transcription progress updates."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_jwt_extended import decode_token, JWTManager
from app.utils.correlation_logger import get_correlation_logger

logger = get_correlation_logger(__name__)


class TranscriptionProgressManager:
    """Manages WebSocket connections and progress broadcasting for transcriptions."""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.connected_clients: Dict[str, Dict[str, Any]] = {}
        
    def get_room_name(self, transcription_id: str) -> str:
        """Generate room name for a transcription."""
        return f"transcription_{transcription_id}"
        
    def join_transcription_room(self, user_id: int, transcription_id: str, sid: str) -> bool:
        """
        Join a user to a transcription room for progress updates.
        
        Args:
            user_id: ID of the authenticated user
            transcription_id: ID of the transcription to monitor
            sid: Socket session ID
            
        Returns:
            bool: True if successfully joined, False otherwise
        """
        try:
            room = self.get_room_name(transcription_id)
            join_room(room, sid=sid)
            
            # Track the connection
            if sid not in self.connected_clients:
                self.connected_clients[sid] = {}
                
            self.connected_clients[sid].update({
                'user_id': user_id,
                'transcription_id': transcription_id,
                'room': room,
                'joined_at': datetime.utcnow().isoformat()
            })
            
            logger.info(f"User {user_id} joined transcription room {transcription_id} | sid={sid}")
            
            # Send confirmation
            self.socketio.emit('room_joined', {
                'transcription_id': transcription_id,
                'message': 'Successfully joined transcription progress updates',
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to join transcription room | user_id={user_id} | transcription_id={transcription_id} | error={str(e)}")
            return False
    
    def leave_transcription_room(self, transcription_id: str, sid: str) -> bool:
        """
        Remove a user from a transcription room.
        
        Args:
            transcription_id: ID of the transcription room to leave
            sid: Socket session ID
            
        Returns:
            bool: True if successfully left, False otherwise
        """
        try:
            room = self.get_room_name(transcription_id)
            leave_room(room, sid=sid)
            
            # Update tracking
            if sid in self.connected_clients:
                client_info = self.connected_clients[sid]
                user_id = client_info.get('user_id', 'unknown')
                logger.info(f"User {user_id} left transcription room {transcription_id} | sid={sid}")
                
                # Remove transcription tracking but keep other client info
                if 'transcription_id' in client_info:
                    del client_info['transcription_id']
                if 'room' in client_info:
                    del client_info['room']
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to leave transcription room | transcription_id={transcription_id} | sid={sid} | error={str(e)}")
            return False
    
    def broadcast_progress(self, transcription_id: str, progress_data: Dict[str, Any]) -> bool:
        """
        Broadcast progress update to all clients in a transcription room.
        
        Args:
            transcription_id: ID of the transcription
            progress_data: Progress information to broadcast
            
        Returns:
            bool: True if broadcast successful, False otherwise
        """
        try:
            room = self.get_room_name(transcription_id)
            
            # Ensure required fields are present
            complete_progress_data = {
                'transcription_id': transcription_id,
                'timestamp': datetime.utcnow().isoformat(),
                **progress_data
            }
            
            # Broadcast to room
            self.socketio.emit('transcription_progress', complete_progress_data, room=room)
            
            logger.info(f"Progress broadcast sent | transcription_id={transcription_id} | stage={progress_data.get('stage', 'unknown')} | progress={progress_data.get('percentage', 0)}%")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to broadcast progress | transcription_id={transcription_id} | error={str(e)}")
            return False
    
    def broadcast_error(self, transcription_id: str, error_message: str, error_code: Optional[str] = None) -> bool:
        """
        Broadcast error message to all clients in a transcription room.
        
        Args:
            transcription_id: ID of the transcription
            error_message: Error message to broadcast
            error_code: Optional error code
            
        Returns:
            bool: True if broadcast successful, False otherwise
        """
        try:
            room = self.get_room_name(transcription_id)
            
            error_data = {
                'transcription_id': transcription_id,
                'stage': 'error',
                'percentage': 0,
                'message': error_message,
                'error_code': error_code,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.socketio.emit('transcription_error', error_data, room=room)
            
            logger.error(f"Error broadcast sent | transcription_id={transcription_id} | error={error_message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to broadcast error | transcription_id={transcription_id} | error={str(e)}")
            return False
    
    def broadcast_completion(self, transcription_id: str, result_data: Dict[str, Any]) -> bool:
        """
        Broadcast completion message to all clients in a transcription room.
        
        Args:
            transcription_id: ID of the transcription
            result_data: Completion data to broadcast
            
        Returns:
            bool: True if broadcast successful, False otherwise
        """
        try:
            room = self.get_room_name(transcription_id)
            
            completion_data = {
                'transcription_id': transcription_id,
                'stage': 'completed',
                'percentage': 100,
                'message': 'Η μεταγραφή ολοκληρώθηκε επιτυχώς!',
                'timestamp': datetime.utcnow().isoformat(),
                **result_data
            }
            
            self.socketio.emit('transcription_completed', completion_data, room=room)
            
            logger.info(f"Completion broadcast sent | transcription_id={transcription_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to broadcast completion | transcription_id={transcription_id} | error={str(e)}")
            return False
    
    def cleanup_client(self, sid: str) -> None:
        """
        Clean up client tracking when disconnected.
        
        Args:
            sid: Socket session ID
        """
        try:
            if sid in self.connected_clients:
                client_info = self.connected_clients[sid]
                user_id = client_info.get('user_id', 'unknown')
                transcription_id = client_info.get('transcription_id')
                
                logger.info(f"Cleaning up client | user_id={user_id} | transcription_id={transcription_id} | sid={sid}")
                
                # Leave any rooms they might be in
                if transcription_id:
                    self.leave_transcription_room(transcription_id, sid)
                
                # Remove from tracking
                del self.connected_clients[sid]
                
        except Exception as e:
            logger.error(f"Failed to cleanup client | sid={sid} | error={str(e)}")
    
    def get_connected_clients_count(self, transcription_id: Optional[str] = None) -> int:
        """
        Get count of connected clients, optionally filtered by transcription.
        
        Args:
            transcription_id: Optional transcription ID to filter by
            
        Returns:
            int: Number of connected clients
        """
        if transcription_id:
            return len([
                client for client in self.connected_clients.values()
                if client.get('transcription_id') == transcription_id
            ])
        return len(self.connected_clients)


# Global instance will be initialized in app factory
progress_manager: Optional[TranscriptionProgressManager] = None


def get_progress_manager() -> Optional[TranscriptionProgressManager]:
    """Get the global progress manager instance."""
    return progress_manager


def init_progress_manager(socketio: SocketIO) -> TranscriptionProgressManager:
    """Initialize the global progress manager."""
    global progress_manager
    progress_manager = TranscriptionProgressManager(socketio)
    return progress_manager