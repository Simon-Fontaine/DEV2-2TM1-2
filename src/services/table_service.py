from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from itertools import combinations
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from .base_service import BaseService, handle_db_operation
from ..models.table import Table, TableStatus
from ..models.reservation import ReservationStatus
from ..models.order import OrderStatus
import logging

logger = logging.getLogger(__name__)


class TableService(BaseService[Table]):
    """
    Enhanced table service with comprehensive table management functionality
    """

    @handle_db_operation("get_by_number")
    def get_by_number(self, session: Session, number: int) -> Optional[Table]:
        """Get table by its number"""
        return session.query(self.model).filter(self.model.number == number).first()

    @handle_db_operation("create")
    def create(self, session: Session, **kwargs) -> Table:
        """Create a new table with duplicate number check"""
        existing = (
            session.query(self.model)
            .filter(self.model.number == kwargs["number"])
            .first()
        )

        if existing:
            raise ValueError(f"Table number {kwargs['number']} already exists")

        obj = self.model(**kwargs)
        session.add(obj)
        session.flush()
        return obj

    @handle_db_operation("update")
    def update(self, session: Session, id: int, **kwargs) -> Optional[Table]:
        """Update table with duplicate number check"""
        obj = session.query(self.model).get(id)
        if obj:
            # If number is being updated, check for duplicates
            if "number" in kwargs and kwargs["number"] != obj.number:
                existing = (
                    session.query(self.model)
                    .filter(
                        and_(self.model.number == kwargs["number"], self.model.id != id)
                    )
                    .first()
                )

                if existing:
                    raise ValueError(f"Table number {kwargs['number']} already exists")

            # Update table if number is unique or unchanged
            for key, value in kwargs.items():
                setattr(obj, key, value)
            session.flush()
        return obj

    @handle_db_operation("update_status")
    def update_status(
        self, session: Session, table_id: int, new_status: TableStatus
    ) -> Optional[Table]:
        """Update table status with validation"""
        table = session.query(self.model).get(table_id)
        if not table:
            return None

        # Validate status transition
        if new_status == TableStatus.AVAILABLE:
            # Check if there are any truly active orders (not paid or cancelled)
            active_orders = [
                order
                for order in table.orders
                if order.status not in [OrderStatus.PAID, OrderStatus.CANCELLED]
            ]

            if active_orders:
                raise ValueError(
                    "Cannot mark table as available while orders are active"
                )

        table.status = new_status
        return table

    @handle_db_operation("get_available_tables")
    def get_available_tables(
        self,
        session: Session,
        desired_time: datetime,
        party_size: int,
        duration_minutes: int = 120,
    ) -> List[Table]:
        """Get available tables for a specific time and party size"""
        # Calculate the end time of the desired reservation
        end_time = desired_time + timedelta(minutes=duration_minutes)

        # Get all tables that meet capacity requirements
        potential_tables = (
            session.query(self.model)
            .filter(
                and_(
                    self.model.capacity >= party_size,
                    self.model.status != TableStatus.MAINTENANCE,
                )
            )
            .all()
        )

        # Filter out tables with conflicting reservations
        available_tables = []
        for table in potential_tables:
            has_conflict = False
            for reservation in table.reservations:
                if reservation.status == ReservationStatus.CANCELLED:
                    continue

                reservation_end = reservation.reservation_datetime + timedelta(
                    minutes=reservation.duration
                )
                if (
                    reservation.reservation_datetime < end_time
                    and reservation_end > desired_time
                ):
                    has_conflict = True
                    break

            if not has_conflict:
                available_tables.append(table)

        return available_tables

    @handle_db_operation("get_status_counts")
    def get_status_counts(self, session: Session) -> dict:
        """Get count of tables in each status"""
        counts = {}
        for status in TableStatus:
            count = (
                session.query(self.model).filter(self.model.status == status).count()
            )
            counts[status.value] = count
        return counts

    @handle_db_operation("find_tables_for_party")
    def find_tables_for_party(
        self,
        session: Session,
        party_size: int,
        desired_time: datetime,
        duration_minutes: int = 120,
        max_tables: int = 3,
        capacity_buffer: float = 1.5,
    ) -> List[List[Table]]:
        """Find optimal combinations of tables for a party"""
        # Get available tables
        available_tables = self.get_available_tables(
            session, desired_time, 1, duration_minutes
        )

        if not available_tables:
            return []

        # Sort tables by capacity for efficiency
        available_tables.sort(key=lambda t: t.capacity)
        max_total_capacity = int(party_size * capacity_buffer)
        valid_combinations = []

        # First, try to find a single table with optimal capacity
        perfect_tables = [
            t for t in available_tables if party_size <= t.capacity <= party_size * 1.2
        ]
        if perfect_tables:
            return [[perfect_tables[0]]]

        # Try combinations of different sizes
        for num_tables in range(1, min(max_tables + 1, len(available_tables) + 1)):
            for combo in combinations(available_tables, num_tables):
                total_capacity = sum(table.capacity for table in combo)

                if party_size <= total_capacity <= max_total_capacity:
                    # Check table proximity if location is available
                    if all(hasattr(t, "location") for t in combo):
                        # Prioritize tables in the same or adjacent locations
                        locations = set(t.location for t in combo)
                        if len(locations) <= 2:  # Allow at most 2 different locations
                            valid_combinations.append(list(combo))
                    else:
                        valid_combinations.append(list(combo))

            # Stop if we found good enough combinations
            if valid_combinations and num_tables < max_tables:
                best_capacity = min(
                    sum(table.capacity for table in combo)
                    for combo in valid_combinations
                )
                if best_capacity <= party_size * 1.2:
                    break

        # Sort combinations by optimality
        valid_combinations.sort(
            key=lambda tables: (
                len(tables),  # Prefer fewer tables
                abs(
                    sum(t.capacity for t in tables) - party_size
                ),  # Prefer closer capacity match
                len(set(t.location for t in tables)),  # Prefer same location
            )
        )

        return valid_combinations

    @handle_db_operation("get_tables_by_location")
    def get_tables_by_location(self, session: Session, location: str) -> List[Table]:
        """Get all tables in a specific location"""
        return session.query(self.model).filter(self.model.location == location).all()

    @handle_db_operation("get_tables_by_capacity")
    def get_tables_by_capacity(
        self, session: Session, min_capacity: int, max_capacity: Optional[int] = None
    ) -> List[Table]:
        """Get tables within a capacity range"""
        query = session.query(self.model).filter(self.model.capacity >= min_capacity)
        if max_capacity is not None:
            query = query.filter(self.model.capacity <= max_capacity)
        return query.all()

    @handle_db_operation("get_tables_needing_maintenance")
    def get_tables_needing_maintenance(self, session: Session) -> List[Table]:
        """Get all tables marked for maintenance"""
        return (
            session.query(self.model)
            .filter(self.model.status == TableStatus.MAINTENANCE)
            .all()
        )

    @handle_db_operation("bulk_update_status")
    def bulk_update_status(
        self, session: Session, table_ids: List[int], new_status: TableStatus
    ) -> int:
        """Update status for multiple tables at once"""
        result = (
            session.query(self.model)
            .filter(self.model.id.in_(table_ids))
            .update({self.model.status: new_status}, synchronize_session=False)
        )
        return result

    @handle_db_operation("get_table_availability")
    def get_table_availability(
        self, session: Session, start_time: datetime, end_time: datetime
    ) -> List[Tuple[Table, List[Tuple[datetime, datetime]]]]:
        """
        Get detailed availability information for all tables within a time range
        Returns: List of tuples (table, list of busy periods)
        """
        tables = session.query(self.model).all()
        availability_info = []

        for table in tables:
            busy_periods = []
            # Get all non-cancelled reservations for this table in the time range
            reservations = [
                r
                for r in table.reservations
                if r.status != ReservationStatus.CANCELLED
                and r.reservation_datetime < end_time
                and (r.reservation_datetime + timedelta(minutes=r.duration))
                > start_time
            ]

            # Sort reservations by start time
            reservations.sort(key=lambda r: r.reservation_datetime)

            # Create list of busy periods
            for reservation in reservations:
                period_start = reservation.reservation_datetime
                period_end = period_start + timedelta(minutes=reservation.duration)
                busy_periods.append((period_start, period_end))

            availability_info.append((table, busy_periods))

        return availability_info

    @handle_db_operation("find_next_available_time")
    def find_next_available_time(
        self,
        session: Session,
        party_size: int,
        preferred_time: datetime,
        duration_minutes: int = 120,
        max_tables: int = 2,
    ) -> Optional[datetime]:
        """
        Find the next available time slot for a party if preferred time is not available
        """
        # Try preferred time first
        available = self.find_tables_for_party(
            session, party_size, preferred_time, duration_minutes, max_tables
        )
        if available:
            return preferred_time

        # Get all reservations after preferred time
        tables = (
            session.query(self.model).filter(self.model.capacity >= party_size).all()
        )

        if not tables:
            return None

        # Get all future reservations for these tables
        future_times = set([preferred_time])
        for table in tables:
            for reservation in table.reservations:
                if reservation.status != ReservationStatus.CANCELLED:
                    future_times.add(reservation.reservation_datetime)
                    future_times.add(
                        reservation.reservation_datetime
                        + timedelta(minutes=reservation.duration)
                    )

        # Sort times and try each as a potential start time
        for time in sorted(future_times):
            if time <= preferred_time:
                continue

            available = self.find_tables_for_party(
                session, party_size, time, duration_minutes, max_tables
            )
            if available:
                return time

        return None
