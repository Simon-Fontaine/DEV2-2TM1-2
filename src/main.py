import argparse
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.restaurant import Restaurant
from models.table import TableStatus
from models.reservation import ReservationStatus
from models.order import OrderStatus

from commands.table_commands import (
    add_table,
    delete_table,
    merge_tables,
    split_table,
    update_table,
    list_tables,
)

from commands.reservation_commands import (
    add_reservation,
    cancel_reservation,
    update_reservation,
    list_reservations,
)

from commands.order_commands import (
    add_order,
    update_order,
    cancel_order,
    list_orders,
)


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def get_default_state_file() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "..", "restaurant_state.json")


def main():
    setup_logging()
    default_state_file = get_default_state_file()
    parser = create_parser()
    args = parser.parse_args()
    restaurant = Restaurant.load_state(default_state_file)

    if args.command is None:
        parser.print_help()
        return

    try:
        args.func(args, restaurant)
    except Exception as e:
        logging.error(e)
        sys.exit(1)

    restaurant.save_state(default_state_file)


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

    # Add Table
    add_table_parser = table_subparsers.add_parser("add", help="Add a new table")
    add_table_parser.add_argument("table_number", type=int, help="Table number")
    add_table_parser.add_argument("capacity", type=int, help="Table capacity")
    add_table_parser.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in TableStatus],
        default=TableStatus.AVAILABLE.value,
        help="New table status (default: Available)",
    )
    add_table_parser.set_defaults(func=add_table)

    # Delete Table
    delete_table_parser = table_subparsers.add_parser("delete", help="Delete a table")
    delete_table_parser.add_argument("table_number", type=int, help="Table number")
    delete_table_parser.set_defaults(func=delete_table)

    # Update Table
    update_table_parser = table_subparsers.add_parser("update", help="Update a table")
    update_table_parser.add_argument("table_number", type=int, help="Table number")
    update_table_parser.add_argument("--capacity", type=int, help="New table capacity")
    update_table_parser.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in TableStatus],
        help="New table status",
    )
    update_table_parser.set_defaults(func=update_table)

    # Merge Tables
    merge_tables_parser = table_subparsers.add_parser("merge", help="Merge tables")
    merge_tables_parser.add_argument(
        "table_numbers", type=int, nargs="+", help="Table numbers to merge"
    )
    merge_tables_parser.set_defaults(func=merge_tables)

    # Split Table
    split_table_parser = table_subparsers.add_parser("split", help="Split a table")
    split_table_parser.add_argument(
        "table_number", type=int, help="Table number to split"
    )
    split_table_parser.add_argument(
        "new_capacities", type=int, nargs="+", help="Capacities of the new tables"
    )
    split_table_parser.set_defaults(func=split_table)

    # List Tables
    list_tables_parser = table_subparsers.add_parser("list", help="List all tables")
    list_tables_parser.set_defaults(func=list_tables)

    # --------------------------------------------------------------------------
    # Reservation Commands
    reservation_parser = subparsers.add_parser(
        "reservation", help="Manage reservations"
    )
    reservation_subparsers = reservation_parser.add_subparsers(
        dest="reservation_command", help="Available reservation commands"
    )

    # Add Reservation
    add_reservation_parser = reservation_subparsers.add_parser(
        "add", help="Add a new reservation"
    )
    add_reservation_parser.add_argument(
        "reservation_id", type=int, help="Reservation ID"
    )
    add_reservation_parser.add_argument("customer_id", type=int, help="Customer ID")
    add_reservation_parser.add_argument("table_number", type=int, help="Table number")
    add_reservation_parser.add_argument(
        "number_of_people", type=int, help="Number of people"
    )
    add_reservation_parser.add_argument(
        "reservation_time", type=str, help="Reservation time (YYYY-MM-DD HH:MM)"
    )
    add_reservation_parser.set_defaults(func=add_reservation)

    # Update Reservation
    update_reservation_parser = reservation_subparsers.add_parser(
        "update", help="Update a reservation"
    )
    update_reservation_parser.add_argument(
        "reservation_id", type=int, help="Reservation ID"
    )
    update_reservation_parser.add_argument(
        "--table_number", type=int, help="New table number"
    )
    update_reservation_parser.add_argument(
        "--number_of_people", type=int, help="New number of people"
    )
    update_reservation_parser.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in ReservationStatus],
        help="New reservation status",
    )
    update_reservation_parser.add_argument(
        "--reservation_time", type=str, help="New reservation time (YYYY-MM-DD HH:MM)"
    )
    update_reservation_parser.set_defaults(func=update_reservation)

    # Cancel Reservation
    cancel_reservation_parser = reservation_subparsers.add_parser(
        "cancel", help="Cancel a reservation"
    )
    cancel_reservation_parser.add_argument(
        "reservation_id", type=int, help="Reservation ID"
    )
    cancel_reservation_parser.set_defaults(func=cancel_reservation)

    # List Reservations
    list_reservations_parser = reservation_subparsers.add_parser(
        "list", help="List all reservations"
    )
    list_reservations_parser.set_defaults(func=list_reservations)

    # --------------------------------------------------------------------------
    # Order Commands
    order_parser = subparsers.add_parser("order", help="Manage orders")
    order_subparsers = order_parser.add_subparsers(
        dest="order_command", help="Available order commands"
    )

    # Add Order
    add_order_parser = order_subparsers.add_parser("add", help="Add a new order")
    add_order_parser.add_argument("order_id", type=int, help="Order ID")
    add_order_parser.add_argument("table_number", type=int, help="Table number")
    add_order_parser.add_argument(
        "items",
        nargs="+",
        help='Order items in the format "dish_name:quantity:price"',
    )
    add_order_parser.set_defaults(func=add_order)

    # Update Order
    update_order_parser = order_subparsers.add_parser("update", help="Update an order")
    update_order_parser.add_argument("order_id", type=int, help="Order ID")
    update_order_parser.add_argument(
        "--table_number", type=int, help="New table number"
    )
    update_order_parser.add_argument(
        "--items",
        nargs="+",
        help='Updated order items in the format "dish_name:quantity:price"',
    )
    update_order_parser.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in OrderStatus],
        help="New order status",
    )
    update_order_parser.set_defaults(func=update_order)

    # Cancel Order
    cancel_order_parser = order_subparsers.add_parser("cancel", help="Cancel an order")
    cancel_order_parser.add_argument("order_id", type=int, help="Order ID")
    cancel_order_parser.set_defaults(func=cancel_order)

    # List Orders
    list_orders_parser = order_subparsers.add_parser("list", help="List all orders")
    list_orders_parser.add_argument(
        "--table", type=int, help="Filter orders by table number"
    )
    list_orders_parser.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in OrderStatus],
        help="Filter orders by status",
    )
    list_orders_parser.set_defaults(func=list_orders)

    return parser


if __name__ == "__main__":
    main()
