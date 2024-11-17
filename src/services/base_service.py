import logging
from functools import wraps
from contextlib import contextmanager
from typing import TypeVar, Generic, Type, List, Optional, Callable
from sqlalchemy.orm import Session, scoped_session

logger = logging.getLogger(__name__)

T = TypeVar("T")


def handle_db_operation(operation_name: str):
    """Decorator for handling database operations with logging and error handling"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                with self.session_scope() as session:
                    result = func(self, session, *args, **kwargs)
                    return result
            except Exception as e:
                logger.error(f"Error in {operation_name}: {str(e)}")
                raise

        return wrapper

    return decorator


class BaseService(Generic[T]):
    """
    Simplified base service with automatic session management and error handling
    """

    def __init__(self, model: Type[T], session_factory: scoped_session):
        self.model = model
        self._session_factory = session_factory

    @property
    def session(self) -> Session:
        """Get a new session"""
        return self._session_factory()

    @contextmanager
    def session_scope(self):
        """Context manager for database operations"""
        session = self.session
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @handle_db_operation("get_all")
    def get_all(self, session: Session) -> List[T]:
        return session.query(self.model).all()

    @handle_db_operation("get_by_id")
    def get_by_id(self, session: Session, id: int) -> Optional[T]:
        return session.query(self.model).get(id)

    @handle_db_operation("create")
    def create(self, session: Session, **kwargs) -> T:
        obj = self.model(**kwargs)
        session.add(obj)
        session.flush()
        return obj

    @handle_db_operation("update")
    def update(self, session: Session, id: int, **kwargs) -> Optional[T]:
        obj = session.query(self.model).get(id)
        if obj:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            session.flush()
        return obj

    @handle_db_operation("delete")
    def delete(self, session: Session, id: int) -> bool:
        obj = session.query(self.model).get(id)
        if obj:
            session.delete(obj)
            return True
        return False

    @handle_db_operation("bulk_create")
    def bulk_create(self, session: Session, items: List[dict]) -> List[T]:
        objects = [self.model(**item) for item in items]
        session.bulk_save_objects(objects)
        return objects

    @handle_db_operation("bulk_update")
    def bulk_update(self, session: Session, items: List[tuple[int, dict]]) -> int:
        updated = 0
        for id, data in items:
            obj = session.query(self.model).get(id)
            if obj:
                for key, value in data.items():
                    setattr(obj, key, value)
                updated += 1
        return updated
