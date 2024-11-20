from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload
from .base_service import BaseService, handle_db_operation
from ..models.table import Table, TableStatus
from ..models.reservation import Reservation, ReservationStatus
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

    @handle_db_operation("get_available_tables")
    def get_available_tables(
        self,
        session: Session,
        reservation_time: datetime,
        duration: int,
        party_size: int,
        max_tables: int = 3,
    ) -> List[List[Table]]:
        """Get possible table combinations for a reservation"""
        try:
            # Get tables that could accommodate the party size divided by max tables
            suitable_tables = (
                session.query(self.model)
                .filter(
                    self.model.status.in_(
                        [TableStatus.AVAILABLE, TableStatus.RESERVED]
                    ),
                    self.model.capacity
                    >= party_size / max_tables,  # Minimum size per table
                )
                .order_by(self.model.capacity)
                .all()
            )

            if not suitable_tables:
                return []

            end_time = reservation_time + timedelta(minutes=duration)

            # Get conflicting reservations
            conflicts = self._get_table_conflicts(
                session, suitable_tables, reservation_time, end_time
            )

            # Remove tables with conflicts
            conflict_table_ids = {table.id for table, _ in conflicts}
            available_tables = [
                t for t in suitable_tables if t.id not in conflict_table_ids
            ]

            if not available_tables:
                return []

            # Find valid table combinations
            valid_combinations = []
            self._find_table_combinations(
                available_tables, party_size, [], valid_combinations, max_tables
            )

            # Sort combinations by efficiency (minimize wasted seats)
            return sorted(
                valid_combinations,
                key=lambda tables: abs(sum(t.capacity for t in tables) - party_size),
            )

        except Exception as e:
            logger.error(f"Error getting available tables: {e}")
            raise

    def _get_table_conflicts(
        self,
        session: Session,
        tables: List[Table],
        start_time: datetime,
        end_time: datetime,
    ) -> List[tuple[Table, List[Reservation]]]:
        """
        Check for conflicts with existing reservations for given tables
        Returns a list of (table, conflicting_reservations) tuples
        """
        conflicts = []
        table_ids = [table.id for table in tables]

        # Get all potentially conflicting reservations
        query = (
            session.query(Reservation)
            .join(Reservation.tables)
            .options(joinedload(Reservation.tables))
            .filter(
                Table.id.in_(table_ids),
                Reservation.status.in_(
                    [ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN]
                ),
            )
        )

        # Get all reservations that might conflict
        reservations = query.all()
        conflicting_reservations = []

        # Check each reservation's time range
        for reservation in reservations:
            reservation_end = reservation.reservation_datetime + timedelta(
                minutes=reservation.duration
            )
            if (
                reservation.reservation_datetime < end_time
                and reservation_end > start_time
            ):
                conflicting_reservations.append(reservation)

        if conflicting_reservations:
            # Group conflicts by table
            table_conflicts = {}
            for reservation in conflicting_reservations:
                for table in reservation.tables:
                    if table.id in table_ids:
                        if table.id not in table_conflicts:
                            table_conflicts[table.id] = []
                        table_conflicts[table.id].append(reservation)

            # Build conflict list
            for table in tables:
                if table.id in table_conflicts:
                    conflicts.append((table, table_conflicts[table.id]))

        return conflicts

    def _find_table_combinations(
        self,
        available_tables: List[Table],
        required_capacity: int,
        current_combination: List[Table],
        valid_combinations: List[List[Table]],
        max_tables: int,
    ) -> None:
        """Recursively find valid table combinations"""
        current_capacity = sum(table.capacity for table in current_combination)

        # Check if current combination is valid
        if current_capacity >= required_capacity:
            valid_combinations.append(current_combination[:])
            return

        # Stop if we've reached max tables
        if len(current_combination) >= max_tables:
            return

        # Try adding each remaining table
        for i, table in enumerate(available_tables):
            # Skip if this table would exceed required capacity by too much
            if current_capacity + table.capacity > required_capacity * 1.5:
                continue

            new_combination = current_combination + [table]
            self._find_table_combinations(
                available_tables[i + 1 :],
                required_capacity,
                new_combination,
                valid_combinations,
                max_tables,
            )

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
