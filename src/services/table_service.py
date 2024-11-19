from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from .base_service import BaseService, handle_db_operation
from ..models.table import Table, TableStatus
from ..models.reservation import ReservationStatus
from ..models.order import OrderStatus
import logging

logger = logging.getLogger(__name__)


class TableService(BaseService[Table]):
    """Service for managing tables"""

    @handle_db_operation("get_by_number")
    def get_by_number(self, session: Session, number: int) -> Optional[Table]:
        """Get table by its number"""
        return session.query(self.model).filter(self.model.number == number).first()

    @handle_db_operation("get_tables_by_capacity")
    def get_tables_by_capacity(
        self, session: Session, min_capacity: int, max_capacity: Optional[int] = None
    ) -> List[Table]:
        """Get available tables by capacity range"""
        query = session.query(self.model).filter(
            and_(
                self.model.capacity >= min_capacity,
                self.model.status == TableStatus.AVAILABLE,
            )
        )

        if max_capacity:
            query = query.filter(self.model.capacity <= max_capacity)

        return query.order_by(self.model.capacity).all()

    @handle_db_operation("get_available_for_reservation")  # New method for reservations
    def get_available_for_reservation(
        self,
        session: Session,
        reservation_time: datetime,
        duration: int,
        party_size: int,
    ) -> List[Table]:
        """Get tables available for a reservation at a specific time"""
        try:
            end_time = reservation_time + timedelta(minutes=duration)

            # Get tables that can accommodate the party size
            suitable_tables = (
                session.query(self.model)
                .filter(
                    and_(
                        self.model.capacity >= party_size,
                        self.model.status.in_(
                            [
                                TableStatus.AVAILABLE,
                                TableStatus.RESERVED,  # Include reserved tables to check conflicts
                            ]
                        ),
                    )
                )
                .all()
            )

            if not suitable_tables:
                return []

            # Filter out tables with conflicting reservations
            available_tables = []
            for table in suitable_tables:
                conflicts = False
                for reservation in table.reservations:
                    if reservation.status not in [
                        ReservationStatus.CONFIRMED,
                        ReservationStatus.CHECKED_IN,
                    ]:
                        continue

                    res_end = reservation.get_end_time()
                    if (
                        reservation.reservation_datetime < end_time
                        and reservation_time < res_end
                    ):
                        conflicts = True
                        break

                if not conflicts:
                    available_tables.append(table)

            # Sort by capacity to minimize wasted seats
            return sorted(available_tables, key=lambda t: t.capacity)

        except Exception as e:
            logger.error(f"Error getting available tables: {e}")
            raise

    @handle_db_operation("update_status")
    def update_status(
        self, session: Session, table_id: int, new_status: TableStatus
    ) -> Optional[Table]:
        """Update table status with validation"""
        table = session.query(self.model).get(table_id)
        if not table:
            return None

        active_orders = [
            o
            for o in table.orders
            if o.status not in [OrderStatus.PAID, OrderStatus.CANCELLED]
        ]
        if active_orders:
            raise ValueError("Cannot change table status while orders are active")

        table.status = new_status
        return table

    @handle_db_operation("move_table")
    def move_table(
        self, session: Session, table_id: int, new_x: int, new_y: int
    ) -> bool:
        """Move a table to a new grid position"""
        table = session.query(self.model).get(table_id)
        if not table:
            raise ValueError("Table not found")

        # Check if position is occupied
        existing = (
            session.query(self.model)
            .filter(
                self.model.grid_x == new_x,
                self.model.grid_y == new_y,
                self.model.id != table_id,
            )
            .first()
        )

        if existing:
            raise ValueError("Position already occupied")

        table.grid_x = new_x
        table.grid_y = new_y
        return True

    @handle_db_operation("get_table_utilization")
    def get_table_utilization(self, session: Session) -> dict:
        """Get table utilization stats"""
        tables = session.query(self.model).all()
        total = len(tables)
        if total == 0:
            return {"total": 0}

        stats = {
            "total": total,
            "available": sum(1 for t in tables if t.status == TableStatus.AVAILABLE),
            "occupied": sum(1 for t in tables if t.status == TableStatus.OCCUPIED),
            "reserved": sum(1 for t in tables if t.status == TableStatus.RESERVED),
            "maintenance": sum(
                1 for t in tables if t.status == TableStatus.MAINTENANCE
            ),
            "cleaning": sum(1 for t in tables if t.status == TableStatus.CLEANING),
        }

        return stats
