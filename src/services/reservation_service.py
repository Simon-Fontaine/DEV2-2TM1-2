import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from .base_service import BaseService, handle_db_operation
from ..models.reservation import Reservation, ReservationStatus, ReservationPriority
from ..models.customer import Customer
from ..models.table import Table, TableStatus

logger = logging.getLogger(__name__)


class ReservationService(BaseService[Reservation]):
    """Service for managing reservations"""

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
        """Create a new reservation with validation"""
        try:
            # Validate tables if provided
            if table_ids:
                tables = session.query(Table).filter(Table.id.in_(table_ids)).all()
                if len(tables) != len(table_ids):
                    raise ValueError("One or more tables not found")

                # Check table capacity
                total_capacity = sum(table.capacity for table in tables)
                if total_capacity < party_size:
                    raise ValueError("Selected tables cannot accommodate party size")

                # Check for conflicting reservations
                end_time = reservation_datetime + timedelta(minutes=duration)

                # Get existing reservations for these tables
                existing_reservations = (
                    session.query(Reservation)
                    .join(Reservation.tables)
                    .filter(
                        Table.id.in_(table_ids),
                        Reservation.status.in_(
                            [ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN]
                        ),
                    )
                    .all()
                )

                # Check each reservation for conflicts
                for existing in existing_reservations:
                    existing_end = existing.reservation_datetime + timedelta(
                        minutes=existing.duration
                    )
                    if (
                        reservation_datetime < existing_end
                        and existing.reservation_datetime < end_time
                    ):
                        raise ValueError(
                            f"Time slot conflicts with existing reservation at {existing.reservation_datetime.strftime('%H:%M')}"
                        )

            # Create reservation
            reservation = Reservation(
                customer_id=customer_id,
                reservation_datetime=reservation_datetime,
                party_size=party_size,
                duration=duration,
                notes=notes,
                special_requests=special_requests,
                priority=priority,
                status=ReservationStatus.CONFIRMED,
            )

            if table_ids:
                reservation.tables = tables
                # Mark tables as reserved
                for table in tables:
                    table.status = TableStatus.RESERVED

            session.add(reservation)
            session.flush()

            # Load relationships before returning
            return (
                session.query(self.model)
                .options(
                    joinedload(Reservation.customer), joinedload(Reservation.tables)
                )
                .get(reservation.id)
            )

        except Exception as e:
            logger.error(f"Error creating reservation: {e}")
            raise

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
            raise ValueError("Reservation not found")

        if reservation.status != ReservationStatus.CONFIRMED:
            raise ValueError("Reservation cannot be checked in")

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
            raise ValueError("Reservation not found")

        if reservation.status != ReservationStatus.CHECKED_IN:
            raise ValueError("Only checked-in reservations can be completed")

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
            raise ValueError("Reservation not found")

        if not reservation.can_cancel():
            raise ValueError("Reservation cannot be cancelled")

        reservation.status = ReservationStatus.CANCELLED

        # Free up tables if they were already reserved
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
            raise ValueError("Reservation not found")

        if reservation.status != ReservationStatus.CONFIRMED:
            raise ValueError("Only confirmed reservations can be marked as no-show")

        # Check if reservation time has passed
        if reservation.reservation_datetime > datetime.now():
            raise ValueError("Cannot mark future reservations as no-show")

        reservation.status = ReservationStatus.NO_SHOW

        # Free up tables
        for table in reservation.tables:
            if table.status == TableStatus.RESERVED:
                table.status = TableStatus.AVAILABLE

        session.flush()
        return (
            session.query(self.model)
            .options(joinedload(Reservation.customer), joinedload(Reservation.tables))
            .get(reservation_id)
        )

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
            query = query.join("tables").filter(Table.id == table_id)

        return query.order_by(self.model.reservation_datetime.desc()).all()

    @handle_db_operation("get_table_schedule")
    def get_table_schedule(
        self, session: Session, table_id: int, date: datetime
    ) -> List[Dict]:
        """Get schedule for a specific table on a given date"""
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        reservations = (
            session.query(self.model)
            .options(joinedload(Reservation.customer))
            .join("tables")
            .filter(
                Table.id == table_id,
                self.model.reservation_datetime.between(start, end),
                self.model.status.in_(
                    [ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN]
                ),
            )
            .order_by(self.model.reservation_datetime)
            .all()
        )

        schedule = []
        for reservation in reservations:
            schedule.append(
                {
                    "reservation_id": reservation.id,
                    "customer_name": reservation.customer.name,
                    "start_time": reservation.reservation_datetime,
                    "end_time": reservation.get_end_time(),
                    "party_size": reservation.party_size,
                    "status": reservation.status.value,
                }
            )

        return schedule
