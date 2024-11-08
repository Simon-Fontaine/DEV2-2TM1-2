import logging
from typing import Optional
from models.db import session_scope
from models.table import Table, TableStatus
from sqlalchemy.exc import IntegrityError


def create_table(
    table_number: int, capacity: int, status: str = TableStatus.AVAILABLE.value
) -> None:
    with session_scope() as session:
        # Check if table already exists
        existing_table = (
            session.query(Table).filter_by(table_number=table_number).first()
        )
        if existing_table:
            logging.error(f"Table #{table_number} already exists.")
            return

        try:
            table_status = TableStatus(status)
        except ValueError:
            logging.error(f"Invalid table status: {status}.")
            return

        new_table = Table(
            table_number=table_number, capacity=capacity, status=table_status
        )
        session.add(new_table)
        try:
            session.commit()
            logging.info(
                f"Successfully created Table #{table_number} with capacity {capacity}."
            )
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to create table: {e.orig}")


def delete_table(table_number: int) -> None:
    with session_scope() as session:
        table = session.query(Table).filter_by(table_number=table_number).first()
        if not table:
            logging.error(f"Table #{table_number} does not exist.")
            return
        session.delete(table)
        try:
            session.commit()
            logging.info(f"Successfully deleted Table #{table_number}.")
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to delete table: {e.orig}")


def list_tables(
    status: Optional[str] = None,
    capacity_min: Optional[int] = None,
    capacity_max: Optional[int] = None,
) -> None:
    with session_scope() as session:
        tables = session.query(Table).all()

        filtered_tables = []
        for table in tables:
            table_status = table.current_status

            if status and table_status != TableStatus(status):
                continue
            if capacity_min is not None and table.capacity < capacity_min:
                continue
            if capacity_max is not None and table.capacity > capacity_max:
                continue
            filtered_tables.append(table)

        if not filtered_tables:
            logging.info("No tables found matching the criteria.")
        else:
            for table in filtered_tables:
                logging.info(
                    f"Table #{table.table_number}: Capacity {table.capacity} "
                    f"seat{'s' if table.capacity > 1 else ''} "
                    f"(Status: {table.current_status.value})."
                )


def update_table(
    table_number: int,
    capacity: Optional[int] = None,
    status: Optional[str] = None,
) -> None:
    with session_scope() as session:
        table = session.query(Table).filter_by(table_number=table_number).first()
        if not table:
            logging.error(f"Table #{table_number} does not exist.")
            return

        if capacity is not None:
            table.capacity = capacity

        if status is not None:
            try:
                table_status = TableStatus(status)
                table.status = table_status
            except ValueError:
                logging.error(f"Invalid table status: {status}.")
                return

        try:
            session.commit()
            logging.info(f"Successfully updated Table #{table_number}.")
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to update table: {e.orig}")
