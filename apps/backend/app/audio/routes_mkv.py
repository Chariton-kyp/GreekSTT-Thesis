"""MKV conversion routes."""

import os
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.auth.verification_required import verification_required
from app.utils.logging_middleware import log_business_operation
from app.utils.correlation_logger import get_correlation_logger, log_business_flow
from app.common.responses import file_success_response, file_error_response
from app.audio.services import AudioService
from app.audio.mkv_converter import MkvConverter

logger = get_correlation_logger(__name__)

mkv_bp = Blueprint('mkv', __name__)


@mkv_bp.route('/convert-mkv', methods=['POST'])
@jwt_required()
@verification_required
@log_business_operation('mkv_conversion')
def convert_mkv_to_m4a():
    """Convert MKV file to M4A audio format."""
    try:
        user_id = get_jwt_identity()
        logger.info(f"MKV conversion request started for user {user_id}")
        
        # Check if FFmpeg is available
        if not MkvConverter.check_ffmpeg_available():
            logger.error("FFmpeg not available on system")
            return file_error_response(
                message='FFmpeg is not available for conversion',
                error_code='FFMPEG_NOT_AVAILABLE',
                status_code=503
            )
        
        # Log conversion flow start
        log_business_flow("mkv_conversion", "validation_start", {"user_id": user_id})
        
        # Check if file is in the request
        if 'video' not in request.files:
            logger.warning(f"MKV conversion attempt without file")
            return file_error_response(
                message_key='NO_FILE_PROVIDED',
                error_code='MISSING_FILE'
            )
        
        file = request.files['video']
        
        # Check if file is selected
        if file.filename == '':
            logger.warning(f"MKV conversion attempt with empty filename")
            return file_error_response(
                message_key='NO_FILE_SELECTED',
                error_code='EMPTY_FILENAME'
            )
            
        # Basic validation
        if not file.filename.lower().endswith('.mkv'):
            return file_error_response(
                message='File must be MKV format',
                error_code='INVALID_FILE_TYPE'
            )
        
        # Log file info
        logger.info(f"Processing MKV file: {file.filename}")
        
        # Convert the file
        converter = MkvConverter()
        output_path, output_filename = converter.convert_mkv_to_m4a(file)
        
        # Save converted file using AudioService
        audio_service = AudioService()
        audio_file = audio_service.save_audio_file(
            file_path=output_path,
            original_filename=output_filename,
            user_id=user_id
        )
        
        # Clean up converted file
        if os.path.exists(output_path):
            os.unlink(output_path)
        
        return file_success_response(
            message_key='FILE_CONVERTED_SUCCESSFULLY',
            data={'audio_file': audio_file.to_dict()},
            status_code=201
        )
        
    except Exception as e:
        logger.error(f"MKV conversion error: {str(e)}")
        return file_error_response(
            message='Conversion failed: ' + str(e),
            error_code='CONVERSION_ERROR',
            status_code=500
        )


@mkv_bp.route('/ffmpeg-status', methods=['GET'])
@jwt_required()
def check_ffmpeg_status():
    """Check if FFmpeg is available for video conversion."""
    try:
        import subprocess
        
        # Check if FFmpeg binary is available
        ffmpeg_available = MkvConverter.check_ffmpeg_available()
        
        # Get FFmpeg version if available
        ffmpeg_version = None
        if ffmpeg_available:
            try:
                result = subprocess.run(
                    ['ffmpeg', '-version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    ffmpeg_version = result.stdout.split('\n')[0]
            except:
                pass
        
        return file_success_response(
            message_key='OPERATION_SUCCESSFUL',
            data={
                'ffmpeg_available': ffmpeg_available,
                'ffmpeg_version': ffmpeg_version,
                'conversion_available': ffmpeg_available
            }
        )
        
    except Exception as e:
        logger.error(f"FFmpeg status check error: {str(e)}")
        return file_error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )