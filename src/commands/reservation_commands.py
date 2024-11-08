import logging
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from models.db import session_scope
from models.reservation import Reservation, ReservationStatus
from models.customer import Customer
from models.table import Table, TableStatus
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String


def add_reservation(
    customer_id: int,
    table_numbers: Optional[List[int]],
    reservation_time_str: str,
    number_of_people: int,
    status: Optional[str] = None,
    duration_minutes: int = 120,
) -> None:
    with session_scope() as session:
        # Parse reservation_time
        try:
            reservation_time = datetime.strptime(reservation_time_str, "%Y-%m-%d %H:%M")
        except ValueError:
            logging.error("Invalid date format. Use 'YYYY-MM-DD HH:MM'.")
            return

        # Fetch customer
        customer = session.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            logging.error(f"Customer with ID {customer_id} does not exist.")
            return

        # Fetch specified tables or find suitable ones using the optimized greedy algorithm
        if table_numbers:
            # Fetch specified tables
            tables = (
                session.query(Table).filter(Table.table_number.in_(table_numbers)).all()
            )
            if len(tables) != len(table_numbers):
                missing_tables = set(table_numbers) - {t.table_number for t in tables}
                logging.error(
                    f"Tables not found: {', '.join(map(str, missing_tables))}"
                )
                return
        else:
            # Find table combinations using the optimized greedy algorithm
            tables = find_table_combinations(
                session, reservation_time, number_of_people, duration_minutes
            )
            if not tables:
                logging.error("No available tables can accommodate the party size.")
                return
            logging.info(
                f"Assigned tables: {', '.join(str(t.table_number) for t in tables)}"
            )

        # Check combined capacity
        total_capacity = sum(table.capacity for table in tables)
        if total_capacity < number_of_people:
            logging.error(
                f"Combined table capacity ({total_capacity}) is insufficient for {number_of_people} people."
            )
            return

        # Create reservation
        reservation_status = (
            ReservationStatus(status) if status else ReservationStatus.PENDING
        )
        reservation = Reservation(
            customer=customer,
            tables=tables,
            reservation_time=reservation_time,
            number_of_people=number_of_people,
            status=reservation_status,
            duration_minutes=duration_minutes,
        )
        session.add(reservation)

        try:
            session.commit()
            logging.info(
                f"Successfully added reservation ID {reservation.id} for customer '{customer.name}' "
                f"on {reservation_time.strftime('%Y-%m-%d %H:%M')} for {number_of_people} people. "
                f"Assigned Tables: {', '.join(str(t.table_number) for t in tables)}."
            )
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to add reservation: {e.orig}")
        except ValueError as e:
            session.rollback()
            logging.error(f"Validation error: {e}")


def find_table_combinations(
    session: Session,
    reservation_time: datetime,
    number_of_people: int,
    duration_minutes: int = 120,
) -> Optional[List[Table]]:
    """
    Finds the minimal number of tables required to accommodate the party size
    using a greedy algorithm, considering the reservation duration.
    """
    # Calculate the end time of the reservation
    reservation_end_time = reservation_time + timedelta(minutes=duration_minutes)

    # Prepare duration string for SQLAlchemy datetime arithmetic
    duration_str = cast(Reservation.duration_minutes, String) + " minutes"

    # Calculate reservation end time within the query
    reservation_end = func.datetime(Reservation.reservation_time, duration_str)

    # Get all available tables at the reservation time
    available_tables = (
        session.query(Table)
        .filter(
            ~Table.reservations.any(
                and_(
                    Reservation.status == ReservationStatus.CONFIRMED,
                    Reservation.reservation_time <= reservation_end_time,
                    reservation_end > reservation_time,
                )
            ),
            Table.status != TableStatus.UNDER_MAINTENANCE,
        )
        .order_by(Table.capacity.asc())
        .all()
    )

    assigned_tables = []
    total_capacity = 0

    for table in available_tables:
        assigned_tables.append(table)
        total_capacity += table.capacity
        if total_capacity >= number_of_people:
            break

    if total_capacity >= number_of_people:
        return assigned_tables
    else:
        return None


def update_reservation(
    reservation_id: int,
    table_numbers: Optional[List[int]] = None,
    reservation_time_str: Optional[str] = None,
    number_of_people: Optional[int] = None,
    status: Optional[str] = None,
    duration_minutes: Optional[int] = None,
) -> None:
    with session_scope() as session:
        reservation = session.query(Reservation).filter_by(id=reservation_id).first()
        if not reservation:
            logging.error(f"Reservation with ID {reservation_id} does not exist.")
            return

        needs_reassignment = False

        # Update number_of_people and mark for reassignment if increased
        if number_of_people is not None:
            if number_of_people <= 0:
                logging.error("Number of people must be a positive integer.")
                return
            if number_of_people > reservation.number_of_people:
                needs_reassignment = True
            reservation.number_of_people = number_of_people

        # Update reservation_time and mark for reassignment if changed
        if reservation_time_str is not None:
            try:
                new_reservation_time = datetime.strptime(
                    reservation_time_str, "%Y-%m-%d %H:%M"
                )
                if new_reservation_time != reservation.reservation_time:
                    needs_reassignment = True
                    reservation.reservation_time = new_reservation_time
            except ValueError:
                logging.error("Invalid date format. Use 'YYYY-MM-DD HH:MM'.")
                return

        # Update duration_minutes if provided
        if duration_minutes is not None:
            if duration_minutes <= 0:
                logging.error("Duration must be a positive integer.")
                return
            reservation.duration_minutes = duration_minutes
            needs_reassignment = True  # Recalculate if duration changes

        # Update tables if table_numbers are provided
        if table_numbers is not None:
            # Fetch specified tables
            new_tables = (
                session.query(Table).filter(Table.table_number.in_(table_numbers)).all()
            )
            if len(new_tables) != len(table_numbers):
                missing_tables = set(table_numbers) - {
                    t.table_number for t in new_tables
                }
                logging.error(
                    f"Tables not found: {', '.join(map(str, missing_tables))}"
                )
                return

            # Check combined capacity
            required_people = (
                number_of_people
                if number_of_people is not None
                else reservation.number_of_people
            )
            total_capacity = sum(table.capacity for table in new_tables)
            if total_capacity < required_people:
                logging.error(
                    f"Combined table capacity ({total_capacity}) is insufficient for "
                    f"{required_people} people."
                )
                return

            # Assign new tables
            reservation.tables = new_tables
            needs_reassignment = True  # Recheck in case of table capacity changes

        # If reassignment is needed due to party size, reservation time, or duration changes
        if needs_reassignment:
            # Attempt to find a new combination of tables
            new_tables = find_table_combinations(
                session,
                reservation.reservation_time,
                reservation.number_of_people,
                reservation.duration_minutes,
            )
            if not new_tables:
                logging.error(
                    "No available tables can accommodate the updated party size and/or time."
                )
                return
            logging.info(
                f"Reassigning tables: {', '.join(str(t.table_number) for t in new_tables)}"
            )
            reservation.tables = new_tables

        # Update reservation status if provided
        if status:
            try:
                reservation.status = ReservationStatus(status)
            except ValueError:
                logging.error(f"Invalid reservation status: {status}.")
                return

        try:
            session.commit()
            logging.info(f"Successfully updated reservation ID {reservation.id}.")
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to update reservation: {e.orig}")
        except ValueError as e:
            session.rollback()
            logging.error(f"Validation error: {e}")


def cancel_reservation(reservation_id: int) -> None:
    with session_scope() as session:
        reservation = session.query(Reservation).filter_by(id=reservation_id).first()
        if not reservation:
            logging.error(f"Reservation with ID {reservation_id} does not exist.")
            return
        reservation.status = ReservationStatus.CANCELLED
        try:
            session.commit()
            logging.info(f"Successfully cancelled reservation ID {reservation.id}.")
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to cancel reservation: {e.orig}")


def list_reservations(
    customer_id: Optional[int] = None,
    table_number: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> None:
    with session_scope() as session:
        query = session.query(Reservation)
        if customer_id is not None:
            query = query.filter_by(customer_id=customer_id)
        if table_number is not None:
            table = session.query(Table).filter_by(table_number=table_number).first()
            if not table:
                logging.error(f"Table #{table_number} does not exist.")
                return
            query = query.filter(Reservation.tables.contains(table))
        if status:
            try:
                status_enum = ReservationStatus(status)
                query = query.filter_by(status=status_enum)
            except ValueError:
                logging.error(f"Invalid reservation status: {status}.")
                return

        total_reservations = query.count()
        reservations = (
            query.order_by(Reservation.reservation_time.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        if not reservations:
            logging.info("No reservations found matching the criteria.")
        else:
            total_pages = ((total_reservations - 1) // page_size) + 1
            logging.info(f"Displaying page {page} of {total_pages}")
            for res in reservations:
                table_numbers = ", ".join(str(t.table_number) for t in res.tables)
                logging.info(
                    f"Reservation ID: {res.id}, Customer: {res.customer.name}, "
                    f"Tables: {table_numbers}, Time: {res.reservation_time.strftime('%Y-%m-%d %H:%M')}, "
                    f"Duration: {res.duration_minutes} mins, Status: {res.status.value}, "
                    f"People: {res.number_of_people}"
                )
