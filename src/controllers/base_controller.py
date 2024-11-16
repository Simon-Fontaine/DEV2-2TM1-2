from typing import Optional, Callable, TypeVar
from ..services.service_manager import ServiceManager
import logging

logger = logging.getLogger(__name__)

# Define a type variable for the return type of operations
T = TypeVar("T")

# Type alias for service operations
ServiceOperation = Callable[[ServiceManager], T]


class BaseController:
    """Base controller class for handling service interactions"""

    def __init__(self):
        self._service_manager: Optional[ServiceManager] = None

    @property
    def service_manager(self) -> ServiceManager:
        if not self._service_manager:
            self._service_manager = ServiceManager()
        return self._service_manager

    def handle_operation(self, operation: ServiceOperation[T]) -> T:
        """Execute an operation within a service manager context"""
        try:
            with self.service_manager as services:
                result = operation(services)
                if hasattr(result, "__iter__") and not isinstance(result, (str, bytes)):
                    # For collections, convert to list to ensure all lazy-loaded attributes are loaded
                    return [item for item in result]
                return result
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}")
            raise
