import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import TypeVar, Generic, Type, Optional, List

from ..models.base import Base

logger = logging.getLogger(__name__)

# Generic type for SQLAlchemy models
T = TypeVar("T", bound=Base)


class BaseService(Generic[T]):
    """Base service class with common CRUD operations"""

    def __init__(self, db_session: Session, model: Type[T]):
        self.__db = db_session
        self.__model = model

    @property
    def db(self) -> Session:
        return self.__db

    @property
    def model(self) -> Type[T]:
        return self.__model

    def get_by_id(self, id: int) -> Optional[T]:
        """Retrieve an entity by its ID"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            logger.error(
                f"Error retrieving {self.model.__name__} with id {id}: {str(e)}"
            )
            raise

    def get_all(self) -> List[T]:
        """Retrieve all entities"""
        try:
            return self.db.query(self.model).all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving all {self.model.__name__}s: {str(e)}")
            raise

    def create(self, obj: T) -> T:
        """Create a new entity"""
        try:
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise

    def update(self, obj: T) -> T:
        """Update an existing entity"""
        try:
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating {self.model.__name__}: {str(e)}")
            raise

    def delete(self, id: int) -> bool:
        """Delete an entity by ID"""
        try:
            obj = self.get_by_id(id)
            if obj:
                self.db.delete(obj)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting {self.model.__name__} with id {id}: {str(e)}")
            raise
