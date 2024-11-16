import logging
from datetime import datetime
from typing import List, Optional, Dict
from .base_controller import BaseController, ServiceOperation
from ..models.table import Table, TableStatus
from ..services.service_manager import ServiceManager

logger = logging.getLogger(__name__)


class TableController(BaseController):
    """Controller for table-related operations"""

    def get_all_tables(self) -> List[Table]:
        """Get all tables"""
        operation: ServiceOperation[List[Table]] = (
            lambda services: services.table_service.get_all()
        )
        return self.handle_operation(operation)

    def get_available_tables(self, datetime: datetime, party_size: int) -> List[Table]:
        """Get available tables for a specific time and party size"""
        operation: ServiceOperation[List[Table]] = (
            lambda services: services.table_service.get_available_tables(
                datetime, party_size
            )
        )
        return self.handle_operation(operation)

    def update_table_status(
        self, table_number: int, new_status: TableStatus
    ) -> Optional[Table]:
        """Update table status"""
        operation: ServiceOperation[Optional[Table]] = (
            lambda services: services.table_service.update_status(
                table_number, new_status
            )
        )
        return self.handle_operation(operation)

    def get_table_status_counts(self) -> Dict[TableStatus, int]:
        """Get count of tables in each status"""
        operation: ServiceOperation[Dict[TableStatus, int]] = lambda services: {
            status: sum(
                1
                for table in services.table_service.get_all()
                if table.status == status
            )
            for status in TableStatus
        }
        return self.handle_operation(operation)

    def create_table(
        self,
        number: int,
        capacity: int,
        location: str,
        status: TableStatus = TableStatus.AVAILABLE,
    ) -> Optional[Table]:
        """Create a new table"""
        operation: ServiceOperation[Optional[Table]] = (
            lambda services: services.table_service.create(
                Table(
                    number=number, capacity=capacity, location=location, status=status
                )
            )
        )
        return self.handle_operation(operation)

    def update_table(
        self,
        table_id: int,
        number: int,
        capacity: int,
        location: str,
        status: TableStatus,
    ) -> Optional[Table]:
        """Update an existing table"""

        def update_op(services: ServiceManager) -> Optional[Table]:
            table = services.table_service.get_by_id(table_id)
            if table:
                table.number = number
                table.capacity = capacity
                table.location = location
                table.status = status
                return services.table_service.update(table)
            return None

        operation: ServiceOperation[Optional[Table]] = update_op
        return self.handle_operation(operation)

    def delete_table(self, table_id: int) -> Optional[Table]:
        """Delete a table"""
        operation: ServiceOperation[Optional[Table]] = (
            lambda services: services.table_service.delete(table_id)
        )
        return self.handle_operation(operation)
