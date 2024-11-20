import logging
from typing import List, Optional, Dict, Set, Tuple
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from .base_service import BaseService, handle_db_operation
from ..models.reservation import Reservation, ReservationStatus, ReservationPriority
from ..models.customer import Customer
from ..models.table import Table, TableStatus

logger = logging.getLogger(__name__)


class ReservationConflictError(Exception):
    """Raised when there is a scheduling conflict"""

    pass


class InvalidReservationError(Exception):
    """Raised when reservation parameters are invalid"""

    pass


class ReservationService(BaseService[Reservation]):
    """Optimized service for managing reservations"""

    MINIMUM_DURATION = 30  # minutes
    MAXIMUM_DURATION = 480  # 8 hours
    ADVANCE_BOOKING_LIMIT = 90  # days
    MINIMUM_PARTY_SIZE = 1
    MAXIMUM_PARTY_SIZE = 50

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reservation_cache = {}  # Simple cache for active reservations

    @handle_db_operation("search_reservations")
    def search_reservations(
        self,
        session: Session,
        customer_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[ReservationStatus] = None,
        table_id: Optional[int] = None,
    ) -> List[Reservation]:
        """Search reservations with various filters"""
        query = session.query(self.model).options(
            joinedload(Reservation.customer), joinedload(Reservation.tables)
        )

        if customer_name:
            query = query.join(Customer).filter(
                Customer.name.ilike(f"%{customer_name}%")
            )

        if start_date:
            query = query.filter(self.model.reservation_datetime >= start_date)

        if end_date:
            query = query.filter(self.model.reservation_datetime <= end_date)

        if status:
            query = query.filter(self.model.status == status)

        if table_id:
            query = query.join(Reservation.tables).filter(Table.id == table_id)

        return query.order_by(self.model.reservation_datetime).all()

    @handle_db_operation("get_upcoming_reservations")
    def get_upcoming_reservations(
        self, session: Session, include_checked_in: bool = True, hours_ahead: int = 24
    ) -> List[Reservation]:
        """Get upcoming reservations within specified hours"""
        now = datetime.now()
        end_time = now + timedelta(hours=hours_ahead)

        statuses = [ReservationStatus.CONFIRMED]
        if include_checked_in:
            statuses.append(ReservationStatus.CHECKED_IN)

        return (
            session.query(self.model)
            .options(joinedload(Reservation.customer), joinedload(Reservation.tables))
            .filter(
                self.model.reservation_datetime.between(now, end_time),
                self.model.status.in_(statuses),
            )
            .order_by(self.model.reservation_datetime)
            .all()
        )

    @handle_db_operation("check_in")
    def check_in(self, session: Session, reservation_id: int) -> Reservation:
        """Check in a reservation"""
        reservation = session.query(self.model).get(reservation_id)
        if not reservation:
            raise InvalidReservationError("Reservation not found")

        if reservation.status != ReservationStatus.CONFIRMED:
            raise InvalidReservationError("Reservation cannot be checked in")

        # Update reservation status
        reservation.status = ReservationStatus.CHECKED_IN

        # Update table statuses
        for table in reservation.tables:
            table.status = TableStatus.OCCUPIED

        session.flush()

        return (
            session.query(self.model)
            .options(joinedload(Reservation.customer), joinedload(Reservation.tables))
            .get(reservation_id)
        )

    @handle_db_operation("complete_reservation")
    def complete_reservation(
        self, session: Session, reservation_id: int
    ) -> Reservation:
        """Mark a reservation as completed"""
        reservation = session.query(self.model).get(reservation_id)
        if not reservation:
            raise InvalidReservationError("Reservation not found")

        if reservation.status != ReservationStatus.CHECKED_IN:
            raise InvalidReservationError(
                "Only checked-in reservations can be completed"
            )

        # Update reservation status
        reservation.status = ReservationStatus.COMPLETED

        # Update table statuses
        for table in reservation.tables:
            table.status = TableStatus.CLEANING

        session.flush()

        return (
            session.query(self.model)
            .options(joinedload(Reservation.customer), joinedload(Reservation.tables))
            .get(reservation_id)
        )

    @handle_db_operation("cancel_reservation")
    def cancel_reservation(self, session: Session, reservation_id: int) -> Reservation:
        """Cancel a reservation"""
        reservation = session.query(self.model).get(reservation_id)
        if not reservation:
            raise InvalidReservationError("Reservation not found")

        if not reservation.can_cancel():
            raise InvalidReservationError("Reservation cannot be cancelled")

        # Update reservation status
        reservation.status = ReservationStatus.CANCELLED

        # Update table statuses if they were reserved
        for table in reservation.tables:
            if table.status == TableStatus.RESERVED:
                table.status = TableStatus.AVAILABLE

        session.flush()

        return (
            session.query(self.model)
            .options(joinedload(Reservation.customer), joinedload(Reservation.tables))
            .get(reservation_id)
        )

    @handle_db_operation("mark_no_show")
    def mark_no_show(self, session: Session, reservation_id: int) -> Reservation:
        """Mark a reservation as no-show"""
        reservation = session.query(self.model).get(reservation_id)
        if not reservation:
            raise InvalidReservationError("Reservation not found")

        if reservation.status != ReservationStatus.CONFIRMED:
            raise InvalidReservationError(
                "Only confirmed reservations can be marked as no-show"
            )

        if reservation.reservation_datetime > datetime.now():
            raise InvalidReservationError("Cannot mark future reservations as no-show")

        # Update reservation status
        reservation.status = ReservationStatus.NO_SHOW

        # Update table statuses
        for table in reservation.tables:
            if table.status == TableStatus.RESERVED:
                table.status = TableStatus.AVAILABLE

        session.flush()

        return (
            session.query(self.model)
            .options(joinedload(Reservation.customer), joinedload(Reservation.tables))
            .get(reservation_id)
        )

    def _validate_reservation_parameters(
        self,
        reservation_datetime: datetime,
        party_size: int,
        duration: int,
        customer_id: Optional[int] = None,
    ) -> None:
        """Validate basic reservation parameters"""
        now = datetime.now()
        max_future_date = now + timedelta(days=self.ADVANCE_BOOKING_LIMIT)

        if reservation_datetime < now:
            raise InvalidReservationError("Reservation time cannot be in the past")

        if reservation_datetime > max_future_date:
            raise InvalidReservationError(
                f"Reservations cannot be made more than {self.ADVANCE_BOOKING_LIMIT} days in advance"
            )

        if duration < self.MINIMUM_DURATION:
            raise InvalidReservationError(
                f"Duration must be at least {self.MINIMUM_DURATION} minutes"
            )

        if duration > self.MAXIMUM_DURATION:
            raise InvalidReservationError(
                f"Duration cannot exceed {self.MAXIMUM_DURATION} minutes"
            )

        if party_size < self.MINIMUM_PARTY_SIZE:
            raise InvalidReservationError("Party size must be at least 1")

        if party_size > self.MAXIMUM_PARTY_SIZE:
            raise InvalidReservationError(
                f"Party size cannot exceed {self.MAXIMUM_PARTY_SIZE}"
            )

    def _get_table_conflicts(
        self,
        session: Session,
        tables: List[Table],
        start_time: datetime,
        end_time: datetime,
        exclude_reservation_id: Optional[int] = None,
    ) -> List[Tuple[Table, List[Reservation]]]:
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

        if exclude_reservation_id:
            query = query.filter(Reservation.id != exclude_reservation_id)

        # Get all reservations that might conflict
        reservations = query.all()
        conflicting_reservations = []

        # Check each reservation's time range
        for reservation in reservations:
            reservation_end = reservation.reservation_datetime + timedelta(
                minutes=int(reservation.duration)
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

    def _verify_table_availability(
        self,
        session: Session,
        tables: List[Table],
        start_time: datetime,
        end_time: datetime,
        exclude_reservation_id: Optional[int] = None,
    ) -> None:
        """Verify tables are available and handle conflicts"""
        conflicts = self._get_table_conflicts(
            session, tables, start_time, end_time, exclude_reservation_id
        )

        if conflicts:
            conflict_details = []
            for table, reservations in conflicts:
                conflict_times = [
                    f"{r.reservation_datetime.strftime('%H:%M')} - "
                    f"{(r.reservation_datetime + timedelta(minutes=int(r.duration))).strftime('%H:%M')}"
                    for r in reservations
                ]
                conflict_details.append(
                    f"Table {table.number} has conflicts at: {', '.join(conflict_times)}"
                )

            raise ReservationConflictError(
                "Scheduling conflict detected:\n" + "\n".join(conflict_details)
            )

    def _verify_total_capacity(self, tables: List[Table], party_size: int) -> None:
        """Verify tables can accommodate the party size"""
        total_capacity = sum(table.capacity for table in tables)
        if total_capacity < party_size:
            raise InvalidReservationError(
                f"Selected tables (total capacity: {total_capacity}) "
                f"cannot accommodate party size of {party_size}"
            )

    @handle_db_operation("create_reservation")
    def create_reservation(
        self,
        session: Session,
        customer_id: int,
        reservation_datetime: datetime,
        party_size: int,
        duration: int = 120,
        table_ids: List[int] = None,
        notes: str = None,
        special_requests: str = None,
        priority: ReservationPriority = ReservationPriority.MEDIUM,
    ) -> Reservation:
        """Create a new reservation with enhanced validation and conflict checking"""
        try:
            # Validate basic parameters
            self._validate_reservation_parameters(
                reservation_datetime, party_size, duration, customer_id
            )

            # Verify customer exists
            customer = session.query(Customer).get(customer_id)
            if not customer:
                raise InvalidReservationError("Customer not found")

            # Get and verify tables
            if not table_ids:
                raise InvalidReservationError("At least one table must be selected")

            tables = session.query(Table).filter(Table.id.in_(table_ids)).all()
            if len(tables) != len(table_ids):
                raise InvalidReservationError("One or more tables not found")

            # Verify total capacity
            self._verify_total_capacity(tables, party_size)

            # Calculate end time
            end_time = reservation_datetime + timedelta(minutes=int(duration))

            # Check for conflicts
            self._verify_table_availability(
                session, tables, reservation_datetime, end_time
            )

            # Create reservation with PENDING status
            reservation = Reservation(
                customer_id=customer_id,
                reservation_datetime=reservation_datetime,
                party_size=party_size,
                duration=duration,
                notes=notes,
                special_requests=special_requests,
                priority=priority,
                status=ReservationStatus.PENDING,  # Changed to PENDING
                tables=tables,
            )

            session.add(reservation)
            session.flush()

            # Invalidate cache
            self._reservation_cache.clear()

            # Return reservation with relationships loaded
            return (
                session.query(self.model)
                .options(
                    joinedload(Reservation.customer), joinedload(Reservation.tables)
                )
                .get(reservation.id)
            )

        except SQLAlchemyError as e:
            logger.error(f"Database error creating reservation: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating reservation: {e}")
            raise

    @handle_db_operation("confirm_reservation")
    def confirm_reservation(self, session: Session, reservation_id: int) -> Reservation:
        """Confirm a pending reservation"""
        reservation = session.query(self.model).get(reservation_id)
        if not reservation:
            raise InvalidReservationError("Reservation not found")

        if reservation.status != ReservationStatus.PENDING:
            raise InvalidReservationError(
                f"Cannot confirm reservation in {reservation.status.value} status"
            )

        # Update reservation status
        reservation.status = ReservationStatus.CONFIRMED

        # Mark tables as reserved
        for table in reservation.tables:
            if table.status == TableStatus.AVAILABLE:
                table.status = TableStatus.RESERVED

        session.flush()

        # Return updated reservation with relationships loaded
        return (
            session.query(self.model)
            .options(joinedload(Reservation.customer), joinedload(Reservation.tables))
            .get(reservation_id)
        )

    @handle_db_operation("get_pending_reservations")
    def get_pending_reservations(
        self, session: Session, hours_ahead: int = 24
    ) -> List[Reservation]:
        """Get pending reservations within specified hours"""
        now = datetime.now()
        end_time = now + timedelta(hours=hours_ahead)

        return (
            session.query(self.model)
            .options(joinedload(Reservation.customer), joinedload(Reservation.tables))
            .filter(
                self.model.reservation_datetime.between(now, end_time),
                self.model.status == ReservationStatus.PENDING,
            )
            .order_by(self.model.reservation_datetime)
            .all()
        )

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
            # Get tables that could accommodate the party
            suitable_tables = (
                session.query(Table)
                .filter(
                    Table.status.in_([TableStatus.AVAILABLE, TableStatus.RESERVED]),
                    Table.capacity >= party_size / max_tables,  # Minimum size per table
                )
                .order_by(Table.capacity)
                .all()
            )

            if not suitable_tables:
                return []

            end_time = reservation_time + timedelta(minutes=duration)

            # Check for conflicts
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

    @handle_db_operation("update_reservation")
    def update_reservation(
        self, session: Session, reservation_id: int, **updates
    ) -> Reservation:
        """Update a reservation with conflict checking"""
        reservation = session.query(self.model).get(reservation_id)
        if not reservation:
            raise ValueError("Reservation not found")

        if reservation.status not in [
            ReservationStatus.PENDING,
            ReservationStatus.CONFIRMED,
        ]:
            raise InvalidReservationError(
                "Only pending or confirmed reservations can be updated"
            )

        # Handle datetime/duration updates
        if "reservation_datetime" in updates or "duration" in updates:
            new_datetime = updates.get(
                "reservation_datetime", reservation.reservation_datetime
            )
            new_duration = updates.get("duration", reservation.duration)

            end_time = new_datetime + timedelta(minutes=new_duration)

            # Check conflicts
            self._verify_table_availability(
                session,
                reservation.tables,
                new_datetime,
                end_time,
                exclude_reservation_id=reservation_id,
            )

        # Handle table updates
        if "table_ids" in updates:
            new_tables = (
                session.query(Table).filter(Table.id.in_(updates["table_ids"])).all()
            )

            if len(new_tables) != len(updates["table_ids"]):
                raise InvalidReservationError("One or more tables not found")

            # Verify capacity
            party_size = updates.get("party_size", reservation.party_size)
            self._verify_total_capacity(new_tables, party_size)

            # Check conflicts for new tables
            self._verify_table_availability(
                session,
                new_tables,
                updates.get("reservation_datetime", reservation.reservation_datetime),
                updates.get("reservation_datetime", reservation.reservation_datetime)
                + timedelta(minutes=updates.get("duration", reservation.duration)),
                exclude_reservation_id=reservation_id,
            )

            # Update tables
            reservation.tables = new_tables

        # Update other fields
        for key, value in updates.items():
            if key != "table_ids":
                setattr(reservation, key, value)

        # Invalidate cache
        self._reservation_cache.clear()

        return reservation
