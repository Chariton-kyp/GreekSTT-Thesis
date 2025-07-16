"""Audio file routes."""

import os
import requests
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.audio.services import AudioService
from app.common.utils import allowed_media_file
from app.auth.verification_required import verification_required
from app.utils.logging_middleware import log_business_operation
from app.utils.correlation_logger import get_correlation_logger, log_business_flow
from app.common.responses import (
    file_success_response, file_error_response, error_response, success_response
)

logger = get_correlation_logger(__name__)

audio_bp = Blueprint('audio', __name__)
audio_service = AudioService()


@audio_bp.route('/upload', methods=['POST'])
@jwt_required()
@verification_required
@log_business_operation('audio_upload')
def upload_audio():
    """Upload an audio file."""
    try:
        user_id = get_jwt_identity()
        
        # Log upload flow start
        log_business_flow("audio_upload", "validation_start", {"user_id": user_id})
        
        # Check if file is in the request
        if 'audio' not in request.files:
            logger.warning(f"Audio upload attempt without file")
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        
        # Check if file is selected
        if file.filename == '':
            logger.warning(f"Audio upload attempt with empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        # Log file validation
        log_business_flow("audio_upload", "file_validation", {
            "filename": file.filename,
            "size": file.content_length or 0
        })
        
        logger.info(f"Audio file upload started", {
            "filename": file.filename,
            "size": file.content_length or 0
        })
        
        # Check file extension (support both audio and video files)
        allowed_audio_extensions = current_app.config.get('ALLOWED_AUDIO_EXTENSIONS', set())
        allowed_video_extensions = current_app.config.get('ALLOWED_VIDEO_EXTENSIONS', set())
        all_allowed_extensions = allowed_audio_extensions.union(allowed_video_extensions)
        
        if not allowed_media_file(file.filename, allowed_audio_extensions, allowed_video_extensions):
            return file_error_response(
                message_key='INVALID_FILE_TYPE',
                error_code='INVALID_FILE_TYPE',
                status_code=400,
                details={'allowed_types': list(all_allowed_extensions)}
            )
        
        # Log processing start
        log_business_flow("audio_upload", "processing_start", {
            "filename": file.filename,
            "validated": True
        })
        
        # Process and save the file
        audio_file = audio_service.save_audio_file(file, user_id)
        
        # Log successful upload
        log_business_flow("audio_upload", "processing_success", {
            "audio_file_id": audio_file.id,
            "duration": audio_file.duration_seconds,
            "file_size": audio_file.file_size
        })
        
        return file_success_response(
            message_key='FILE_UPLOADED_SUCCESSFULLY',
            data={'audio_file': audio_file.to_dict()},
            status_code=201
        )
        
    except ValueError as e:
        return file_error_response(
            message=str(e),
            error_code='UPLOAD_ERROR',
            status_code=400
        )
    except Exception as e:
        current_app.logger.error(f"Audio upload error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@audio_bp.route('/', methods=['GET'])
@jwt_required()
@log_business_operation('get_user_audio_files')
def get_user_audio_files():
    """Get all audio files for the current user."""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        audio_files, pagination = audio_service.get_user_audio_files(
            user_id, page, per_page
        )
        
        return success_response(
            message_key='OPERATION_SUCCESSFUL',
            data={
                'audio_files': [af.to_dict() for af in audio_files],
                'pagination': pagination
            }
        )
        
    except Exception as e:
        current_app.logger.error(f"Get audio files error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@audio_bp.route('/<int:audio_id>', methods=['GET'])
@jwt_required()
@log_business_operation('get_audio_file')
def get_audio_file(audio_id):
    """Get details of a specific audio file."""
    try:
        user_id = get_jwt_identity()
        audio_file = audio_service.get_audio_file(audio_id, user_id)
        
        if not audio_file:
            return file_error_response(
                message_key='FILE_NOT_FOUND',
                error_code='AUDIO_FILE_NOT_FOUND',
                status_code=404
            )
        
        return success_response(
            message_key='OPERATION_SUCCESSFUL',
            data={'audio_file': audio_file.to_dict()}
        )
        
    except Exception as e:
        current_app.logger.error(f"Get audio file error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@audio_bp.route('/<int:audio_id>/download', methods=['GET'])
@jwt_required()
@log_business_operation('download_audio_file')
def download_audio_file(audio_id):
    """Download an audio file."""
    try:
        user_id = get_jwt_identity()
        audio_file = audio_service.get_audio_file(audio_id, user_id)
        
        if not audio_file:
            return file_error_response(
                message_key='FILE_NOT_FOUND',
                error_code='AUDIO_FILE_NOT_FOUND',
                status_code=404
            )
        
        # Check if file exists
        if not os.path.exists(audio_file.file_path):
            return file_error_response(
                message='File not found on server',
                error_code='FILE_NOT_FOUND_ON_SERVER',
                status_code=404
            )
        
        response = send_file(
            audio_file.file_path,
            as_attachment=False,  # Change to False for streaming/inline playback
            download_name=audio_file.original_filename,
            mimetype=audio_file.mime_type,
            conditional=True  # Enable HTTP range requests for better audio playback
        )
        
        # Add CORS headers for audio playback
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Accept-Ranges'] = 'bytes'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Download audio file error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@audio_bp.route('/<int:audio_id>/stream', methods=['GET'])
@log_business_operation('stream_audio_compressed')
def stream_audio_compressed(audio_id):
    """Stream compressed audio for large video files."""
    try:
        # Custom JWT handling for streaming URLs with query parameters
        token = None
        
        # Try to get token from Authorization header first
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        # Fallback to query parameter for streaming URLs
        if not token:
            token = request.args.get('Authorization')
            if token and token.startswith('Bearer '):
                token = token.split(' ')[1]
        
        if not token:
            return error_response(
                message='Authentication required',
                error_code='UNAUTHORIZED',
                status_code=401
            )
        
        # Manually verify JWT token
        try:
            from flask_jwt_extended import decode_token
            decoded_token = decode_token(token)
            user_id = decoded_token['sub']
        except Exception as e:
            logger.warning(f"Invalid token for streaming: {e}")
            return error_response(
                message='Invalid authentication token',
                error_code='INVALID_TOKEN',
                status_code=401
            )
        
        # Get audio file
        audio_file = audio_service.get_audio_file(audio_id, user_id)
        
        if not audio_file:
            return file_error_response(
                message_key='FILE_NOT_FOUND',
                error_code='AUDIO_FILE_NOT_FOUND',
                status_code=404
            )
        
        # Check if file exists
        if not os.path.exists(audio_file.file_path):
            return file_error_response(
                message='File not found on server',
                error_code='FILE_NOT_FOUND_ON_SERVER',
                status_code=404
            )
        
        # For large files (>100MB), serve with optimized streaming
        file_size = os.path.getsize(audio_file.file_path)
        logger.info(f"Streaming file: {file_size/1024/1024:.1f}MB")
        
        # Simple direct streaming - no compression, just headers
        response = send_file(
            audio_file.file_path,
            as_attachment=False,
            download_name=f"stream_{audio_file.original_filename}",
            mimetype=audio_file.mime_type or 'audio/mpeg',
            conditional=True  # Enable HTTP range requests
        )
        
        # Headers for fast streaming
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = 'public, max-age=3600'  # 1 hour cache
        response.headers['Content-Length'] = str(file_size)
        
        # Remove problematic headers that can cause SSL issues
        if 'Transfer-Encoding' in response.headers:
            del response.headers['Transfer-Encoding']
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Stream audio error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@audio_bp.route('/<int:audio_id>', methods=['DELETE'])
@jwt_required()
@log_business_operation('delete_audio_file')
def delete_audio_file(audio_id):
    """Delete an audio file."""
    try:
        user_id = get_jwt_identity()
        
        if audio_service.delete_audio_file(audio_id, user_id):
            return file_success_response(
                message_key='FILE_DELETED_SUCCESSFULLY'
            )
        else:
            return file_error_response(
                message_key='FILE_NOT_FOUND',
                error_code='AUDIO_FILE_NOT_FOUND',
                status_code=404
            )
            
    except Exception as e:
        current_app.logger.error(f"Delete audio file error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@audio_bp.route('/<int:audio_id>/metadata', methods=['GET'])
@jwt_required()
@log_business_operation('get_audio_metadata')
def get_audio_metadata(audio_id):
    """Get detailed metadata of an audio file."""
    try:
        user_id = get_jwt_identity()
        metadata = audio_service.get_audio_metadata(audio_id, user_id)
        
        if not metadata:
            return file_error_response(
                message_key='FILE_NOT_FOUND',
                error_code='AUDIO_FILE_NOT_FOUND',
                status_code=404
            )
        
        return success_response(
            message_key='OPERATION_SUCCESSFUL',
            data={'metadata': metadata}
        )
        
    except Exception as e:
        current_app.logger.error(f"Get audio metadata error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@audio_bp.route('/convert-mkv', methods=['POST'])
@jwt_required()
@verification_required
@log_business_operation('mkv_conversion')
def convert_mkv_to_m4a():
    """
    Convert MKV file to M4A format using AI service.
    Simple functionality that can be easily removed later.
    """
    try:
        user_id = get_jwt_identity()
        
        # Check if file is provided
        if 'file' not in request.files:
            return file_error_response(
                message_key='FILE_REQUIRED',
                error_code='NO_FILE_PROVIDED',
                status_code=400
            )
        
        file = request.files['file']
        if file.filename == '':
            return file_error_response(
                message_key='FILE_REQUIRED',
                error_code='NO_FILE_SELECTED',
                status_code=400
            )
        
        # Check file extension
        if not file.filename.lower().endswith('.mkv'):
            return file_error_response(
                message_key='INVALID_FILE_TYPE',
                error_code='NOT_MKV_FILE',
                status_code=400
            )
        
        logger.info(f"Converting MKV to M4A for user {user_id}: {file.filename}")
        
        # Forward to ASR service for audio conversion
        asr_service_url = current_app.config.get('ASR_SERVICE_URL', 'http://asr-service:8001')
        
        files = {'file': (file.filename, file.stream, file.mimetype)}
        response = requests.post(
            f"{asr_service_url}/conversion/mkv-to-m4a",
            files=files,
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code != 200:
            logger.error(f"AI service conversion failed: {response.text}")
            return error_response(
                message_key='CONVERSION_FAILED',
                error_code='AI_SERVICE_ERROR',
                status_code=response.status_code
            )
        
        # Return the converted file
        output_filename = file.filename.replace('.mkv', '.m4a')
        
        logger.info(f"MKV conversion successful for user {user_id}")
        
        return current_app.response_class(
            response.content,
            mimetype='audio/m4a',
            headers={
                'Content-Disposition': f'attachment; filename="{output_filename}"'
            }
        )
        
    except requests.RequestException as e:
        logger.error(f"AI service request error: {str(e)}")
        return error_response(
            message_key='EXTERNAL_SERVICE_ERROR',
            error_code='AI_SERVICE_UNAVAILABLE',
            status_code=503
        )
    
    except Exception as e:
        logger.error(f"MKV conversion error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='CONVERSION_ERROR',
            status_code=500
        )