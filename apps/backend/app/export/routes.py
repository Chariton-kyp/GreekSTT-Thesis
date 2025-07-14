from flask import Blueprint, request, jsonify, send_file, current_app, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import io
import json
import time
import pytz

def get_greek_time() -> datetime:
    """Get current time in Greek timezone (Europe/Athens)."""
    greek_tz = pytz.timezone('Europe/Athens')
    return datetime.now(greek_tz)

def format_greek_datetime(dt: datetime = None, format_str: str = '%d/%m/%Y %H:%M') -> str:
    """Format datetime in Greek timezone with specified format."""
    if dt is None:
        dt = get_greek_time()
    elif dt.tzinfo is None:
        # If datetime is naive, assume it's UTC and convert to Greek time
        dt = pytz.UTC.localize(dt).astimezone(pytz.timezone('Europe/Athens'))
    elif dt.tzinfo != pytz.timezone('Europe/Athens'):
        # Convert to Greek time if it's in a different timezone
        dt = dt.astimezone(pytz.timezone('Europe/Athens'))
    
    return dt.strftime(format_str)

from app.export.services import ExportService
from app.common.responses import success_response, error_response
from app.utils.correlation_logger import get_correlation_logger

logger = get_correlation_logger(__name__)

export_bp = Blueprint('export', __name__, url_prefix='/api/export')

@export_bp.route('/transcriptions', methods=['GET'])
@jwt_required()
def export_transcriptions():
    """Export transcription data in PDF or DOCX format."""
    try:
        user_id = get_jwt_identity()
        export_service = ExportService()
        
        # Get query parameters
        format = request.args.get('format', 'pdf')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        models = request.args.get('models', '').split(',') if request.args.get('models') else None
        
        # Get transcription data
        transcriptions = export_service.get_transcriptions_for_export(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            models=models
        )
        
        if format == 'pdf':
            pdf_data = export_service.transcriptions_to_pdf(transcriptions)
            return send_file(
                io.BytesIO(pdf_data),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'transcriptions-{format_greek_datetime(format_str="%Y%m%d")}.pdf'
            )
        
        elif format == 'docx':
            docx_data = export_service.transcriptions_to_docx(transcriptions)
            return send_file(
                io.BytesIO(docx_data),
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                as_attachment=True,
                download_name=f'transcriptions-{format_greek_datetime(format_str="%Y%m%d")}.docx'
            )
        
        else:
            return error_response('Unsupported format. Only PDF and DOCX are supported.', 400)
            
    except Exception as e:
        logger.error(f"Export transcriptions failed: {str(e)}")
        return error_response(f'Export failed: {str(e)}', 500)

@export_bp.route('/comparisons/<comparison_id>.<format>', methods=['GET'])
@jwt_required()
def export_comparison_result(comparison_id, format):
    """Export model comparison results in PDF or DOCX format."""
    try:
        user_id = get_jwt_identity()
        export_service = ExportService()
        
        # Get comparison data
        comparison = export_service.get_comparison_for_export(comparison_id, user_id)
        
        if not comparison:
            return error_response('Comparison not found', 404)
        
        if format == 'pdf':
            pdf_data = export_service.generate_comparison_pdf(comparison)
            return send_file(
                io.BytesIO(pdf_data),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'comparison-{comparison_id}.pdf'
            )
        
        elif format == 'docx':
            docx_data = export_service.generate_comparison_docx(comparison)
            return send_file(
                io.BytesIO(docx_data),
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                as_attachment=True,
                download_name=f'comparison-{comparison_id}.docx'
            )
        
        else:
            return error_response('Unsupported format. Only PDF and DOCX are supported.', 400)
            
    except Exception as e:
        logger.error(f"Export comparison failed: {str(e)}")
        return error_response(f'Export failed: {str(e)}', 500)