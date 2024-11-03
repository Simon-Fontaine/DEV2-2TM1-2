import argparse
import logging
import sys
from typing import Optional
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.restaurant import Restaurant
from models.table import TableStatus


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def get_default_state_file() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "..", "restaurant_state.json")


def create_parser(default_state_file: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Table Management System")
    parser.add_argument(
        "--file",
        type=str,
        default=default_state_file,
        help="File to save/load the restaurant state.",
    )
    subparsers = parser.add_subparsers(title="Commands", dest="command")

    subparsers.add_parser("list", help="List all tables")

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

    parser_add = subparsers.add_parser("add", help="Add a new table")
    parser_add.add_argument("id", type=int, help="Table number")
    parser_add.add_argument(
        "--capacity", type=int, help="Table capacity", required=True
    )
    parser_add.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in TableStatus],
        default=TableStatus.AVAILABLE.value,
        help="Table status",
    )

    parser_delete = subparsers.add_parser("delete", help="Delete a table")
    parser_delete.add_argument("id", type=int, help="Table number")

    return parser


def handle_command(args: argparse.Namespace, restaurant: Restaurant) -> bool:
    def add_table():
        restaurant.add_table(args.id, args.capacity, TableStatus(args.status))

    def delete_table():
        restaurant.delete_table(args.id)

    def update_table():
        restaurant.update_table(
            args.id,
            args.capacity if args.capacity else None,
            args.status if args.status else None,
        )

    def list_tables():
        restaurant.list_tables()

    command_handlers = {
        "add": add_table,
        "delete": delete_table,
        "update": update_table,
        "list": list_tables,
    }

    handler = command_handlers.get(args.command)
    if handler:
        handler()
        return True
    return False


def main() -> None:
    setup_logging()
    default_state_file = get_default_state_file()
    parser = create_parser(default_state_file)
    args = parser.parse_args()
    restaurant = Restaurant.load_state(args.file)

    if not handle_command(args, restaurant):
        parser.print_help()

    restaurant.save_state(args.file)


if __name__ == "__main__":
    main()
