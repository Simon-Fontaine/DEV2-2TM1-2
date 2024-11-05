import logging
from typing import List, Optional
from models.db import session_scope
from models.table import Table, TableStatus


def create_table(
    capacity: int,
    status: Optional[TableStatus] = None,
) -> None:
    with session_scope() as session:

        table = Table(capacity=capacity)
        if status is not None:
            table.status = status
        session.add(table)
        session.commit()

        logging.info(
            f"Created table: #{table.table_number} ({table.capacity} seat{"s" if table.capacity > 1 else ""})."
        )


def delete_table(table_number: int) -> None:
    with session_scope() as session:
        table = session.query(Table).filter_by(table_number=table_number).first()
        if not table:
            raise ValueError(f"Table #{table_number} does not exist.")
        session.delete(table)
        session.commit()

        logging.info(f"Deleted table: #{table.table_number}.")


def list_tables(
    status: Optional[TableStatus] = None,
    capacity_min: Optional[int] = None,
    capacity_max: Optional[int] = None,
) -> List[Table]:
    with session_scope() as session:
        filter = []
        if status is not None:
            filter.append(Table.status == TableStatus(status))
        if capacity_min is not None:
            filter.append(Table.capacity >= capacity_min)
        if capacity_max is not None:
            filter.append(Table.capacity <= capacity_max)

        tables = session.query(Table).filter(*filter).all()

        if not tables:
            logging.info("No tables found matching the criteria.")

        for table in tables:
            logging.info(
                f"Table #{table.table_number}: {table.capacity} seat{'s' if table.capacity > 1 else ''} ({table.status.value})."
            )


def update_table(
    table_number: int,
    new_capacity: Optional[int] = None,
    new_status: Optional[TableStatus] = None,
) -> None:
    with session_scope() as session:
        table = session.query(Table).filter_by(table_number=table_number).first()
        if not table:
            raise ValueError(f"Table #{table_number} does not exist.")
        if new_capacity is not None:
            table.capacity = new_capacity
        if new_status is not None:
            table.status = TableStatus(new_status)
        session.commit()

        logging.info(
            f"Updated table #{table.table_number}: {table.capacity} seat{'s' if table.capacity > 1 else ''} ({table.status.value})."
        )
