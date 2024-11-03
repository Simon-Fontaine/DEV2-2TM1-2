import argparse
import logging
import sys
from typing import Optional
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.restaurant import Restaurant
from models.table import TableStatus


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_state_file = os.path.join(script_dir, "..", "restaurant_state.json")

    parser = argparse.ArgumentParser(description="Table Management System")
    parser.add_argument(
        "--file",
        type=str,
        default=default_state_file,
        help="File to save/load the restaurant state.",
    )
    subparsers = parser.add_subparsers(title="Commands", dest="command")

    # List tables
    subparsers.add_parser("list", help="List all tables")

    # Update a table
    parser_update = subparsers.add_parser(
        "update", help="Update the status or capacity of a table"
    )
    parser_update.add_argument("id", type=int, help="Table number")
    parser_update.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in TableStatus],
        help="New status",
    )
    parser_update.add_argument("--capacity", type=int, help="New capacity")

    # Add a table
    parser_add = subparsers.add_parser("add", help="Add a new table")
    parser_add.add_argument("id", type=int, help="Table number")
    parser_add.add_argument("capacity", type=int, help="Table capacity")
    parser_add.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in TableStatus],
        default=TableStatus.AVAILABLE.value,
        help="Table status",
    )

    # Delete a table
    parser_delete = subparsers.add_parser("delete", help="Delete a table")
    parser_delete.add_argument("id", type=int, help="Table number")

    args = parser.parse_args()
    restaurant = Restaurant.load_state(args.file)

    if args.command == "add":
        restaurant.add_table(args.id, args.capacity, TableStatus(args.status))
    elif args.command == "delete":
        restaurant.delete_table(args.id)
    elif args.command == "update":
        new_status: Optional[str] = args.status if args.status else None
        new_capacity: Optional[int] = args.capacity if args.capacity else None
        restaurant.update_table(args.id, new_capacity, new_status)
    elif args.command == "list":
        restaurant.list_tables()
    else:
        parser.print_help()

    restaurant.save_state(args.file)


if __name__ == "__main__":
    main()
