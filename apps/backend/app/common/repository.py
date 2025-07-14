"""Base repository for data access."""

from typing import Type, List, Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db


class BaseRepository:
    """Base repository with common database operations."""
    
    def __init__(self, model: Type[db.Model]):
        self.model = model
    
    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[db.Model]:
        """Get all records with optional filters."""
        query = self.model.query.filter_by(is_deleted=False)
        
        if filters:
            query = query.filter_by(**filters)
        
        return query.all()
    
    def get_by_id(self, id: int) -> Optional[db.Model]:
        """Get a record by ID."""
        return self.model.query.filter_by(
            id=id,
            is_deleted=False
        ).first()
    
    def create(self, **kwargs) -> db.Model:
        """Create a new record."""
        try:
            instance = self.model(**kwargs)
            db.session.add(instance)
            db.session.commit()
            return instance
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    def update(self, id: int, **kwargs) -> Optional[db.Model]:
        """Update an existing record."""
        try:
            instance = self.get_by_id(id)
            if instance:
                for key, value in kwargs.items():
                    setattr(instance, key, value)
                db.session.commit()
            return instance
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    def delete(self, id: int, soft: bool = True) -> bool:
        """Delete a record (soft delete by default)."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"BaseRepository.delete called with id={id}, soft={soft}")
            instance = self.get_by_id(id)
            if instance:
                logger.info(f"Found instance to delete: {instance}")
                if soft:
                    logger.info("Performing soft delete")
                    instance.soft_delete()
                    logger.info("Soft delete completed")
                else:
                    logger.info("Performing hard delete")
                    db.session.delete(instance)
                    db.session.commit()
                    logger.info("Hard delete completed")
                return True
            else:
                logger.warning(f"Instance with id={id} not found for deletion")
                return False
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError during delete: {str(e)}")
            db.session.rollback()
            raise e
        except Exception as e:
            logger.error(f"Unexpected error during delete: {str(e)}")
            db.session.rollback()
            raise e
    
    def paginate(self, page: int = 1, per_page: int = 20, 
                 filters: Optional[Dict[str, Any]] = None,
                 sort_by: str = 'created_at',
                 sort_order: str = 'desc') -> Dict[str, Any]:
        """Get paginated results."""
        query = self.model.query.filter_by(is_deleted=False)
        
        if filters:
            query = query.filter_by(**filters)
        
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