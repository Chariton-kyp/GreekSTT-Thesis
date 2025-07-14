"""Research analytics service for thesis project - FIXED VERSION."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import func, and_, distinct
from app.extensions import db
from app.transcription.models import Transcription
from app.audio.models import AudioFile
from app.utils.correlation_logger import get_correlation_logger

logger = get_correlation_logger(__name__)


class ResearchAnalyticsService:
    """Simplified analytics service focused on research metrics."""
    
    def __init__(self):
        logger.info("Research analytics service initialized")
    
    # User-specific analytics methods for frontend compatibility
    
    def get_user_transcription_count(self, user_id: int) -> int:
        """Get total transcription count for a user."""
        try:
            return db.session.query(func.count(Transcription.id))\
                .filter(Transcription.user_id == user_id)\
                .scalar() or 0
        except Exception as e:
            logger.error(f"Error getting user transcription count: {str(e)}")
            return 0
    
    def get_user_model_usage(self, user_id: int, model_name: str) -> int:
        """Get model usage count for a user."""
        try:
            # Map display names to database names
            db_model_names = []
            if model_name == 'whisper':
                db_model_names = ['whisper', 'faster-whisper']
            elif model_name == 'wav2vec2':
                db_model_names = ['wav2vec2']
            else:
                db_model_names = [model_name]
            
            return db.session.query(func.count(Transcription.id))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.model_used.in_(db_model_names)
                    )
                )\
                .scalar() or 0
        except Exception as e:
            logger.error(f"Error getting user model usage: {str(e)}")
            return 0
    
    def get_user_comparison_count(self, user_id: int) -> int:
        """Get comparison count for a user - count 'both' model entries."""
        try:
            return db.session.query(func.count(Transcription.id))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.model_used == 'both'
                    )
                )\
                .scalar() or 0
        except Exception as e:
            logger.error(f"Error getting user comparison count: {str(e)}")
            return 0
    
    def get_user_avg_accuracy(self, user_id: int) -> float:
        """Get average accuracy for a user using academic_accuracy_score."""
        try:
            avg_accuracy = db.session.query(func.avg(Transcription.academic_accuracy_score))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.academic_accuracy_score.isnot(None)
                    )
                )\
                .scalar()
            return round(float(avg_accuracy or 0), 2)
        except Exception as e:
            logger.error(f"Error getting user average accuracy: {str(e)}")
            return 0.0
    
    def get_user_avg_processing_time(self, user_id: int) -> float:
        """Get average processing time for a user from both whisper and wav2vec columns."""
        try:
            # Get average from both whisper and wav2vec processing times
            whisper_avg = db.session.query(func.avg(Transcription.whisper_processing_time))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.whisper_processing_time.isnot(None)
                    )
                )\
                .scalar() or 0
            
            wav2vec_avg = db.session.query(func.avg(Transcription.wav2vec_processing_time))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.wav2vec_processing_time.isnot(None)
                    )
                )\
                .scalar() or 0
            
            # Calculate overall average
            times = []
            if whisper_avg > 0:
                times.append(whisper_avg)
            if wav2vec_avg > 0:
                times.append(wav2vec_avg)
            
            if times:
                return round(sum(times) / len(times), 2)
            return 0.0
        except Exception as e:
            logger.error(f"Error getting user average processing time: {str(e)}")
            return 0.0
    
    def get_user_best_accuracy(self, user_id: int) -> float:
        """Get best accuracy score for a user."""
        try:
            best_accuracy = db.session.query(func.max(Transcription.academic_accuracy_score))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.academic_accuracy_score.isnot(None)
                    )
                )\
                .scalar()
            return round(float(best_accuracy or 0), 2)
        except Exception as e:
            logger.error(f"Error getting user best accuracy: {str(e)}")
            return 0.0
    
    def get_user_recent_transcriptions(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get recent transcriptions for a user."""
        try:
            recent = db.session.query(Transcription)\
                .filter(Transcription.user_id == user_id)\
                .order_by(Transcription.created_at.desc())\
                .limit(limit)\
                .all()
            
            return [
                {
                    'id': t.id,
                    'model_used': t.model_used,
                    'academic_accuracy_score': t.academic_accuracy_score,
                    'whisper_wer': t.whisper_wer,
                    'wav2vec_wer': t.wav2vec_wer,
                    'whisper_processing_time': t.whisper_processing_time,
                    'wav2vec_processing_time': t.wav2vec_processing_time,
                    'created_at': t.created_at.isoformat() if t.created_at else None,
                    'completedAt': t.completed_at.isoformat() if t.completed_at else None
                }
                for t in recent
            ]
        except Exception as e:
            logger.error(f"Error getting user recent transcriptions: {str(e)}")
            return []
    
    def get_user_weekly_activity(self, user_id: int) -> List[Dict]:
        """Get weekly activity for a user."""
        try:
            # Get last 7 days of activity
            result = []
            today = datetime.utcnow().date()
            
            for i in range(7):
                date = today - timedelta(days=i)
                start_day = datetime.combine(date, datetime.min.time())
                end_day = start_day + timedelta(days=1)
                
                count = db.session.query(func.count(Transcription.id))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.created_at >= start_day,
                            Transcription.created_at < end_day
                        )
                    )\
                    .scalar() or 0
                
                result.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': count
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting user weekly activity: {str(e)}")
            return []
    
    def get_user_preferred_model(self, user_id: int) -> str:
        """Get most used model by a user."""
        try:
            model_counts = db.session.query(
                Transcription.model_used,
                func.count(Transcription.id).label('count')
            )\
            .filter(Transcription.user_id == user_id)\
            .group_by(Transcription.model_used)\
            .order_by(func.count(Transcription.id).desc())\
            .first()
            
            # Map database model names to display names
            if model_counts:
                model_name = model_counts.model_used
                if model_name in ['faster-whisper', 'whisper']:
                    return 'Whisper-Large-3'
                elif model_name == 'wav2vec2':
                    return 'wav2vec2-Greek'
                elif model_name == 'both':
                    return 'Model Comparison'
                else:
                    return model_name
            return 'Whisper-Large-3'
        except Exception as e:
            logger.error(f"Error getting user preferred model: {str(e)}")
            return 'Whisper-Large-3'
    
    def get_user_most_used_format(self, user_id: int) -> str:
        """Get most used audio format by a user."""
        try:
            # Join with audio files to get mime_type info
            format_count = db.session.query(AudioFile.mime_type)\
                .join(Transcription, AudioFile.id == Transcription.audio_file_id)\
                .filter(Transcription.user_id == user_id)\
                .group_by(AudioFile.mime_type)\
                .order_by(func.count(AudioFile.mime_type).desc())\
                .first()
            
            if format_count and format_count[0]:
                mime_type = format_count[0]
                if 'mp3' in mime_type:
                    return 'MP3'
                elif 'wav' in mime_type:
                    return 'WAV'
                elif 'mp4' in mime_type:
                    return 'MP4'
                else:
                    return mime_type.split('/')[-1].upper()
            return 'MP3'
        except Exception as e:
            logger.error(f"Error getting user most used format: {str(e)}")
            return 'MP3'
    
    def get_user_avg_file_size(self, user_id: int) -> float:
        """Get average file size for a user."""
        try:
            avg_size = db.session.query(func.avg(AudioFile.file_size))\
                .join(Transcription, AudioFile.id == Transcription.audio_file_id)\
                .filter(Transcription.user_id == user_id)\
                .scalar()
            
            return round(float(avg_size or 0) / 1024 / 1024, 2)  # Convert to MB
        except Exception as e:
            logger.error(f"Error getting user average file size: {str(e)}")
            return 0.0
    
    def get_user_insights_count(self, user_id: int) -> int:
        """Get number of insights generated for a user (comparison count)."""
        return self.get_user_comparison_count(user_id)
    
    def get_user_avg_wer(self, user_id: int) -> float:
        """Get average WER for a user across all models."""
        try:
            # Get average from both whisper and wav2vec WER scores
            whisper_wer = db.session.query(func.avg(Transcription.whisper_wer))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.whisper_wer.isnot(None)
                    )
                )\
                .scalar() or 0
            
            wav2vec_wer = db.session.query(func.avg(Transcription.wav2vec_wer))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.wav2vec_wer.isnot(None)
                    )
                )\
                .scalar() or 0
            
            # Calculate overall average
            wers = []
            if whisper_wer > 0:
                wers.append(whisper_wer)
            if wav2vec_wer > 0:
                wers.append(wav2vec_wer)
            
            if wers:
                return round(sum(wers) / len(wers), 2)
            return 0.0
        except Exception as e:
            logger.error(f"Error getting user average WER: {str(e)}")
            return 0.0


# Global instance
research_analytics_service_fixed = ResearchAnalyticsService()