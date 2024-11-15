import logging
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.exc import IntegrityError
from models.db import session_scope
from models.reservation import Reservation
from models.customer import Customer
from models.table import Table, TableStatus
from sqlalchemy.orm import Session
from itertools import combinations
from sqlalchemy import func, cast, and_, String


def parse_datetime(date_str: str) -> Optional[datetime]:
    """Parse a datetime string in the format 'YYYY-MM-DD HH:MM'."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    except ValueError:
        logging.error("Invalid date format. Use 'YYYY-MM-DD HH:MM'.")
        return None


def find_customer(session: Session, customer_id: int) -> Optional[Customer]:
    """Retrieve a customer by ID or log an error if not found."""
    customer = session.query(Customer).filter_by(id=customer_id).first()
    if not customer:
        logging.error(f"Customer with ID {customer_id} does not exist.")
    return customer


def find_tables(session: Session, table_numbers: List[int]) -> Optional[List[Table]]:
    """Retrieve tables by their numbers or log an error if any are missing."""
    tables = session.query(Table).filter(Table.table_number.in_(table_numbers)).all()
    if len(tables) != len(table_numbers):
        missing = set(table_numbers) - {table.table_number for table in tables}
        logging.error(f"Tables not found: {', '.join(map(str, missing))}")
        return None
    return tables


def find_best_table_combination(
    session: Session,
    reservation_time: datetime,
    number_of_people: int,
    duration_minutes: int = 120,
) -> Optional[List[Table]]:
    reservation_end_time = reservation_time + timedelta(minutes=duration_minutes)
    duration_str = cast(Reservation.duration_minutes, String) + " minutes"
    reservation_end = func.datetime(Reservation.reservation_time, duration_str)

    available_tables = (
        session.query(Table)
        .filter(
            ~Table.reservations.any(
                and_(
                    Reservation.reservation_time <= reservation_end_time,
                    reservation_end > reservation_time,
                )
            ),
            Table.status != TableStatus.UNDER_MAINTENANCE,
        )
        .order_by(Table.capacity.desc())
        .all()
    )

    # Generate all possible combinations of tables
    for r in range(1, len(available_tables) + 1):
        for table_group in combinations(available_tables, r):
            total_capacity = sum(table.capacity for table in table_group)
            if total_capacity >= number_of_people:
                return list(table_group)

    logging.error("No table combination can accommodate the party size.")
    return None


def add_reservation(
    customer_id: int,
    table_numbers: Optional[List[int]],
    reservation_time_str: str,
    number_of_people: int,
    duration_minutes: int = 120,
) -> None:
    with session_scope() as session:
        # Parse reservation time
        reservation_time = parse_datetime(reservation_time_str)
        if not reservation_time:
            return

        # Fetch customer
        customer = find_customer(session, customer_id)
        if not customer:
            return

        # Find tables
        if table_numbers:
            tables = find_tables(session, table_numbers)
            if not tables:
                return
        else:
            tables = find_best_table_combination(
                session, reservation_time, number_of_people, duration_minutes
            )
            if not tables:
                return

        # Check combined capacity
        total_capacity = sum(table.capacity for table in tables)
        if total_capacity < number_of_people:
            logging.error(
                f"Combined table capacity ({total_capacity}) is insufficient for {number_of_people} people."
            )
            return

        # Create reservation

        reservation = Reservation(
            customer=customer,
            tables=tables,
            reservation_time=reservation_time,
            number_of_people=number_of_people,
            duration_minutes=duration_minutes,
        )
        session.add(reservation)

        try:
            session.commit()
            logging.info(
                f"Reservation created successfully for {number_of_people} people "
                f"at {reservation_time.strftime('%Y-%m-%d %H:%M')} using tables: "
                f"{', '.join(str(table.table_number) for table in tables)}."
            )
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to create reservation: {e.orig}")


def cancel_reservation(reservation_id: int) -> None:
    """Cancel a reservation by removing it from the database."""
    with session_scope() as session:
        reservation = session.query(Reservation).filter_by(id=reservation_id).first()
        if not reservation:
            logging.error(f"Reservation with ID {reservation_id} does not exist.")
            return

        try:
            session.delete(reservation)
            session.commit()
            logging.info(
                f"Successfully cancelled and removed reservation ID {reservation_id}."
            )
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to cancel reservation: {e.orig}")


def update_reservation(
    reservation_id: int,
    table_numbers: Optional[List[int]] = None,
    reservation_time_str: Optional[str] = None,
    number_of_people: Optional[int] = None,
    duration_minutes: Optional[int] = None,
) -> None:
    """Update an existing reservation with new details."""
    with session_scope() as session:
        reservation = session.query(Reservation).filter_by(id=reservation_id).first()
        if not reservation:
            logging.error(f"Reservation with ID {reservation_id} does not exist.")
            return

        needs_reassignment = False

        # Update reservation time
        if reservation_time_str:
            new_reservation_time = parse_datetime(reservation_time_str)
            if not new_reservation_time:
                return
            if new_reservation_time != reservation.reservation_time:
                reservation.reservation_time = new_reservation_time
                needs_reassignment = True

        # Update number of people
        if number_of_people is not None:
            if number_of_people <= 0:
                logging.error("Number of people must be a positive integer.")
                return
            if number_of_people > reservation.number_of_people:
                needs_reassignment = True
            reservation.number_of_people = number_of_people

        # Update duration
        if duration_minutes is not None:
            if duration_minutes <= 0:
                logging.error("Duration must be a positive integer.")
                return
            reservation.duration_minutes = duration_minutes
            needs_reassignment = True

        # Update tables
        if table_numbers:
            tables = find_tables(session, table_numbers)
            if not tables:
                return

            required_capacity = number_of_people or reservation.number_of_people
            if sum(table.capacity for table in tables) < required_capacity:
                logging.error("Selected tables do not meet the required capacity.")
                return
            reservation.tables = tables

        # Reassign tables if necessary
        if needs_reassignment:
            new_tables = find_best_table_combination(
                session,
                reservation.reservation_time,
                reservation.number_of_people,
                reservation.duration_minutes,
            )
            if not new_tables:
                logging.error(
                    "No available tables can accommodate the updated reservation details."
                )
                return
            reservation.tables = new_tables

        try:
            session.commit()
            logging.info(f"Successfully updated reservation ID {reservation.id}.")
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to update reservation: {e.orig}")


def list_reservations(
    customer_id: Optional[int] = None,
    table_number: Optional[int] = None,
    page: int = 1,
    page_size: int = 10,
) -> None:
    """List reservations with optional filters for customer, table."""
    with session_scope() as session:
        query = session.query(Reservation)

        # Filter by customer ID
        if customer_id:
            customer = find_customer(session, customer_id)
            if not customer:
                return
            query = query.filter_by(customer_id=customer_id)

        # Filter by table number
        if table_number:
            table = session.query(Table).filter_by(table_number=table_number).first()
            if not table:
                logging.error(f"Table #{table_number} does not exist.")
                return
            query = query.filter(Reservation.tables.contains(table))

        # Pagination
        total_reservations = query.count()
        reservations = (
            query.order_by(Reservation.reservation_time.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        # Display results
        if not reservations:
            logging.info("No reservations found matching the criteria.")
            return

        total_pages = (total_reservations + page_size - 1) // page_size
        logging.info(f"Displaying page {page} of {total_pages}")
        for reservation in reservations:
            table_numbers = ", ".join(
                str(table.table_number) for table in reservation.tables
            )
            logging.info(
                f"Reservation ID: {reservation.id}, Customer: {reservation.customer.name}, "
                f"Tables: {table_numbers}, Time: {reservation.reservation_time.strftime('%Y-%m-%d %H:%M')}, "
                f"Duration: {reservation.duration_minutes} mins, People: {reservation.number_of_people}"
            )
