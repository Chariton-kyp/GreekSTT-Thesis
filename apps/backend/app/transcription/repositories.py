"""Transcription repositories."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_
from app.common.repository import BaseRepository
from app.transcription.models import Transcription, TranscriptionSegment


class TranscriptionRepository(BaseRepository):
    """Repository for transcription data access."""
    
    def __init__(self):
        super().__init__(Transcription)
    
    def get_by_audio_file(self, audio_file_id: int) -> List[Transcription]:
        """Get all transcriptions for an audio file."""
        return self.model.query.filter_by(
            audio_file_id=audio_file_id,
            is_deleted=False
        ).all()
    
    def get_by_template(self, template_id: int) -> List[Transcription]:
        """Get all transcriptions using a specific template."""
        return self.model.query.filter_by(
            template_id=template_id,
            is_deleted=False
        ).all()
    
    def get_pending_transcriptions(self) -> List[Transcription]:
        """Get all pending transcriptions."""
        return self.model.query.filter_by(
            status='pending',
            is_deleted=False
        ).all()
    
    def get_processing_transcriptions(self) -> List[Transcription]:
        """Get all transcriptions currently being processed."""
        return self.model.query.filter_by(
            status='processing',
            is_deleted=False
        ).all()
    
    def paginate(self, page: int = 1, per_page: int = 20, 
                 filters: Optional[Dict[str, Any]] = None,
                 sort_by: str = 'created_at',
                 sort_order: str = 'desc') -> Dict[str, Any]:
        """Get paginated results with audio_file relationship loaded and advanced filtering."""
        query = self.model.query.options(joinedload(Transcription.audio_file)).filter_by(is_deleted=False)
        
        if filters:
            # Handle simple filters
            simple_filters = {}
            for key, value in filters.items():
                if key not in ['start_date', 'end_date', 'search']:
                    simple_filters[key] = value
            
            if simple_filters:
                query = query.filter_by(**simple_filters)
            
            # Handle date range filtering
            if 'start_date' in filters and filters['start_date']:
                try:
                    # Frontend sends YYYY-MM-DD, convert to start of day UTC
                    start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d')
                    query = query.filter(Transcription.created_at >= start_date)
                except ValueError:
                    pass  # Invalid date format, ignore
            
            if 'end_date' in filters and filters['end_date']:
                try:
                    # Frontend sends YYYY-MM-DD, convert to end of day UTC
                    end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d')
                    # Add 23:59:59 to include the entire end date
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                    query = query.filter(Transcription.created_at <= end_date)
                except ValueError:
                    pass  # Invalid date format, ignore
            
            # Handle text search
            if 'search' in filters and filters['search']:
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Transcription.title.ilike(search_term),
                        Transcription.description.ilike(search_term),
                        Transcription.text.ilike(search_term)
                    )
                )
        
        # Add sorting
        if hasattr(self.model, sort_by):
            sort_attr = getattr(self.model, sort_by)
            if sort_order.lower() == 'desc':
                query = query.order_by(sort_attr.desc())
            else:
                query = query.order_by(sort_attr.asc())
        
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return {
            'items': pagination.items,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    
    def get_by_id(self, id: int) -> Optional[Transcription]:
        """Get a transcription by ID with audio_file relationship loaded."""
        return self.model.query.options(joinedload(Transcription.audio_file)).filter_by(
            id=id,
            is_deleted=False
        ).first()


class TranscriptionSegmentRepository(BaseRepository):
    """Repository for transcription segment data access."""
    
    def __init__(self):
        super().__init__(TranscriptionSegment)
    
    def get_by_transcription(self, transcription_id: int) -> List[TranscriptionSegment]:
        """Get all segments for a transcription."""
        return self.model.query.filter_by(
            transcription_id=transcription_id,
            is_deleted=False
        ).order_by(TranscriptionSegment.start_time).all()