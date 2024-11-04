import logging
from argparse import Namespace

from models.restaurant import Restaurant
from models.table import Table, TableStatus


def add_table(args: Namespace, restaurant: Restaurant) -> None:
    status = TableStatus(args.status) if args.status else TableStatus.AVAILABLE
    table = Table(args.table_number, args.capacity, status)
    restaurant.add_table(table)
    logging.info(f"Added table: #{table.table_number} (capacity: {table.capacity})")


def delete_table(args: Namespace, restaurant: Restaurant) -> None:
    restaurant.delete_table(args.table_number)
    logging.info(f"Deleted table: #{args.table_number}")


def merge_tables(args: Namespace, restaurant: Restaurant) -> None:
    restaurant.merge_tables(args.table_numbers)
    logging.info(
        f"Merged tables: {', '.join(str(table_number) for table_number in args.table_numbers)}"
    )


def split_table(args: Namespace, restaurant: Restaurant) -> None:
    restaurant.split_table(args.table_number, args.new_capacities)
    logging.info(
        f"Split table: #{args.table_number} into {len(args.new_capacities)} new tables"
    )


def update_table(args: Namespace, restaurant: Restaurant) -> None:
    status = TableStatus(args.status) if args.status else None
    restaurant.update_table(args.table_number, args.capacity, status)
    logging.info(
        f"Updated table: #{args.table_number} (capacity: {args.capacity}, status: {args.status})"
    )


def list_tables(args: Namespace, restaurant: Restaurant) -> None:
    tables = restaurant.list_tables()

    if not tables:
        logging.info("No tables found")
        return

    for table in tables:
        logging.info(table)
