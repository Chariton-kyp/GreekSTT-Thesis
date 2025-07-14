"""Transcription upload routes - unified upload and transcription creation."""

import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.audio.services import AudioService
from app.transcription.services import TranscriptionService
from app.common.utils import allowed_audio_file, allowed_video_file, allowed_media_file
from app.auth.verification_required import verification_required
from app.utils.logging_middleware import log_business_operation
import logging

logger = logging.getLogger(__name__)

upload_bp = Blueprint('transcription_upload', __name__)
audio_service = AudioService()
transcription_service = TranscriptionService()


@upload_bp.route('', methods=['POST'])
@upload_bp.route('/', methods=['POST'])
@jwt_required()
@verification_required
@log_business_operation('transcription_upload_and_create')
def upload_and_transcribe():
    """Upload audio file and create transcription in one operation."""
    try:
        user_id = get_jwt_identity()
        
        # Check if file is in the request
        if 'file' not in request.files:
            logger.warning(f"Transcription upload attempt without file | user_id={user_id}")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            logger.warning(f"Transcription upload attempt with empty filename | user_id={user_id}")
            return jsonify({'error': 'No file selected'}), 400
        
        # Get form data (academic version - no template support)
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        language = request.form.get('language', 'el')
        ai_model = request.form.get('ai_model', 'whisper')
        
        # Debug logging for ai_model
        logger.info(f"Upload request | user_id={user_id} | ai_model_raw='{request.form.get('ai_model')}' | ai_model_processed='{ai_model}'")
        
        # Validate required fields
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        if len(title) < 3:
            return jsonify({'error': 'Title must be at least 3 characters long'}), 400
        
        if len(title) > 200:
            return jsonify({'error': 'Title must be less than 200 characters'}), 400
        
        if description and len(description) > 1000:
            return jsonify({'error': 'Description must be less than 1000 characters'}), 400
        
        if language not in ['el', 'en']:
            return jsonify({'error': 'Language must be "el" or "en"'}), 400
        
        # Validate AI model parameter - accepts 'whisper', 'wav2vec2', or 'both'
        # Also accepts legacy model names for backward compatibility
        valid_models = ['whisper', 'wav2vec2', 'both', 'whisper-large-v3', 'whisper-medium', 'wav2vec2-greek', 'compare']
        if ai_model not in valid_models:
            return jsonify({'error': 'Invalid AI model. Must be "whisper", "wav2vec2", or "both"'}), 400
        
        # Normalize legacy model names to simplified versions
        if ai_model in ['whisper-large-v3', 'whisper-medium']:
            ai_model = 'whisper'
        elif ai_model == 'wav2vec2-greek':
            ai_model = 'wav2vec2'
        elif ai_model == 'compare':
            ai_model = 'both'
        
        logger.info(f"Transcription upload started | user_id={user_id} | filename={file.filename} | title={title} | language={language} | ai_model={ai_model}")
        
        # Check file extension (support both audio and video files)
        allowed_audio_extensions = current_app.config.get('ALLOWED_AUDIO_EXTENSIONS', set())
        allowed_video_extensions = current_app.config.get('ALLOWED_VIDEO_EXTENSIONS', set())
        all_allowed_extensions = allowed_audio_extensions.union(allowed_video_extensions)
        
        if not allowed_media_file(file.filename, allowed_audio_extensions, allowed_video_extensions):
            return jsonify({
                'error': f'Invalid file type. Allowed types: {", ".join(sorted(all_allowed_extensions))}'
            }), 400
        
        # Check file size (8GB limit for large files)
        max_file_size = 8 * 1024 * 1024 * 1024  # 8GB
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > max_file_size:
            return jsonify({'error': 'File size must be less than 8GB'}), 400
        
        # Template functionality removed for academic version
        
        # Academic Mode: Unlimited transcription access for research purposes
        current_app.logger.info("Academic mode enabled - unlimited transcription access granted for research")
        
        # Academic logging: Track file processing details for research analytics
        estimated_duration = max(60, file_size / (1024 * 1024) * 60)  # At least 1 minute
        current_app.logger.info(f"Academic upload processing: {file_size / (1024*1024):.1f}MB file, estimated {estimated_duration}s duration")
        
        # Step 1: Save audio file
        audio_file = audio_service.save_audio_file(file, user_id)
        
        logger.info(f"Audio file saved | user_id={user_id} | audio_file_id={audio_file.id} | duration={audio_file.duration_seconds}s")
        
        # Step 2: Create transcription job with all metadata
        transcription = transcription_service.create_transcription_with_metadata(
            audio_file_id=audio_file.id,
            user_id=user_id,
            title=title,
            description=description,
            language=language,
            ai_model=ai_model
        )
        
        logger.info(f"Transcription job created | user_id={user_id} | transcription_id={transcription.id} | status={transcription.status}")
        
        # Return response with both audio file and transcription data
        return jsonify({
            'message': 'File uploaded and transcription started successfully',
            'audio_file': audio_file.to_dict(),
            'transcription': transcription.to_dict(),
            'academic_mode': True  # Always in academic research mode
        }), 201
        
    except ValueError as e:
        logger.error(f"Validation error in upload_and_transcribe | user_id={get_jwt_identity()} | error={str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Upload and transcribe error | user_id={get_jwt_identity()} | error={str(e)}")
        return jsonify({'error': 'Failed to upload file and create transcription'}), 500


@upload_bp.route('/formats', methods=['GET'])
@jwt_required()
@log_business_operation('get_supported_formats')
def get_supported_formats():
    """Get list of supported audio/video formats."""
    try:
        formats = {
            'audio': [
                {
                    'extension': '.mp3',
                    'mime_type': 'audio/mpeg',
                    'description': 'MP3 Audio'
                },
                {
                    'extension': '.wav',
                    'mime_type': 'audio/wav',
                    'description': 'WAV Audio'
                },
                {
                    'extension': '.m4a',
                    'mime_type': 'audio/mp4',
                    'description': 'M4A Audio'
                },
                {
                    'extension': '.flac',
                    'mime_type': 'audio/flac',
                    'description': 'FLAC Audio'
                },
                {
                    'extension': '.ogg',
                    'mime_type': 'audio/ogg',
                    'description': 'OGG Audio'
                },
                {
                    'extension': '.webm',
                    'mime_type': 'audio/webm',
                    'description': 'WebM Audio'
                }
            ],
            'video': [
                {
                    'extension': '.mkv',
                    'mime_type': 'video/x-matroska',
                    'description': 'MKV Video'
                },
                {
                    'extension': '.mp4',
                    'mime_type': 'video/mp4',
                    'description': 'MP4 Video'
                },
                {
                    'extension': '.mov',
                    'mime_type': 'video/quicktime',
                    'description': 'QuickTime Video'
                },
                {
                    'extension': '.avi',
                    'mime_type': 'video/x-msvideo',
                    'description': 'AVI Video'
                },
                {
                    'extension': '.wmv',
                    'mime_type': 'video/x-ms-wmv',
                    'description': 'WMV Video'
                }
            ],
            'max_file_size': '8GB',
            'max_duration': '10 hours'
        }
        
        return jsonify(formats), 200
        
    except Exception as e:
        logger.error(f"Get supported formats error: {str(e)}")
        return jsonify({'error': 'Failed to get supported formats'}), 500


@upload_bp.route('/batch', methods=['POST'])
@jwt_required()
@verification_required
@log_business_operation('batch_transcription_upload_and_create')
def batch_upload_and_transcribe():
    """Upload multiple audio files and create transcriptions in one operation."""
    try:
        user_id = get_jwt_identity()
        
        # Get files from request
        files = request.files.getlist('files')
        if not files or len(files) == 0:
            logger.warning(f"Batch transcription upload attempt without files | user_id={user_id}")
            return jsonify({'error': 'No files provided'}), 400
        
        # Limit number of files in batch
        max_batch_size = current_app.config.get('MAX_BATCH_UPLOAD_SIZE', 10)
        if len(files) > max_batch_size:
            return jsonify({'error': f'Maximum {max_batch_size} files allowed per batch'}), 400
        
        # Get common form data
        base_title = request.form.get('base_title', '').strip()
        description = request.form.get('description', '').strip()
        language = request.form.get('language', 'el')
        ai_model = request.form.get('ai_model', 'whisper')
        
        # Validate common fields
        if not base_title:
            return jsonify({'error': 'Base title is required'}), 400
        
        if len(base_title) < 3:
            return jsonify({'error': 'Base title must be at least 3 characters long'}), 400
        
        if len(base_title) > 150:  # Shorter for batch to allow numbering
            return jsonify({'error': 'Base title must be less than 150 characters'}), 400
        
        if description and len(description) > 1000:
            return jsonify({'error': 'Description must be less than 1000 characters'}), 400
        
        if language not in ['el', 'en']:
            return jsonify({'error': 'Language must be "el" or "en"'}), 400
        
        # Validate AI model parameter - accepts 'whisper', 'wav2vec2', or 'both'
        # Also accepts legacy model names for backward compatibility
        valid_models = ['whisper', 'wav2vec2', 'both', 'whisper-large-v3', 'whisper-medium', 'wav2vec2-greek', 'compare']
        if ai_model not in valid_models:
            return jsonify({'error': 'Invalid AI model. Must be "whisper", "wav2vec2", or "both"'}), 400
        
        # Normalize legacy model names to simplified versions
        if ai_model in ['whisper-large-v3', 'whisper-medium']:
            ai_model = 'whisper'
        elif ai_model == 'wav2vec2-greek':
            ai_model = 'wav2vec2'
        elif ai_model == 'compare':
            ai_model = 'both'
        
        # Template functionality removed for academic version
        
        logger.info(f"Batch transcription upload started | user_id={user_id} | file_count={len(files)} | base_title={base_title} | language={language} | ai_model={ai_model}")
        
        results = []
        total_file_size = 0
        max_file_size = 8 * 1024 * 1024 * 1024  # 8GB per file
        max_batch_size_bytes = 20 * 1024 * 1024 * 1024  # 20GB total batch size
        
        # First pass: validate all files
        for i, file in enumerate(files):
            if file.filename == '':
                return jsonify({'error': f'File {i+1} has no filename'}), 400
            
            # Check file extension (support both audio and video files)
            allowed_audio_extensions = current_app.config.get('ALLOWED_AUDIO_EXTENSIONS', set())
            allowed_video_extensions = current_app.config.get('ALLOWED_VIDEO_EXTENSIONS', set())
            all_allowed_extensions = allowed_audio_extensions.union(allowed_video_extensions)
            
            if not allowed_media_file(file.filename, allowed_audio_extensions, allowed_video_extensions):
                return jsonify({
                    'error': f'File {i+1} ({file.filename}): Invalid file type. Allowed types: {", ".join(sorted(all_allowed_extensions))}'
                }), 400
            
            # Check individual file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > max_file_size:
                return jsonify({'error': f'File {i+1} ({file.filename}): File size must be less than 8GB'}), 400
            
            total_file_size += file_size
        
        # Check total batch size
        if total_file_size > max_batch_size_bytes:
            return jsonify({'error': f'Total batch size must be less than 20GB. Current: {total_file_size / (1024*1024*1024):.1f}GB'}), 400
        
        # Academic Mode: Unlimited batch transcription access for research purposes
        current_app.logger.info("Academic mode enabled - unlimited batch transcription access for research")
        
        # Academic logging: Track batch processing details for research analytics
        estimated_total_duration = max(60 * len(files), total_file_size / (1024 * 1024) * 60)
        current_app.logger.info(f"Academic batch processing: {len(files)} files, {total_file_size / (1024*1024*1024):.1f}GB total, estimated {estimated_total_duration}s duration")
        
        # Second pass: process all files
        for i, file in enumerate(files):
            try:
                # Generate unique title for each file
                if len(files) == 1:
                    title = base_title
                else:
                    title = f"{base_title} - Μέρος {i+1}"
                
                # Step 1: Save audio file
                audio_file = audio_service.save_audio_file(file, user_id)
                
                logger.info(f"Batch audio file saved | user_id={user_id} | file={i+1}/{len(files)} | audio_file_id={audio_file.id}")
                
                # Step 2: Create transcription job
                transcription = transcription_service.create_transcription_with_metadata(
                    audio_file_id=audio_file.id,
                    user_id=user_id,
                    title=title,
                    description=description,
                    language=language,
                    ai_model=ai_model
                )
                
                results.append({
                    'file_index': i + 1,
                    'filename': file.filename,
                    'audio_file': audio_file.to_dict(),
                    'transcription': transcription.to_dict(),
                    'status': 'success'
                })
                
                logger.info(f"Batch transcription created | user_id={user_id} | file={i+1}/{len(files)} | transcription_id={transcription.id}")
                
            except Exception as e:
                logger.error(f"Error processing file {i+1}/{len(files)} | user_id={user_id} | filename={file.filename} | error={str(e)}")
                results.append({
                    'file_index': i + 1,
                    'filename': file.filename,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Count successful uploads
        successful_count = len([r for r in results if r['status'] == 'success'])
        failed_count = len(results) - successful_count
        
        logger.info(f"Batch upload completed | user_id={user_id} | total={len(files)} | successful={successful_count} | failed={failed_count}")
        
        return jsonify({
            'message': f'Batch upload completed: {successful_count} successful, {failed_count} failed',
            'summary': {
                'total_files': len(files),
                'successful': successful_count,
                'failed': failed_count
            },
            'results': results,
            'academic_mode': True  # Always in academic research mode
        }), 201 if successful_count > 0 else 400
        
    except Exception as e:
        logger.error(f"Batch upload and transcribe error | user_id={get_jwt_identity()} | error={str(e)}")
        return jsonify({'error': 'Failed to process batch upload'}), 500


@upload_bp.route('/ai-models', methods=['GET'])
@jwt_required()
@log_business_operation('get_ai_models')
def get_ai_models():
    """Get list of available AI models."""
    try:
        models = [
            {
                'id': 'whisper-large-v3',
                'name': 'Whisper Large V3',
                'description': 'Πιο ακριβές μοντέλο για ελληνικά (προτείνεται)',
                'languages': ['el', 'en'],
                'recommended': True
            },
            {
                'id': 'whisper-medium',
                'name': 'Whisper Medium',
                'description': 'Μεσαίο μοντέλο, ταχύτερο αλλά λιγότερο ακριβές',
                'languages': ['el', 'en'],
                'recommended': False
            },
            {
                'id': 'wav2vec2-greek',
                'name': 'Wav2Vec2 Greek',
                'description': 'Ειδικευμένο μοντέλο για ελληνικά',
                'languages': ['el'],
                'recommended': False
            }
        ]
        
        return jsonify({
            'ai_models': models,
            'default': 'whisper-large-v3'
        }), 200
        
    except Exception as e:
        logger.error(f"Get AI models error: {str(e)}")
        return jsonify({'error': 'Failed to get AI models'}), 500