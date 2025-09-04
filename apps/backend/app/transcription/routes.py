"""Transcription routes."""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.common.decorators import validate_request
from app.schemas.transcription import UpdateTranscriptionTextSchema
from app.transcription.services import TranscriptionService
from app.utils.logging_middleware import log_business_operation
from app.common.responses import (
    transcription_success_response, transcription_error_response, 
    error_response, success_response
)
import logging

logger = logging.getLogger(__name__)

transcription_bp = Blueprint('transcription', __name__)
transcription_service = TranscriptionService()


@transcription_bp.route('', methods=['GET'])
@transcription_bp.route('/', methods=['GET'])
@jwt_required()
@log_business_operation('get_user_transcriptions')
def get_user_transcriptions():
    try:
        user_id = get_jwt_identity()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', request.args.get('limit', 20), type=int)
        status = request.args.get('status')
        sort = request.args.get('sort', 'created_at')
        order = request.args.get('order', 'desc')
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')
        
        transcriptions, pagination = transcription_service.get_user_transcriptions(
            user_id, page, per_page, status, sort, order, start_date, end_date, search
        )
        
        return success_response(
            message_key='OPERATION_SUCCESSFUL',
            data={
                'transcriptions': [t.to_dict() for t in transcriptions],
                'pagination': pagination,
                'academic_mode': True
            }
        )
        
    except Exception as e:
        current_app.logger.error(f"Get transcriptions error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@transcription_bp.route('/<int:transcription_id>', methods=['GET'])
@jwt_required()
@log_business_operation('get_transcription')
def get_transcription(transcription_id):
    try:
        user_id = get_jwt_identity()
        transcription = transcription_service.get_transcription(transcription_id, user_id)
        
        if not transcription:
            return transcription_error_response(
                message_key='TRANSCRIPTION_NOT_FOUND',
                error_code='TRANSCRIPTION_NOT_FOUND',
                status_code=404
            )
        
        include_segments = request.args.get('include_segments', 'false').lower() == 'true'
        
        result = transcription.to_dict()
        if include_segments:
            result['segments'] = [s.to_dict() for s in transcription.segments]
        
        return success_response(
            message_key='OPERATION_SUCCESSFUL',
            data={
                'transcription': result,
                'academic_mode': True
            }
        )
        
    except Exception as e:
        current_app.logger.error(f"Get transcription error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@transcription_bp.route('/<int:transcription_id>/download', methods=['GET'])
@jwt_required()
@log_business_operation('download_transcription')
def download_transcription(transcription_id):
    try:
        user_id = get_jwt_identity()
        format_type = request.args.get('format', 'txt')
        
        file_data, filename, mimetype = transcription_service.export_transcription(
            transcription_id, user_id, format_type
        )
        
        if not file_data:
            return transcription_error_response(
                message_key='TRANSCRIPTION_NOT_FOUND',
                error_code='TRANSCRIPTION_NOT_FOUND',
                status_code=404
            )
        
        from flask import send_file
        from io import BytesIO
        
        return send_file(
            BytesIO(file_data),
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except ValueError as e:
        return error_response(
            message=str(e),
            error_code='VALIDATION_ERROR',
            status_code=400
        )
    except Exception as e:
        current_app.logger.error(f"Download transcription error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@transcription_bp.route('/<int:transcription_id>', methods=['PUT'])
@jwt_required()
@validate_request(UpdateTranscriptionTextSchema)
@log_business_operation('update_transcription')
def update_transcription(transcription_id, validated_data):
    try:
        user_id = get_jwt_identity()
        
        transcription = transcription_service.update_transcription_text(
            transcription_id, user_id, validated_data['text']
        )
        
        if not transcription:
            return transcription_error_response(
                message_key='TRANSCRIPTION_NOT_FOUND',
                error_code='TRANSCRIPTION_NOT_FOUND',
                status_code=404
            )
        
        return transcription_success_response(
            message_key='TRANSCRIPTION_UPDATED_SUCCESSFULLY',
            data={'transcription': transcription.to_dict()}
        )
        
    except Exception as e:
        current_app.logger.error(f"Update transcription error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@transcription_bp.route('/<int:transcription_id>', methods=['DELETE'])
@jwt_required()
@log_business_operation('delete_transcription')
def delete_transcription(transcription_id):
    try:
        user_id = get_jwt_identity()
        
        if transcription_service.delete_transcription(transcription_id, user_id):
            return transcription_success_response(
                message_key='TRANSCRIPTION_DELETED_SUCCESSFULLY'
            )
        else:
            return transcription_error_response(
                message_key='TRANSCRIPTION_NOT_FOUND',
                error_code='TRANSCRIPTION_NOT_FOUND',
                status_code=404
            )
            
    except Exception as e:
        current_app.logger.error(f"Delete transcription error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@transcription_bp.route('/<int:transcription_id>/retry', methods=['POST'])
@jwt_required()
@log_business_operation('retry_transcription')
def retry_transcription(transcription_id):
    """Retry a failed transcription."""
    try:
        user_id = get_jwt_identity()
        
        current_app.logger.info("Academic mode - unlimited retry access granted for research")
        
        transcription = transcription_service.get_transcription(transcription_id, user_id)
        if transcription and transcription.audio_file:
            current_app.logger.info(f"Academic retry: processing {transcription.audio_file.duration_seconds}s audio")
        
        transcription = transcription_service.retry_transcription(transcription_id, user_id)
        
        if not transcription:
            return transcription_error_response(
                message_key='TRANSCRIPTION_NOT_FOUND',
                error_code='TRANSCRIPTION_NOT_FOUND',
                status_code=404
            )
        
        return transcription_success_response(
            message_key='TRANSCRIPTION_RETRY_STARTED',
            data={
                'transcription': transcription.to_dict(),
                'academic_mode': True
            }
        )
        
    except Exception as e:
        current_app.logger.error(f"Retry transcription error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@transcription_bp.route('/<int:transcription_id>/summarize', methods=['POST'])
@jwt_required()
@log_business_operation('generate_summary')
def generate_summary(transcription_id):
    """Generate AI summary for transcription."""
    try:
        user_id = get_jwt_identity()
        
        transcription = transcription_service.get_transcription(transcription_id, user_id)
        
        if not transcription:
            return transcription_error_response(
                message_key='TRANSCRIPTION_NOT_FOUND',
                error_code='TRANSCRIPTION_NOT_FOUND',
                status_code=404
            )
        
        if transcription.status != 'completed':
            return error_response(
                message='Transcription must be completed to generate summary',
                error_code='TRANSCRIPTION_NOT_COMPLETED',
                status_code=400
            )
        
        summary = transcription_service.generate_ai_summary(transcription_id, user_id)
        
        if not summary:
            return error_response(
                message='Failed to generate summary',
                error_code='SUMMARY_GENERATION_FAILED',
                status_code=500
            )
        
        return success_response(
            message_key='SUMMARY_GENERATED_SUCCESSFULLY',
            data={'summary': summary}
        )
        
    except Exception as e:
        current_app.logger.error(f"Generate summary error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@transcription_bp.route('/<int:transcription_id>/segments', methods=['GET'])
@jwt_required()
@log_business_operation('get_transcription_segments')
def get_transcription_segments(transcription_id):
    """Get transcription segments."""
    try:
        user_id = get_jwt_identity()
        
        transcription = transcription_service.get_transcription(transcription_id, user_id)
        
        if not transcription:
            return transcription_error_response(
                message_key='TRANSCRIPTION_NOT_FOUND',
                error_code='TRANSCRIPTION_NOT_FOUND',
                status_code=404
            )
        
        segments = [s.to_dict() for s in transcription.segments]
        
        return success_response(
            message_key='OPERATION_SUCCESSFUL',
            data={'segments': segments}
        )
        
    except Exception as e:
        current_app.logger.error(f"Get segments error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )



@transcription_bp.route('/<int:transcription_id>/segments/<int:segment_index>', methods=['PUT'])
@jwt_required()
@log_business_operation('update_segment')
def update_segment(transcription_id, segment_index):
    """Update a specific segment."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'text' not in data:
            return error_response(
                message='Text is required',
                error_code='VALIDATION_ERROR',
                status_code=400
            )
        
        transcription = transcription_service.get_transcription(transcription_id, user_id)
        
        if not transcription:
            return transcription_error_response(
                message_key='TRANSCRIPTION_NOT_FOUND',
                error_code='TRANSCRIPTION_NOT_FOUND',
                status_code=404
            )
        
        success = transcription_service.update_segment(
            transcription_id, segment_index, data['text'], user_id
        )
        
        if not success:
            return error_response(
                message='Segment not found or update failed',
                error_code='SEGMENT_UPDATE_FAILED',
                status_code=400
            )
        
        return success_response(
            message_key='SEGMENT_UPDATED_SUCCESSFULLY'
        )
        
    except Exception as e:
        current_app.logger.error(f"Update segment error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@transcription_bp.route('/validate-url', methods=['POST'])
@jwt_required()
@log_business_operation('validate_video_url')
def validate_url():
    """Validate URL and return video metadata without downloading."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'url' not in data:
            return error_response(
                message='URL is required',
                error_code='VALIDATION_ERROR',
                status_code=400
            )
        
        url = data['url'].strip()
        
        if not url:
            return error_response(
                message='URL cannot be empty',
                error_code='VALIDATION_ERROR',
                status_code=400
            )
        
        logger.info(f"URL validation request | user_id={user_id} | url={url}")
        
        from app.transcription.url_service import URLProcessingService
        url_service = URLProcessingService()
        
        if not url_service.is_supported_url(url):
            return error_response(
                message='Unsupported video platform. Supported platforms: YouTube, Vimeo',
                error_code='UNSUPPORTED_PLATFORM',
                status_code=400
            )
        
        try:
            metadata = url_service.extract_metadata(url)
            
            logger.info(f"URL validation successful | user_id={user_id} | title={metadata['title']} | duration={metadata['duration_string']} | platform={metadata['platform']}")
            
            return success_response(
                message_key='URL_VALIDATED_SUCCESSFULLY',
                message_category='TRANSCRIPTION_MESSAGES',
                data={
                    'metadata': metadata,
                    'supported_platforms': url_service.get_supported_platforms()
                }
            )
            
        except ValueError as e:
            logger.warning(f"URL validation failed | user_id={user_id} | url={url} | error={str(e)}")
            return error_response(
                message=f'Failed to process URL: {str(e)}',
                error_code='URL_PROCESSING_FAILED',
                status_code=400
            )
        
    except Exception as e:
        current_app.logger.error(f"URL validation error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


@transcription_bp.route('/from-url', methods=['POST'])
@jwt_required()
@log_business_operation('transcription_from_url')
def transcribe_from_url():
    """Create transcription from video/audio URL."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['url', 'title', 'language']
        for field in required_fields:
            if not data.get(field):
                return error_response(
                    message=f'{field} is required',
                    error_code='VALIDATION_ERROR',
                    status_code=400
                )
        
        url = data['url'].strip()
        title = data['title'].strip()
        description = data.get('description', '').strip()
        language = data.get('language', 'el')
        ai_model = data.get('ai_model', 'whisper-large-v3')
        
        if len(title) < 3:
            return error_response(
                message='Title must be at least 3 characters long',
                error_code='VALIDATION_ERROR',
                status_code=400
            )
        
        if len(title) > 200:
            return error_response(
                message='Title must be less than 200 characters',
                error_code='VALIDATION_ERROR',
                status_code=400
            )
        
        if description and len(description) > 1000:
            return error_response(
                message='Description must be less than 1000 characters',
                error_code='VALIDATION_ERROR',
                status_code=400
            )
        
        if language not in ['el', 'en']:
            return error_response(
                message='Language must be "el" or "en"',
                error_code='VALIDATION_ERROR',
                status_code=400
            )
        
        valid_models = ['whisper', 'wav2vec2', 'both', 'whisper-large-v3', 'whisper-medium', 'wav2vec2-greek', 'compare']
        if ai_model not in valid_models:
            return error_response(
                message='Invalid AI model',
                error_code='VALIDATION_ERROR',
                status_code=400
            )
        
        if ai_model in ['whisper-large-v3', 'whisper-medium']:
            ai_model = 'whisper'
        elif ai_model == 'wav2vec2-greek':
            ai_model = 'wav2vec2'
        elif ai_model == 'compare':
            ai_model = 'both'
        
        logger.info(f"URL transcription request | user_id={user_id} | url={url} | title={title} | language={language} | ai_model={ai_model}")
        
        from app.transcription.url_service import URLProcessingService
        from app.audio.services import AudioService
        
        url_service = URLProcessingService()
        audio_service = AudioService()
        
        if not url_service.is_supported_url(url):
            return error_response(
                message='Unsupported video platform',
                error_code='UNSUPPORTED_PLATFORM',
                status_code=400
            )
        
        try:
            metadata = url_service.extract_metadata(url)
            logger.info(f"URL metadata extracted | duration={metadata['duration_string']} | platform={metadata['platform']}")
        except ValueError as e:
            return error_response(
                message=f'Failed to process URL: {str(e)}',
                error_code='URL_PROCESSING_FAILED',
                status_code=400
            )
        
        current_app.logger.info("Academic mode enabled - unlimited URL transcription access for research")
        
        duration = metadata.get('duration', 60)
        current_app.logger.info(f"Academic URL processing: {duration}s duration content from {metadata.get('platform', 'unknown')} platform")
        
        try:
            logger.info(f"Starting audio download from URL | user_id={user_id}")
            audio_file_path = url_service.download_audio(url, user_id, title)
            
            audio_file = audio_service.save_audio_from_path(
                file_path=audio_file_path,
                original_filename=f"{title}.mp3",
                user_id=user_id,
                source_url=url,
                metadata=metadata
            )
            
            logger.info(f"Audio file saved | user_id={user_id} | audio_file_id={audio_file.id} | duration={audio_file.duration_seconds}s")
            
            url_service.cleanup_temp_file(audio_file_path)
            
        except Exception as e:
            logger.error(f"Audio download failed | user_id={user_id} | url={url} | error={str(e)}")
            return error_response(
                message=f'Failed to download audio: {str(e)}',
                error_code='AUDIO_DOWNLOAD_FAILED',
                status_code=500
            )
        
        try:
            transcription = transcription_service.create_transcription_with_metadata(
                audio_file_id=audio_file.id,
                user_id=user_id,
                title=title,
                description=description,
                language=language,
                ai_model=ai_model
            )
            
            logger.info(f"URL transcription job created | user_id={user_id} | transcription_id={transcription.id} | status={transcription.status}")
            
            return transcription_success_response(
                message_key='TRANSCRIPTION_STARTED',
                data={
                    'transcription': transcription.to_dict(),
                    'audio_file': audio_file.to_dict(),
                    'source_metadata': metadata,
                    'academic_mode': True
                },
                status_code=201
            )
            
        except Exception as e:
            logger.error(f"Transcription creation failed | user_id={user_id} | error={str(e)}")
            return error_response(
                message=f'Failed to create transcription: {str(e)}',
                error_code='TRANSCRIPTION_CREATION_FAILED',
                status_code=500
            )
        
    except Exception as e:
        current_app.logger.error(f"URL transcription error: {str(e)}")
        return error_response(
            message_key='INTERNAL_SERVER_ERROR',
            error_code='SYSTEM_ERROR',
            status_code=500
        )


# =============================================================================
# =============================================================================

@transcription_bp.route('/<int:transcription_id>/evaluate', methods=['POST'])
@jwt_required()
@log_business_operation('evaluate_transcription_wer_cer')
def evaluate_transcription(transcription_id):
    """Evaluate transcription accuracy with ground truth text."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'ground_truth' not in data:
            return error_response(
                message='Ground truth text is required',
                error_code='VALIDATION_ERROR',
                status_code=400
            )
        
        ground_truth = data['ground_truth'].strip()
        notes = data.get('notes', '').strip()
        
        
        if not ground_truth:
            return error_response(
                message='Ground truth text cannot be empty',
                error_code='VALIDATION_ERROR',
                status_code=400
            )
        
        transcription = transcription_service.get_transcription(transcription_id, user_id)
        if not transcription:
            return error_response(
                message='Transcription not found',
                error_code='TRANSCRIPTION_NOT_FOUND',
                status_code=404
            )
        
        evaluation_results = transcription.evaluate_with_ground_truth(
            ground_truth=ground_truth,
            user_id=user_id,
            notes=notes
        )
        
        logger.info(f"Transcription evaluation completed | transcription_id={transcription_id} | user_id={user_id} | whisper_wer={evaluation_results.get('whisper_wer')} | wav2vec_wer={evaluation_results.get('wav2vec_wer')}")
        
        return success_response(
            message='Evaluation completed successfully',
            data={
                'evaluation_results': evaluation_results,
                'transcription': transcription.to_dict()
            }
        )
        
    except Exception as e:
        logger.error(f"Transcription evaluation failed | transcription_id={transcription_id} | user_id={user_id} | error={str(e)}")
        return error_response(
            message=f'Failed to evaluate transcription: {str(e)}',
            error_code='EVALUATION_FAILED',
            status_code=500
        )


@transcription_bp.route('/<int:transcription_id>/wer-cer', methods=['GET'])
@jwt_required()
@log_business_operation('get_transcription_wer_cer')
def get_transcription_wer_cer(transcription_id):
    """Get WER/CER evaluation results for a transcription."""
    try:
        user_id = get_jwt_identity()
        
        transcription = transcription_service.get_transcription(transcription_id, user_id)
        if not transcription:
            return error_response(
                message='Transcription not found',
                error_code='TRANSCRIPTION_NOT_FOUND',
                status_code=404
            )
        
        evaluation_data = {
            'has_evaluation': transcription.evaluation_completed,
            'ground_truth_text': transcription.ground_truth_text,
            
            'whisper_wer': transcription.whisper_wer,
            'whisper_cer': transcription.whisper_cer,
            'wav2vec_wer': transcription.wav2vec_wer,
            'wav2vec_cer': transcription.wav2vec_cer,
            
            'academic_accuracy_score': transcription.academic_accuracy_score,
            'best_performing_model': transcription.best_performing_model,
            'evaluation_date': transcription.evaluation_date.isoformat() if transcription.evaluation_date else None,
            'evaluation_notes': transcription.evaluation_notes,
            
            'whisper_accuracy': transcription.whisper_accuracy,
            'wav2vec_accuracy': transcription.wav2vec_accuracy,
            'whisper_char_accuracy': transcription.whisper_char_accuracy,
            'wav2vec_char_accuracy': transcription.wav2vec_char_accuracy,
            
            'whisper_diacritic_accuracy': transcription.whisper_diacritic_accuracy,
            'wav2vec_diacritic_accuracy': transcription.wav2vec_diacritic_accuracy,
            'whisper_greek_char_accuracy': transcription.whisper_greek_char_accuracy,
            'wav2vec_greek_char_accuracy': transcription.wav2vec_greek_char_accuracy,
            
            'whisper_substitutions': transcription.whisper_substitutions,
            'whisper_deletions': transcription.whisper_deletions,
            'whisper_insertions': transcription.whisper_insertions,
            'wav2vec_substitutions': transcription.wav2vec_substitutions,
            'wav2vec_deletions': transcription.wav2vec_deletions,
            'wav2vec_insertions': transcription.wav2vec_insertions,
        }
        
        return success_response(
            message='WER/CER data retrieved successfully',
            data=evaluation_data
        )
        
    except Exception as e:
        logger.error(f"Get WER/CER failed | transcription_id={transcription_id} | user_id={user_id} | error={str(e)}")
        return error_response(
            message=f'Failed to get WER/CER data: {str(e)}',
            error_code='WER_CER_RETRIEVAL_FAILED',
            status_code=500
        )