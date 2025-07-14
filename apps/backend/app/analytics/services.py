"""Research analytics service for thesis project."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import func, and_, or_, distinct
from app.extensions import db
from app.transcription.models import Transcription
from app.audio.models import AudioFile
from app.utils.correlation_logger import get_correlation_logger

logger = get_correlation_logger(__name__)


class ResearchAnalyticsService:
    """Simplified analytics service focused on research metrics."""
    
    def __init__(self):
        logger.info("Research analytics service initialized")
    
    # Core Research Metrics
    
    def get_total_transcriptions(self) -> int:
        """Get total number of transcriptions (only active, non-deleted)."""
        try:
            return db.session.query(func.count(Transcription.id))\
                .filter(
                    and_(
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .scalar() or 0
        except Exception as e:
            logger.error(f"Error getting total transcriptions: {str(e)}")
            return 0
    
    def get_model_usage(self, model_name: str) -> int:
        """Get usage count for a specific model (only active, non-deleted)."""
        try:
            return db.session.query(func.count(Transcription.id))\
                .filter(
                    and_(
                        Transcription.model_used == model_name,
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .scalar() or 0
        except Exception as e:
            logger.error(f"Error getting model usage for {model_name}: {str(e)}")
            return 0
    
    def get_comparison_count(self) -> int:
        """Get total number of model comparisons (only active, non-deleted 'both' transcriptions)."""
        try:
            # Count 'both' transcriptions (comparison mode)
            comparison_count = db.session.query(func.count(Transcription.id))\
                .filter(
                    and_(
                        Transcription.model_used == 'both',
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .scalar() or 0
            
            return comparison_count
        except Exception as e:
            logger.error(f"Error getting comparison count: {str(e)}")
            return 0
    
    def get_avg_accuracy(self, model_name: str) -> float:
        """Get average accuracy for a specific model (only active, non-deleted)."""
        try:
            if model_name == 'whisper':
                avg_accuracy = db.session.query(func.avg(Transcription.whisper_accuracy))\
                    .filter(
                        and_(
                            Transcription.whisper_accuracy.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar()
            elif model_name == 'wav2vec2':
                avg_accuracy = db.session.query(func.avg(Transcription.wav2vec_accuracy))\
                    .filter(
                        and_(
                            Transcription.wav2vec_accuracy.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar()
            else:
                # For other models, check both columns and take the average
                whisper_avg = db.session.query(func.avg(Transcription.whisper_accuracy))\
                    .filter(
                        and_(
                            Transcription.whisper_accuracy.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar() or 0
                wav2vec_avg = db.session.query(func.avg(Transcription.wav2vec_accuracy))\
                    .filter(
                        and_(
                            Transcription.wav2vec_accuracy.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar() or 0
                avg_accuracy = (whisper_avg + wav2vec_avg) / 2 if whisper_avg or wav2vec_avg else 0
            
            return round(float(avg_accuracy or 0), 2)
        except Exception as e:
            logger.error(f"Error getting average accuracy for {model_name}: {str(e)}")
            return 0.0
    
    def get_avg_wer(self, model_name: str) -> float:
        """Get average Word Error Rate for a specific model (only active, non-deleted)."""
        try:
            if model_name == 'whisper':
                avg_wer = db.session.query(func.avg(Transcription.whisper_wer))\
                    .filter(
                        and_(
                            Transcription.whisper_wer.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar()
            elif model_name == 'wav2vec2':
                avg_wer = db.session.query(func.avg(Transcription.wav2vec_wer))\
                    .filter(
                        and_(
                            Transcription.wav2vec_wer.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar()
            else:
                # For other models, check both columns and take the average
                whisper_wer = db.session.query(func.avg(Transcription.whisper_wer))\
                    .filter(
                        and_(
                            Transcription.whisper_wer.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar() or 0
                wav2vec_wer = db.session.query(func.avg(Transcription.wav2vec_wer))\
                    .filter(
                        and_(
                            Transcription.wav2vec_wer.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar() or 0
                avg_wer = (whisper_wer + wav2vec_wer) / 2 if whisper_wer or wav2vec_wer else 0
            
            return round(float(avg_wer or 0), 2)
        except Exception as e:
            logger.error(f"Error getting average WER for {model_name}: {str(e)}")
            return 0.0
    
    def get_avg_cer(self, model_name: str) -> float:
        """Get average Character Error Rate for a specific model (only active, non-deleted)."""
        try:
            if model_name == 'whisper':
                avg_cer = db.session.query(func.avg(Transcription.whisper_cer))\
                    .filter(
                        and_(
                            Transcription.whisper_cer.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar()
            elif model_name == 'wav2vec2':
                avg_cer = db.session.query(func.avg(Transcription.wav2vec_cer))\
                    .filter(
                        and_(
                            Transcription.wav2vec_cer.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar()
            else:
                # For other models, check both columns and take the average
                whisper_cer = db.session.query(func.avg(Transcription.whisper_cer))\
                    .filter(
                        and_(
                            Transcription.whisper_cer.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar() or 0
                wav2vec_cer = db.session.query(func.avg(Transcription.wav2vec_cer))\
                    .filter(
                        and_(
                            Transcription.wav2vec_cer.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar() or 0
                avg_cer = (whisper_cer + wav2vec_cer) / 2 if whisper_cer or wav2vec_cer else 0
            
            return round(float(avg_cer or 0), 2)
        except Exception as e:
            logger.error(f"Error getting average CER for {model_name}: {str(e)}")
            return 0.0
    
    def get_avg_processing_time(self, model_name: str) -> float:
        """Get average processing time for a specific model (only active, non-deleted)."""
        try:
            if model_name == 'whisper' or model_name == 'faster-whisper':
                avg_time = db.session.query(func.avg(Transcription.whisper_processing_time))\
                    .filter(
                        and_(
                            Transcription.whisper_processing_time.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar()
            elif model_name == 'wav2vec2':
                avg_time = db.session.query(func.avg(Transcription.wav2vec_processing_time))\
                    .filter(
                        and_(
                            Transcription.wav2vec_processing_time.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar()
            else:
                # For other models, check both columns and take the average
                whisper_time = db.session.query(func.avg(Transcription.whisper_processing_time))\
                    .filter(
                        and_(
                            Transcription.whisper_processing_time.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar() or 0
                wav2vec_time = db.session.query(func.avg(Transcription.wav2vec_processing_time))\
                    .filter(
                        and_(
                            Transcription.wav2vec_processing_time.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar() or 0
                avg_time = (whisper_time + wav2vec_time) / 2 if whisper_time or wav2vec_time else 0
            
            return round(float(avg_time or 0), 2)
        except Exception as e:
            logger.error(f"Error getting average processing time for {model_name}: {str(e)}")
            return 0.0
    
    # Research Dashboard Summary
    
    def get_research_dashboard_stats(self) -> Dict[str, Any]:
        """Get core research statistics for thesis dashboard."""
        try:
            # Model usage
            whisper_count = self.get_model_usage('whisper')
            wav2vec_count = self.get_model_usage('wav2vec2')
            
            # Accuracy metrics
            whisper_accuracy = self.get_avg_accuracy('whisper')
            wav2vec_accuracy = self.get_avg_accuracy('wav2vec2')
            
            # Error rates
            whisper_wer = self.get_avg_wer('whisper')
            wav2vec_wer = self.get_avg_wer('wav2vec2')
            whisper_cer = self.get_avg_cer('whisper')
            wav2vec_cer = self.get_avg_cer('wav2vec2')
            
            # Processing times
            whisper_time = self.get_avg_processing_time('whisper')
            wav2vec_time = self.get_avg_processing_time('wav2vec2')
            
            return {
                'total_transcriptions': self.get_total_transcriptions(),
                'comparison_count': self.get_comparison_count(),
                'model_usage': {
                    'whisper': whisper_count,
                    'wav2vec2': wav2vec_count
                },
                'accuracy_metrics': {
                    'whisper': {
                        'accuracy': whisper_accuracy,
                        'wer': whisper_wer,
                        'cer': whisper_cer,
                        'processing_time': whisper_time
                    },
                    'wav2vec2': {
                        'accuracy': wav2vec_accuracy,
                        'wer': wav2vec_wer,
                        'cer': wav2vec_cer,
                        'processing_time': wav2vec_time
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error getting research dashboard stats: {str(e)}")
            return {}
    
    def get_model_comparison_data(self) -> List[Dict[str, Any]]:
        """Get data for model comparison charts."""
        try:
            # Get transcriptions with both models for the same audio file
            comparison_data = []
            
            # Find audio files with both transcriptions
            audio_files_with_both = db.session.query(Transcription.audio_file_id)\
                .group_by(Transcription.audio_file_id)\
                .having(func.count(distinct(Transcription.model_used)) >= 2)\
                .limit(50)  # Limit for performance
            
            for audio_file_id in audio_files_with_both:
                whisper_trans = db.session.query(Transcription)\
                    .filter(
                        and_(
                            Transcription.audio_file_id == audio_file_id[0],
                            Transcription.model_used == 'whisper'
                        )
                    ).first()
                
                wav2vec_trans = db.session.query(Transcription)\
                    .filter(
                        and_(
                            Transcription.audio_file_id == audio_file_id[0],
                            Transcription.model_used == 'wav2vec2'
                        )
                    ).first()
                
                if whisper_trans and wav2vec_trans:
                    comparison_data.append({
                        'audio_file_id': audio_file_id[0],
                        'whisper': {
                            'wer': whisper_trans.wer_score or 0,
                            'cer': whisper_trans.cer_score or 0,
                            'accuracy': whisper_trans.accuracy_score or 0,
                            'processing_time': whisper_trans.processing_time or 0
                        },
                        'wav2vec2': {
                            'wer': wav2vec_trans.wer_score or 0,
                            'cer': wav2vec_trans.cer_score or 0,
                            'accuracy': wav2vec_trans.accuracy_score or 0,
                            'processing_time': wav2vec_trans.processing_time or 0
                        }
                    })
            
            return comparison_data
        except Exception as e:
            logger.error(f"Error getting model comparison data: {str(e)}")
            return []
    
    def get_recent_transcriptions_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get statistics for recent transcriptions."""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            recent_stats = db.session.query(
                Transcription.model_used,
                func.count(Transcription.id).label('count'),
                func.avg(Transcription.wer_score).label('avg_wer'),
                func.avg(Transcription.cer_score).label('avg_cer'),
                func.avg(Transcription.accuracy_score).label('avg_accuracy'),
                func.avg(Transcription.processing_time).label('avg_time')
            ).filter(
                Transcription.created_at >= since_date
            ).group_by(
                Transcription.model_used
            ).all()
            
            stats = {}
            for row in recent_stats:
                stats[row.model_used] = {
                    'count': row.count,
                    'avg_wer': round(float(row.avg_wer or 0), 2),
                    'avg_cer': round(float(row.avg_cer or 0), 2),
                    'avg_accuracy': round(float(row.avg_accuracy or 0), 2),
                    'avg_processing_time': round(float(row.avg_time or 0), 2)
                }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting recent transcription stats: {str(e)}")
            return {}
    
    # User-specific analytics methods for frontend compatibility
    
    def get_user_transcription_count(self, user_id: int) -> int:
        """Get total transcription count for a user (only active, non-deleted)."""
        try:
            return db.session.query(func.count(Transcription.id))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .scalar() or 0
        except Exception as e:
            logger.error(f"Error getting user transcription count: {str(e)}")
            return 0
    
    def get_user_model_usage(self, user_id: int, model_name: str) -> int:
        """Get model usage count for a user (only active, non-deleted, exact model only)."""
        try:
            if model_name == 'whisper':
                # Count ONLY pure 'whisper' transcriptions (not faster-whisper, not both)
                return db.session.query(func.count(Transcription.id))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.model_used == 'whisper',
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar() or 0
            elif model_name == 'wav2vec2':
                # Count ONLY pure 'wav2vec2' transcriptions (not both)
                return db.session.query(func.count(Transcription.id))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.model_used == 'wav2vec2',
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar() or 0
            else:
                return db.session.query(func.count(Transcription.id))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.model_used == model_name,
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar() or 0
        except Exception as e:
            logger.error(f"Error getting user model usage: {str(e)}")
            return 0
    
    def get_user_comparison_count(self, user_id: int) -> int:
        """Get comparison count for a user (only active, non-deleted comparisons)."""
        try:
            # Count transcriptions with model_used = 'both' (direct model comparisons)
            comparison_count = db.session.query(func.count(Transcription.id))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.model_used == 'both',
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .scalar() or 0
            
            return comparison_count
        except Exception as e:
            logger.error(f"Error getting user comparison count: {str(e)}")
            return 0
    
    def get_user_avg_accuracy(self, user_id: int) -> float:
        """Get average accuracy for a user."""
        try:
            # Get average of both whisper and wav2vec accuracies for the user (only active, non-deleted)
            whisper_avg = db.session.query(func.avg(Transcription.whisper_accuracy))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.whisper_accuracy.isnot(None),
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .scalar() or 0
            
            wav2vec_avg = db.session.query(func.avg(Transcription.wav2vec_accuracy))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.wav2vec_accuracy.isnot(None),
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .scalar() or 0
            
            # Calculate overall average
            if whisper_avg > 0 and wav2vec_avg > 0:
                avg_accuracy = (whisper_avg + wav2vec_avg) / 2
            elif whisper_avg > 0:
                avg_accuracy = whisper_avg
            elif wav2vec_avg > 0:
                avg_accuracy = wav2vec_avg
            else:
                avg_accuracy = 0
            
            return round(float(avg_accuracy), 2)
        except Exception as e:
            logger.error(f"Error getting user average accuracy: {str(e)}")
            return 0.0
    
    def get_user_avg_processing_time(self, user_id: int) -> float:
        """Get average processing time for a user."""
        try:
            # Get average of both whisper and wav2vec processing times for the user (only active, non-deleted)
            whisper_avg = db.session.query(func.avg(Transcription.whisper_processing_time))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.whisper_processing_time.isnot(None),
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .scalar() or 0
            
            wav2vec_avg = db.session.query(func.avg(Transcription.wav2vec_processing_time))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.wav2vec_processing_time.isnot(None),
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .scalar() or 0
            
            # Calculate overall average
            if whisper_avg > 0 and wav2vec_avg > 0:
                avg_time = (whisper_avg + wav2vec_avg) / 2
            elif whisper_avg > 0:
                avg_time = whisper_avg
            elif wav2vec_avg > 0:
                avg_time = wav2vec_avg
            else:
                avg_time = 0
            
            return round(float(avg_time), 2)
        except Exception as e:
            logger.error(f"Error getting user average processing time: {str(e)}")
            return 0.0
    
    def get_user_best_accuracy(self, user_id: int) -> float:
        """Get best accuracy score for a user."""
        try:
            # Get best accuracy from both whisper and wav2vec (only active, non-deleted)
            whisper_best = db.session.query(func.max(Transcription.whisper_accuracy))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.whisper_accuracy.isnot(None),
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .scalar() or 0
            
            wav2vec_best = db.session.query(func.max(Transcription.wav2vec_accuracy))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.wav2vec_accuracy.isnot(None),
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .scalar() or 0
            
            best_accuracy = max(whisper_best, wav2vec_best)
            return round(float(best_accuracy), 2)
        except Exception as e:
            logger.error(f"Error getting user best accuracy: {str(e)}")
            return 0.0
    
    def get_user_recent_transcriptions(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get recent transcriptions for a user (only active, non-deleted)."""
        try:
            recent = db.session.query(Transcription)\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .order_by(Transcription.created_at.desc())\
                .limit(limit)\
                .all()
            
            return [
                {
                    'id': t.id,
                    'model_used': t.model_used,
                    'whisper_accuracy': t.whisper_accuracy,
                    'wav2vec_accuracy': t.wav2vec_accuracy,
                    'whisper_wer': t.whisper_wer,
                    'wav2vec_wer': t.wav2vec_wer,
                    'whisper_processing_time': t.whisper_processing_time,
                    'wav2vec_processing_time': t.wav2vec_processing_time,
                    'created_at': t.created_at.isoformat() if t.created_at else None
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
            for i in range(7):
                date = datetime.utcnow() - timedelta(days=i)
                start_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_day = start_day + timedelta(days=1)
                
                count = db.session.query(func.count(Transcription.id))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.created_at >= start_day,
                            Transcription.created_at < end_day,
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar() or 0
                
                result.append({
                    'date': start_day.strftime('%Y-%m-%d'),
                    'count': count
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting user weekly activity: {str(e)}")
            return []
    
    def get_user_preferred_model(self, user_id: int) -> str:
        """Get most used model by a user."""
        try:
            # First check if user has any transcriptions
            total_transcriptions = self.get_user_transcription_count(user_id)
            if total_transcriptions == 0:
                return ""  # No model preference for users with no transcriptions
            
            model_counts = db.session.query(
                Transcription.model_used,
                func.count(Transcription.id).label('count')
            )\
            .filter(
                and_(
                    Transcription.user_id == user_id,
                    Transcription.is_active == True,
                    Transcription.is_deleted == False
                )
            )\
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
                    return 'Σύγκριση Μοντέλων'
                else:
                    return 'Whisper-Large-3'  # Default fallback
            return ""  # No model preference if no transcriptions
        except Exception as e:
            logger.error(f"Error getting user preferred model: {str(e)}")
            return ""
    
    def get_user_most_used_format(self, user_id: int) -> str:
        """Get most used audio format by a user (only active, non-deleted)."""
        try:
            # Join with audio files to get format info
            format_count = db.session.query(AudioFile.format)\
                .join(Transcription, AudioFile.id == Transcription.audio_file_id)\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .group_by(AudioFile.format)\
                .order_by(func.count(AudioFile.format).desc())\
                .first()
            
            return format_count[0] if format_count else 'wav'
        except Exception as e:
            logger.error(f"Error getting user most used format: {str(e)}")
            return 'wav'
    
    def get_user_avg_file_size(self, user_id: int) -> float:
        """Get average file size for a user (only active, non-deleted)."""
        try:
            avg_size = db.session.query(func.avg(AudioFile.file_size))\
                .join(Transcription, AudioFile.id == Transcription.audio_file_id)\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .scalar()
            
            return round(float(avg_size or 0) / 1024 / 1024, 2)  # Convert to MB
        except Exception as e:
            logger.error(f"Error getting user average file size: {str(e)}")
            return 0.0
    
    def get_user_insights_count(self, user_id: int) -> int:
        """Get number of insights generated for a user."""
        # Return comparison count as insights (academic approach)
        return self.get_user_comparison_count(user_id)
    
    def get_user_model_usage_by_date(self, user_id: int, model_name: str, date_str: str) -> int:
        """Get model usage count for a user on a specific date (only active, non-deleted)."""
        try:
            from datetime import datetime, timedelta
            # Parse date and get date range
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = start_datetime + timedelta(days=1)
            
            if model_name == 'whisper':
                # Count ONLY pure 'whisper' transcriptions (not faster-whisper, not both)
                return db.session.query(func.count(Transcription.id))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.model_used == 'whisper',
                            Transcription.is_active == True,
                            Transcription.is_deleted == False,
                            Transcription.created_at >= start_datetime,
                            Transcription.created_at < end_datetime
                        )
                    )\
                    .scalar() or 0
            elif model_name == 'wav2vec2':
                # Count ONLY pure 'wav2vec2' transcriptions
                return db.session.query(func.count(Transcription.id))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.model_used == 'wav2vec2',
                            Transcription.is_active == True,
                            Transcription.is_deleted == False,
                            Transcription.created_at >= start_datetime,
                            Transcription.created_at < end_datetime
                        )
                    )\
                    .scalar() or 0
            elif model_name == 'both':
                # Count ONLY comparison transcriptions
                return db.session.query(func.count(Transcription.id))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.model_used == 'both',
                            Transcription.is_active == True,
                            Transcription.is_deleted == False,
                            Transcription.created_at >= start_datetime,
                            Transcription.created_at < end_datetime
                        )
                    )\
                    .scalar() or 0
            else:
                return 0
        except Exception as e:
            logger.error(f"Error getting user model usage by date: {str(e)}")
            return 0
    
    def get_user_successful_transcriptions(self, user_id: int, model_name: str) -> int:
        """Get count of successful transcriptions for a user and model (those with actual text content)."""
        try:
            if model_name == 'whisper':
                # Count whisper transcriptions that have actual content (successful)
                return db.session.query(func.count(Transcription.id))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.model_used == 'whisper',
                            Transcription.is_active == True,
                            Transcription.is_deleted == False,
                            Transcription.text.isnot(None),
                            Transcription.text != ''
                        )
                    )\
                    .scalar() or 0
            elif model_name == 'wav2vec2':
                # Count wav2vec2 transcriptions that have actual content (successful)
                return db.session.query(func.count(Transcription.id))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.model_used == 'wav2vec2',
                            Transcription.is_active == True,
                            Transcription.is_deleted == False,
                            Transcription.text.isnot(None),
                            Transcription.text != ''
                        )
                    )\
                    .scalar() or 0
            else:
                return 0
        except Exception as e:
            logger.error(f"Error getting user successful transcriptions: {str(e)}")
            return 0
    
    def get_user_system_analytics(self, user_id: int, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get system analytics for a specific user (thesis focus on individual data)."""
        try:
            # Get user-specific data that looks like system data
            user_transcriptions = self.get_user_transcription_count(user_id)
            user_whisper_count = self.get_user_model_usage(user_id, 'whisper')
            user_wav2vec_count = self.get_user_model_usage(user_id, 'wav2vec2')
            user_comparisons = self.get_user_comparison_count(user_id)
            
            # Calculate evaluated transcriptions count (those with accuracy scores, only active/non-deleted)
            evaluated_count = db.session.query(func.count(Transcription.id))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.is_active == True,
                        Transcription.is_deleted == False,
                        or_(
                            Transcription.whisper_accuracy.isnot(None),
                            Transcription.wav2vec_accuracy.isnot(None)
                        )
                    )
                )\
                .scalar() or 0
            
            # Get model-specific metrics for the user
            whisper_accuracy = self.get_user_model_avg_accuracy(user_id, 'whisper')
            wav2vec_accuracy = self.get_user_model_avg_accuracy(user_id, 'wav2vec2')
            whisper_wer = self.get_user_model_avg_wer(user_id, 'whisper')
            wav2vec_wer = self.get_user_model_avg_wer(user_id, 'wav2vec2')
            whisper_time = self.get_user_model_avg_processing_time(user_id, 'whisper')
            wav2vec_time = self.get_user_model_avg_processing_time(user_id, 'wav2vec2')
            
            # Calculate overall averages
            overall_accuracy = self.get_user_avg_accuracy(user_id)
            overall_wer = self.get_user_avg_wer(user_id)
            overall_time = self.get_user_avg_processing_time(user_id)
            
            # Calculate derived metrics
            whisper_speed_score = max(0, 100 - (whisper_time * 2)) if whisper_time > 0 else 0  # Less harsh penalty
            wav2vec_speed_score = max(0, 100 - (wav2vec_time * 2)) if wav2vec_time > 0 else 0  # Less harsh penalty
            
            # Better accuracy from WER calculation (NO DEFAULTS - REAL DATA ONLY)
            if whisper_wer > 0:
                whisper_accuracy_from_wer = max(0, 100 - whisper_wer)
            elif whisper_accuracy > 0:
                whisper_accuracy_from_wer = whisper_accuracy
            else:
                whisper_accuracy_from_wer = 0.0  # No data = 0, no fake defaults
                
            if wav2vec_wer > 0:
                wav2vec_accuracy_from_wer = max(0, 100 - wav2vec_wer)
            elif wav2vec_accuracy > 0:
                wav2vec_accuracy_from_wer = wav2vec_accuracy
            else:
                wav2vec_accuracy_from_wer = 0.0  # No data = 0, no fake defaults
                
            # Calculate actual usage scores from corrected counts
            whisper_usage_score = min(100, (user_whisper_count / max(1, user_transcriptions)) * 100)
            wav2vec_usage_score = min(100, (user_wav2vec_count / max(1, user_transcriptions)) * 100)
            
            # Success rates based on actual data (successful transcriptions / total attempts)
            # Get successful transcription counts (those with actual results)
            whisper_successful = self.get_user_successful_transcriptions(user_id, 'whisper')
            wav2vec_successful = self.get_user_successful_transcriptions(user_id, 'wav2vec2')
            
            # Calculate real success rates
            whisper_success_rate = (whisper_successful / max(1, user_whisper_count)) * 100 if user_whisper_count > 0 else 0
            wav2vec_success_rate = (wav2vec_successful / max(1, user_wav2vec_count)) * 100 if user_wav2vec_count > 0 else 0
            
            # Use ONLY real data - NO ESTIMATES OR DEFAULTS
            # If no accuracy data exists, show 0 (thesis requirement: no fake data)
            # whisper_accuracy and wav2vec_accuracy remain as-is from database
            # whisper_wer and wav2vec_wer remain as-is from database
            
            # Realtime factor calculation
            realtime_factor = overall_time / 60.0 if overall_time > 0 else 0  # Rough estimation
            
            # Comparison percentage
            comparison_percentage = (user_comparisons / max(1, user_transcriptions)) * 100 if user_transcriptions > 0 else 0
            
            # Real time series data for the last 7 days (NO MOCK DATA)
            time_series_data = self.get_user_weekly_activity(user_id)
            for entry in time_series_data:
                # Get actual model usage for this date (NO ASSUMPTIONS)
                date_str = entry['date']
                entry['whisperCount'] = self.get_user_model_usage_by_date(user_id, 'whisper', date_str)
                entry['wav2vecCount'] = self.get_user_model_usage_by_date(user_id, 'wav2vec2', date_str)
                entry['comparisonCount'] = self.get_user_model_usage_by_date(user_id, 'both', date_str)
            
            # Greek language metrics removed for thesis simplification
            
            return {
                'totalTranscriptions': user_transcriptions,
                'whisperTranscriptions': user_whisper_count,
                'wav2vecTranscriptions': user_wav2vec_count,
                'totalComparisons': user_comparisons,
                'evaluatedTranscriptionsCount': evaluated_count,
                
                # Model-specific metrics
                'whisperAccuracy': whisper_accuracy,
                'wav2vecAccuracy': wav2vec_accuracy,
                'whisperWER': whisper_wer,
                'wav2vecWER': wav2vec_wer,
                'whisperProcessingTime': whisper_time,
                'wav2vecProcessingTime': wav2vec_time,
                'whisperSuccessRate': whisper_success_rate,
                'wav2vecSuccessRate': wav2vec_success_rate,
                
                # Calculated chart metrics
                'whisperSpeedScore': whisper_speed_score,
                'wav2vecSpeedScore': wav2vec_speed_score,
                'whisperAccuracyFromWER': whisper_accuracy_from_wer,
                'wav2vecAccuracyFromWER': wav2vec_accuracy_from_wer,
                'whisperUsageScore': whisper_usage_score,
                'wav2vecUsageScore': wav2vec_usage_score,
                
                # System-wide computed metrics
                'averageAccuracy': overall_accuracy,
                'averageWER': overall_wer,
                'averageProcessingTime': overall_time,
                'realtimeFactor': realtime_factor,
                'comparisonPercentage': comparison_percentage,
                
                # Time series data  
                'timeSeriesData': time_series_data
            }
        except Exception as e:
            logger.error(f"Error getting user system analytics: {str(e)}")
            return {
                'totalTranscriptions': 0,
                'whisperTranscriptions': 0,
                'wav2vecTranscriptions': 0,
                'totalComparisons': 0,
                'evaluatedTranscriptionsCount': 0,
                'whisperAccuracy': 0,
                'wav2vecAccuracy': 0,
                'whisperWER': 0,
                'wav2vecWER': 0,
                'whisperProcessingTime': 0,
                'wav2vecProcessingTime': 0,
                'whisperSuccessRate': 0,
                'wav2vecSuccessRate': 0,
                'whisperSpeedScore': 0,
                'wav2vecSpeedScore': 0,
                'whisperAccuracyFromWER': 0,
                'wav2vecAccuracyFromWER': 0,
                'whisperUsageScore': 0,
                'wav2vecUsageScore': 0,
                'averageAccuracy': 0,
                'averageWER': 0,
                'averageProcessingTime': 0,
                'realtimeFactor': 0,
                'comparisonPercentage': 0,
                'timeSeriesData': []
            }
    
    def get_user_model_avg_accuracy(self, user_id: int, model_name: str) -> float:
        """Get average accuracy for a user's specific model (only active, non-deleted)."""
        try:
            if model_name == 'whisper':
                # Get accuracy from transcriptions where model_used = 'whisper' OR 'both' (for whisper part)
                avg_accuracy = db.session.query(func.avg(Transcription.whisper_accuracy))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.whisper_accuracy.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False,
                            Transcription.model_used.in_(['whisper', 'both'])
                        )
                    )\
                    .scalar()
            elif model_name == 'wav2vec2':
                # Get accuracy from transcriptions where model_used = 'wav2vec2' OR 'both' (for wav2vec part)
                avg_accuracy = db.session.query(func.avg(Transcription.wav2vec_accuracy))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.wav2vec_accuracy.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False,
                            Transcription.model_used.in_(['wav2vec2', 'both'])
                        )
                    )\
                    .scalar()
            else:
                avg_accuracy = 0
            
            return round(float(avg_accuracy or 0), 2)
        except Exception as e:
            logger.error(f"Error getting user model average accuracy: {str(e)}")
            return 0.0
    
    def get_user_model_avg_wer(self, user_id: int, model_name: str) -> float:
        """Get average WER for a user's specific model."""
        try:
            if model_name == 'whisper':
                avg_wer = db.session.query(func.avg(Transcription.whisper_wer))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.whisper_wer.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar()
            elif model_name == 'wav2vec2':
                avg_wer = db.session.query(func.avg(Transcription.wav2vec_wer))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.wav2vec_wer.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar()
            else:
                avg_wer = 0
            
            return round(float(avg_wer or 0), 2)
        except Exception as e:
            logger.error(f"Error getting user model average WER: {str(e)}")
            return 0.0
    
    def get_user_model_avg_processing_time(self, user_id: int, model_name: str) -> float:
        """Get average processing time for a user's specific model."""
        try:
            if model_name == 'whisper':
                avg_time = db.session.query(func.avg(Transcription.whisper_processing_time))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.whisper_processing_time.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar()
            elif model_name == 'wav2vec2':
                avg_time = db.session.query(func.avg(Transcription.wav2vec_processing_time))\
                    .filter(
                        and_(
                            Transcription.user_id == user_id,
                            Transcription.wav2vec_processing_time.isnot(None),
                            Transcription.is_active == True,
                            Transcription.is_deleted == False
                        )
                    )\
                    .scalar()
            else:
                avg_time = 0
            
            return round(float(avg_time or 0), 2)
        except Exception as e:
            logger.error(f"Error getting user model average processing time: {str(e)}")
            return 0.0
    
    def get_user_avg_wer(self, user_id: int) -> float:
        """Get average WER for a user across all models."""
        try:
            # Get average of both whisper and wav2vec WER for the user (only active, non-deleted)
            whisper_wer = db.session.query(func.avg(Transcription.whisper_wer))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.whisper_wer.isnot(None),
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .scalar() or 0
            
            wav2vec_wer = db.session.query(func.avg(Transcription.wav2vec_wer))\
                .filter(
                    and_(
                        Transcription.user_id == user_id,
                        Transcription.wav2vec_wer.isnot(None),
                        Transcription.is_active == True,
                        Transcription.is_deleted == False
                    )
                )\
                .scalar() or 0
            
            # Calculate overall average
            if whisper_wer > 0 and wav2vec_wer > 0:
                avg_wer = (whisper_wer + wav2vec_wer) / 2
            elif whisper_wer > 0:
                avg_wer = whisper_wer
            elif wav2vec_wer > 0:
                avg_wer = wav2vec_wer
            else:
                avg_wer = 0
            
            return round(float(avg_wer), 2)
        except Exception as e:
            logger.error(f"Error getting user average WER: {str(e)}")
            return 0.0
    


# Global instance
research_analytics_service = ResearchAnalyticsService()

# Legacy alias for compatibility
AnalyticsService = ResearchAnalyticsService