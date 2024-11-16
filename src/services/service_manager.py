import logging
from typing import Optional
from sqlalchemy.orm import Session

from ..models.base import SessionLocal
from .table_service import TableService

logger = logging.getLogger(__name__)


class ServiceManager:
    """Manages all services and database sessions"""

    def __init__(self):
        self.__session: Optional[Session] = None
        self.__table_service: Optional[TableService] = None

    @property
    def session(self) -> Session:
        if self.__session is None:
            raise ValueError("Session not initialized")
        return self.__session

    @session.setter
    def session(self, value: Session):
        self.__session = value

    def __enter__(self):
        self.session = SessionLocal()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is not None:  # An exception occurred
                self.session.rollback()
                logger.error(f"Session rolled back due to error: {exc_val}")
            self.session.close()
            self.session = None

    @property
    def table_service(self) -> TableService:
        if not self.session:
            raise RuntimeError("ServiceManager must be used within a context manager")
        if not self.__table_service:
            self.__table_service = TableService(self.session)
        return self.__table_service
