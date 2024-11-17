import logging
from typing import TypeVar, Generic, Type, List, Optional
from sqlalchemy.orm import Session, scoped_session
from contextlib import contextmanager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Service(Generic[T]):
    """
    Universal service class that handles database operations with built-in session management.
    """

    def __init__(self, model: Type[T], session_factory):
        self.model = model
        self._session_factory = scoped_session(session_factory)

    def get_session(self) -> Session:
        """Get a new session"""
        return self._session_factory()

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database operation failed: {str(e)}")
            raise
        finally:
            session.close()

    def get_all(self) -> List[T]:
        """Get all records"""
        with self.session_scope() as session:
            return [
                self._clone_object(obj, session)
                for obj in session.query(self.model).all()
            ]

    def get_by_id(self, id: int) -> Optional[T]:
        """Get record by ID"""
        with self.session_scope() as session:
            obj = session.query(self.model).filter(self.model.id == id).first()
            return self._clone_object(obj, session) if obj else None

    def create(self, **kwargs) -> T:
        """Create a new record"""
        with self.session_scope() as session:
            obj = self.model(**kwargs)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return self._clone_object(obj, session)

    def update(self, id: int, **kwargs) -> Optional[T]:
        """Update a record"""
        with self.session_scope() as session:
            obj = session.query(self.model).filter(self.model.id == id).first()
            if obj:
                for key, value in kwargs.items():
                    setattr(obj, key, value)
                session.commit()
                session.refresh(obj)
                return self._clone_object(obj, session)
            return None

    def delete(self, id: int) -> bool:
        """Delete a record"""
        with self.session_scope() as session:
            obj = session.query(self.model).filter(self.model.id == id).first()
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False

    def _clone_object(self, obj: T, session: Session) -> T:
        """Create a clean copy of an object with a new session"""
        if obj is None:
            return None
        session.expunge_all()
        return obj
