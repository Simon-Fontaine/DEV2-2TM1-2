import logging
import argparse

from models.db import engine
from models.table import Base as TableBase, TableStatus

from commands.table_commands import (
    create_table,
    delete_table,
    list_tables,
    update_table,
)

TableBase.metadata.create_all(engine)


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    setup_logging()
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "table":
        if args.table_command == "create":
            create_table(args.capacity, args.status)
        elif args.table_command == "delete":
            delete_table(args.table_number)
        elif args.table_command == "list":
            list_tables(args.status, args.capacity_min, args.capacity_max)
        elif args.table_command == "update":
            update_table(args.table_number, args.capacity, args.status)
        else:
            logging.error(f"Available commands: create, delete, list, update.")

    # print(args)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A simple restaurant management system."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Table Commands
    table_parser = subparsers.add_parser("table", help="Manage tables")
    table_subparsers = table_parser.add_subparsers(
        dest="table_command", help="Available table commands"
    )

    # Create Table
    create_table_parser = table_subparsers.add_parser(
        "create", help="Create a new table"
    )
    create_table_parser.add_argument("capacity", type=int, help="Table capacity")
    create_table_parser.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in TableStatus],
        help="Table status",
    )

    # Delete Table
    delete_table_parser = table_subparsers.add_parser("delete", help="Delete a table")
    delete_table_parser.add_argument("table_number", type=int, help="Table number")

    # List Tables
    list_tables_parser = table_subparsers.add_parser("list", help="List all tables")
    list_tables_parser.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in TableStatus],
        help="Table status",
    )
    list_tables_parser.add_argument(
        "--capacity_min", type=int, help="Minimum table capacity"
    )
    list_tables_parser.add_argument(
        "--capacity_max", type=int, help="Maximum table capacity"
    )

    # Update Table
    update_table_parser = table_subparsers.add_parser("update", help="Update a table")
    update_table_parser.add_argument("table_number", type=int, help="Table number")
    update_table_parser.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in TableStatus],
        help="Table status",
    )
    update_table_parser.add_argument("--capacity", type=int, help="New table capacity")

    return parser


if __name__ == "__main__":
    main()
