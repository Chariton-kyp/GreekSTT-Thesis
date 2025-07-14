"""
Chunked upload routes for large files.
Simple implementation without external dependencies.
"""

import os
import json
import hashlib
from pathlib import Path
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.utils.correlation_logger import get_correlation_logger
from app.common.responses import success_response, error_response, file_success_response, file_error_response
from app.audio.services import AudioService
from app.audio.mkv_converter import MkvConverter

logger = get_correlation_logger(__name__)

chunked_bp = Blueprint('chunked', __name__)


@chunked_bp.route('/start-chunked-upload', methods=['POST'])
@jwt_required()
def start_chunked_upload():
    """Initialize a chunked upload session."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        filename = secure_filename(data.get('filename', ''))
        file_size = data.get('fileSize', 0)
        chunk_size = data.get('chunkSize', 5 * 1024 * 1024)  # 5MB default
        
        if not filename:
            return file_error_response(
                message_key='NO_FILE_PROVIDED',
                error_code='MISSING_FILENAME'
            )
        
        # Check file size limits (8GB max)
        max_file_size = 8 * 1024 * 1024 * 1024  # 8GB
        if file_size > max_file_size:
            return file_error_response(
                message='File size exceeds maximum limit of 8GB',
                error_code='FILE_TOO_LARGE'
            )
            
        # Create upload session
        upload_id = hashlib.md5(f"{user_id}_{filename}_{file_size}".encode()).hexdigest()[:16]
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'chunks', upload_id)
        Path(upload_dir).mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        metadata = {
            'filename': filename,
            'file_size': file_size,
            'chunk_size': chunk_size,
            'chunks_received': [],
            'user_id': user_id
        }
        
        with open(os.path.join(upload_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f)
            
        logger.info(f"Started chunked upload: {upload_id} for file: {filename}")
        
        return success_response(
            message_key='UPLOAD_INITIALIZED',
            data={
                'uploadId': upload_id,
                'chunkSize': chunk_size
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to start chunked upload: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='UPLOAD_INIT_FAILED'
        )


@chunked_bp.route('/upload-chunk', methods=['POST'])
@jwt_required()
def upload_chunk():
    """Upload a single chunk."""
    try:
        upload_id = request.form.get('uploadId')
        chunk_index = int(request.form.get('chunkIndex', 0))
        
        if 'chunk' not in request.files:
            return file_error_response(
                message_key='NO_CHUNK_PROVIDED',
                error_code='MISSING_CHUNK'
            )
            
        chunk = request.files['chunk']
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'chunks', upload_id)
        
        # Load metadata
        metadata_path = os.path.join(upload_dir, 'metadata.json')
        if not os.path.exists(metadata_path):
            return file_error_response(
                message_key='UPLOAD_NOT_FOUND',
                error_code='INVALID_UPLOAD_ID'
            )
            
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            
        # Save chunk
        chunk_path = os.path.join(upload_dir, f"chunk_{chunk_index:06d}")
        chunk.save(chunk_path)
        
        # Update metadata
        if chunk_index not in metadata['chunks_received']:
            metadata['chunks_received'].append(chunk_index)
            metadata['chunks_received'].sort()
            
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
            
        logger.info(f"Received chunk {chunk_index} for upload {upload_id}")
        
        return success_response(
            message_key='CHUNK_UPLOADED',
            data={
                'chunkIndex': chunk_index,
                'chunksReceived': len(metadata['chunks_received'])
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to upload chunk: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='CHUNK_UPLOAD_FAILED'
        )


@chunked_bp.route('/complete-chunked-upload', methods=['POST'])
@jwt_required()
def complete_chunked_upload():
    """Complete chunked upload and start conversion."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        upload_id = data.get('uploadId')
        action = data.get('action', 'convert')  # 'convert' or 'upload'
        
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'chunks', upload_id)
        metadata_path = os.path.join(upload_dir, 'metadata.json')
        
        if not os.path.exists(metadata_path):
            return file_error_response(
                message_key='UPLOAD_NOT_FOUND',
                error_code='INVALID_UPLOAD_ID'
            )
            
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            
        # Combine chunks
        output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', metadata['filename'])
        Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as outfile:
            for i in sorted(metadata['chunks_received']):
                chunk_path = os.path.join(upload_dir, f"chunk_{i:06d}")
                with open(chunk_path, 'rb') as chunk_file:
                    outfile.write(chunk_file.read())
                    
        # Verify file size
        if os.path.getsize(output_path) != metadata['file_size']:
            os.unlink(output_path)
            return file_error_response(
                message='File size mismatch after combining chunks',
                error_code='FILE_SIZE_MISMATCH'
            )
            
        # Clean up chunks
        import shutil
        shutil.rmtree(upload_dir)
        
        logger.info(f"Combined chunks for file: {metadata['filename']}")
        
        # Handle based on action
        if action == 'convert' and metadata['filename'].lower().endswith('.mkv'):
            # Convert MKV to M4A
            converter = MkvConverter()
            
            # Create a fake FileStorage object for the converter
            class FakeFileStorage:
                def __init__(self, path, filename):
                    self.filename = filename
                    self._path = path
                    
                def save(self, dst):
                    import shutil
                    shutil.copy(self._path, dst)
                    
            fake_file = FakeFileStorage(output_path, metadata['filename'])
            converted_path, converted_filename = converter.convert_mkv_to_m4a(fake_file)
            
            # Save converted file
            audio_service = AudioService()
            audio_file = audio_service.save_audio_file(
                file_path=converted_path,
                original_filename=converted_filename,
                user_id=user_id
            )
            
            # Clean up
            os.unlink(output_path)
            os.unlink(converted_path)
            
            return file_success_response(
                message_key='FILE_CONVERTED_SUCCESSFULLY',
                data={'audio_file': audio_file.to_dict()}
            )
            
        else:
            # Just save the uploaded file
            audio_service = AudioService()
            audio_file = audio_service.save_audio_file(
                file_path=output_path,
                original_filename=metadata['filename'],
                user_id=user_id
            )
            
            os.unlink(output_path)
            
            return file_success_response(
                message_key='FILE_UPLOADED_SUCCESSFULLY',
                data={'audio_file': audio_file.to_dict()}
            )
            
    except Exception as e:
        logger.error(f"Failed to complete chunked upload: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='UPLOAD_COMPLETION_FAILED'
        )