"""Audio file services."""

import os
import logging
from typing import Optional, Tuple, List, Dict, Any
from werkzeug.datastructures import FileStorage
from flask import current_app
from app.extensions import db
from app.audio.models import AudioFile
from app.audio.repositories import AudioRepository
from app.common.utils import (
    generate_unique_filename, 
    get_audio_duration,
    get_file_mimetype,
    calculate_file_hash,
    sanitize_filename
)

logger = logging.getLogger(__name__)


class AudioService:
    """Service for audio file operations."""
    
    def __init__(self):
        self.repository = AudioRepository()
    
    def save_audio_file(self, file: FileStorage, user_id: int) -> AudioFile:
        """Save uploaded audio file and create database record."""
        logger.info(f"Saving audio file for user {user_id}: {file.filename}")
        
        # Sanitize original filename
        original_filename = sanitize_filename(file.filename)
        
        # Generate unique filename
        stored_filename = generate_unique_filename(original_filename)
        logger.debug(f"Generated unique filename: {stored_filename}")
        
        # Create user-specific directory
        user_dir = os.path.join(
            current_app.config['UPLOAD_FOLDER'], 
            'audio', 
            str(user_id)
        )
        os.makedirs(user_dir, exist_ok=True)
        
        # Full file path
        file_path = os.path.join(user_dir, stored_filename)
        
        # Save file
        logger.debug(f"Saving file to: {file_path}")
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_hash = calculate_file_hash(file_path)
        mime_type = get_file_mimetype(file_path)
        
        logger.info(f"File saved successfully: {file_size/1024/1024:.2f} MB, hash: {file_hash[:8]}, type: {mime_type}")
        
        # Handle duplicate uploads - reuse existing file ONLY if same user
        existing = AudioFile.query.filter_by(file_hash=file_hash, user_id=user_id).first()
        if existing:
            logger.info(f"User {user_id} re-uploading their own file: {original_filename} (hash: {file_hash[:8]}) - reusing existing AudioFile ID={existing.id}")
            # Remove the newly uploaded file since we're reusing the existing one
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Removed duplicate file: {file_path}")
            return existing
        
        # Check if another user has uploaded the same file
        other_user_file = AudioFile.query.filter_by(file_hash=file_hash).first()
        if other_user_file:
            logger.info(f"User {user_id} uploading file already uploaded by user {other_user_file.user_id}: {original_filename} (hash: {file_hash[:8]}) - creating separate record")
            # Different user - create a new AudioFile record but use the same physical file
            # Copy the existing file instead of using the new upload
            existing_file_path = other_user_file.file_path
            if os.path.exists(existing_file_path):
                import shutil
                shutil.copy2(existing_file_path, file_path)
                logger.debug(f"Copied existing file from {existing_file_path} to {file_path}")
            # File info already calculated above
        
        # Get audio metadata
        duration = get_audio_duration(file_path)
        if duration is not None:
            logger.info(f"Audio duration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
        else:
            logger.warning(f"Could not determine audio duration for file: {file_path}")
            duration = 0.0  # Default to 0 seconds if duration cannot be determined
        
        # Create database record
        audio_file = AudioFile(
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            mime_type=mime_type,
            duration_seconds=duration,
            user_id=user_id,
            status='uploaded'
        )
        
        db.session.add(audio_file)
        db.session.commit()
        
        logger.info(f"Audio file saved successfully: ID={audio_file.id}, user={user_id}, duration={duration:.1f}s")
        return audio_file
    
    def get_audio_file(self, audio_id: int, user_id: int) -> Optional[AudioFile]:
        """Get audio file if user has access."""
        logger.debug(f"User {user_id} requesting audio file {audio_id}")
        
        audio_file = self.repository.get_by_id(audio_id)
        
        # Check if user owns the file
        if audio_file and audio_file.user_id == user_id:
            logger.debug(f"Audio file {audio_id} access granted to user {user_id}")
            return audio_file
        
        if audio_file:
            logger.warning(f"User {user_id} denied access to audio file {audio_id} (owner: {audio_file.user_id})")
        else:
            logger.warning(f"Audio file {audio_id} not found for user {user_id}")
        
        return None
    
    def get_user_audio_files(self, user_id: int, page: int = 1, 
                            per_page: int = 20) -> Tuple[List[AudioFile], Dict[str, Any]]:
        """Get all audio files for a user with pagination."""
        logger.info(f"Getting audio files for user {user_id}: page={page}, per_page={per_page}")
        
        result = self.repository.get_user_files(user_id, page, per_page)
        
        logger.info(f"Retrieved {len(result['items'])} audio files for user {user_id} (total: {result['total']})")
        return result['items'], {
            'total': result['total'],
            'pages': result['pages'],
            'current_page': result['current_page'],
            'per_page': result['per_page'],
            'has_prev': result['has_prev'],
            'has_next': result['has_next']
        }
    
    def delete_audio_file(self, audio_id: int, user_id: int) -> bool:
        """Delete audio file if user has access."""
        logger.info(f"User {user_id} attempting to delete audio file {audio_id}")
        
        audio_file = self.get_audio_file(audio_id, user_id)
        
        if not audio_file:
            logger.warning(f"Audio file {audio_id} not found or access denied for user {user_id}")
            return False
        
        transcription_count = audio_file.transcriptions.count()
        
        # Check if file has transcriptions
        if transcription_count > 0:
            # Just soft delete - keep the file
            logger.info(f"Soft deleting audio file {audio_id} (has {transcription_count} transcriptions)")
            audio_file.soft_delete()
        else:
            # No transcriptions - can delete the actual file
            logger.info(f"Hard deleting audio file {audio_id} (no transcriptions)")
            try:
                if os.path.exists(audio_file.file_path):
                    os.remove(audio_file.file_path)
                    logger.debug(f"Physical file deleted: {audio_file.file_path}")
            except Exception as e:
                logger.error(f"Error deleting physical file {audio_file.file_path}: {str(e)}")
            
            # Hard delete from database
            db.session.delete(audio_file)
            db.session.commit()
        
        logger.info(f"Audio file {audio_id} deleted successfully by user {user_id}")
        return True
    
    def get_audio_metadata(self, audio_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed metadata for an audio file."""
        logger.info(f"Getting metadata for audio file {audio_id}, user {user_id}")
        
        audio_file = self.get_audio_file(audio_id, user_id)
        
        if not audio_file:
            logger.warning(f"Cannot get metadata - audio file {audio_id} not found or access denied for user {user_id}")
            return None
        
        metadata = audio_file.to_dict()
        
        # Add additional metadata if available
        try:
            from mutagen import File as MutagenFile
            audio = MutagenFile(audio_file.file_path)
            
            if audio:
                # Extract additional metadata
                metadata['audio_info'] = {
                    'length': audio.info.length if hasattr(audio.info, 'length') else None,
                    'bitrate': audio.info.bitrate if hasattr(audio.info, 'bitrate') else None,
                    'sample_rate': audio.info.sample_rate if hasattr(audio.info, 'sample_rate') else None,
                    'channels': audio.info.channels if hasattr(audio.info, 'channels') else None,
                }
                
                # Extract tags if available
                if audio.tags:
                    metadata['tags'] = {
                        'title': str(audio.tags.get('TIT2', '')) if audio.tags.get('TIT2') else None,
                        'artist': str(audio.tags.get('TPE1', '')) if audio.tags.get('TPE1') else None,
                        'album': str(audio.tags.get('TALB', '')) if audio.tags.get('TALB') else None,
                        'date': str(audio.tags.get('TDRC', '')) if audio.tags.get('TDRC') else None,
                    }
                    logger.debug(f"Extracted audio tags for file {audio_id}")
        except Exception as e:
            logger.error(f"Error extracting metadata for audio file {audio_id}: {str(e)}")
        
        logger.info(f"Metadata retrieved for audio file {audio_id}")
        return metadata
    
    def update_audio_status(self, audio_id: int, status: str) -> Optional[AudioFile]:
        """Update the status of an audio file."""
        logger.info(f"Updating audio file {audio_id} status to: {status}")
        
        audio_file = self.repository.update(audio_id, status=status)
        
        if audio_file:
            logger.info(f"Audio file {audio_id} status updated to {status}")
        else:
            logger.warning(f"Failed to update status for audio file {audio_id}")
            
        return audio_file
    
    def save_audio_from_path(self, file_path: str, original_filename: str, user_id: int, 
                           source_url: str = None, metadata: dict = None) -> AudioFile:
        """Save audio file from local path (for URL downloads)."""
        import shutil
        import os
        from mutagen import File as MutagenFile
        
        logger.info(f"Saving audio file from path: {file_path}")
        
        if not os.path.exists(file_path):
            raise ValueError("Audio file path does not exist")
        
        # Get file info
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError("Audio file is empty")
        
        # Generate unique filename
        file_extension = os.path.splitext(original_filename)[1] or '.mp3'
        unique_filename = generate_unique_filename(original_filename)
        
        # Create upload directory if it doesn't exist
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        # Copy file to upload directory
        destination_path = os.path.join(upload_dir, unique_filename)
        shutil.copy2(file_path, destination_path)
        
        # Calculate file hash (required for database)
        file_hash = calculate_file_hash(destination_path)
        
        # Handle duplicate downloads - reuse existing file if same hash exists
        existing = AudioFile.query.filter_by(file_hash=file_hash).first()
        if existing:
            if existing.user_id == user_id:
                logger.info(f"User {user_id} re-downloading their own URL content: {original_filename} (hash: {file_hash[:8]}) - reusing existing AudioFile ID={existing.id}")
                # Remove the newly downloaded file since we're reusing the existing one
                if os.path.exists(destination_path):
                    os.remove(destination_path)
                    logger.debug(f"Removed duplicate downloaded file: {destination_path}")
                return existing
            else:
                logger.info(f"Duplicate URL content downloaded by different user {user_id}: {original_filename} (hash: {file_hash[:8]}, original owner: {existing.user_id}) - creating new AudioFile for this user")
                # Different user - we still need to create a separate AudioFile record
        
        # Get mime type
        mime_type = get_file_mimetype(destination_path)
        
        # Extract audio metadata
        duration_seconds = 0
        try:
            audio_file = MutagenFile(destination_path)
            if audio_file and audio_file.info:
                duration_seconds = int(audio_file.info.length)
        except Exception as e:
            logger.warning(f"Could not extract duration from audio file: {str(e)}")
        
        # For different users with same content, create unique filename to avoid conflicts
        if existing and existing.user_id != user_id:
            # Add user suffix to make filename unique for different users
            base_name, ext = os.path.splitext(unique_filename)
            unique_filename = f"{base_name}_user{user_id}{ext}"
            new_destination_path = os.path.join(upload_dir, unique_filename)
            shutil.move(destination_path, new_destination_path)
            destination_path = new_destination_path
        
        # Create AudioFile record
        audio_file_record = AudioFile(
            user_id=user_id,
            original_filename=original_filename,
            stored_filename=unique_filename,
            file_path=destination_path,
            file_size=file_size,
            file_hash=file_hash,
            mime_type=mime_type,
            duration_seconds=duration_seconds,
            source_url=source_url,
            video_metadata=metadata or {},
            status='completed'
        )
        
        # Save to database with error handling
        try:
            db.session.add(audio_file_record)
            db.session.commit()
        except Exception as e:
            # If database insert fails, clean up the file
            if os.path.exists(destination_path):
                os.remove(destination_path)
            logger.error(f"Failed to save audio file to database: {e}")
            raise
        
        logger.info(f"Audio file saved from path | audio_file_id={audio_file_record.id} | size={file_size} | duration={duration_seconds}s")
        return audio_file_record