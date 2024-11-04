import argparse
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.restaurant import Restaurant
from models.table import TableStatus
from commands.table_commands import (
    AddTableCommand,
    DeleteTableCommand,
    UpdateTableCommand,
    ListTablesCommand,
)
from commands.reservation_commands import (
    AddReservationCommand,
    CancelReservationCommand,
    ModifyReservationCommand,
    ListReservationsCommand,
)
from commands.order_commands import (
    AddOrderCommand,
    ModifyOrderCommand,
    DeleteOrderCommand,
    ListOrdersCommand,
)
from datetime import datetime


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def get_default_state_file() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "..", "restaurant_state.json")


def main():
    setup_logging()
    default_state_file = get_default_state_file()
    parser = create_parser(default_state_file)
    args = parser.parse_args()
    restaurant = Restaurant.load_state(args.file)

    if args.command is None:
        parser.print_help()
        return

    try:
        args.func(args, restaurant)
    except Exception as e:
        logging.error(e)
        sys.exit(1)

    restaurant.save_state(args.file)


def create_parser(default_state_file: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Restaurant Management System")
    parser.add_argument(
        "--file",
        type=str,
        default=default_state_file,
        help="File to save/load the restaurant state.",
    )
    subparsers = parser.add_subparsers(title="Commands", dest="command")

    # Table Commands
    table_parser = subparsers.add_parser("table", help="Manage tables")
    table_subparsers = table_parser.add_subparsers(dest="subcommand")

    # Add Table
    parser_add_table = table_subparsers.add_parser("add", help="Add a new table")
    parser_add_table.add_argument("id", type=int, help="Table number")
    parser_add_table.add_argument(
        "--capacity", type=int, required=True, help="Table capacity"
    )
    parser_add_table.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in TableStatus],
        default=TableStatus.AVAILABLE.value,
        help="Table status",
    )
    parser_add_table.set_defaults(func=add_table)

    # Delete Table
    parser_delete_table = table_subparsers.add_parser("delete", help="Delete a table")
    parser_delete_table.add_argument("id", type=int, help="Table number")
    parser_delete_table.set_defaults(func=delete_table)

    # Update Table
    parser_update_table = table_subparsers.add_parser("update", help="Update a table")
    parser_update_table.add_argument("id", type=int, help="Table number")
    parser_update_table.add_argument("--capacity", type=int, help="New capacity")
    parser_update_table.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in TableStatus],
        help="New status",
    )
    parser_update_table.set_defaults(func=update_table)

    # List Tables
    parser_list_tables = table_subparsers.add_parser("list", help="List all tables")
    parser_list_tables.set_defaults(func=list_tables)

    # Reservation Commands
    reservation_parser = subparsers.add_parser(
        "reservation", help="Manage reservations"
    )
    reservation_subparsers = reservation_parser.add_subparsers(dest="subcommand")

    # Add Reservation
    parser_add_reservation = reservation_subparsers.add_parser(
        "add", help="Add a new reservation"
    )
    parser_add_reservation.add_argument("id", type=int, help="Reservation ID")
    parser_add_reservation.add_argument("customer_id", type=int, help="Customer ID")
    parser_add_reservation.add_argument("table_number", type=int, help="Table number")
    parser_add_reservation.add_argument(
        "number_of_people", type=int, help="Number of people"
    )
    parser_add_reservation.add_argument(
        "reservation_time_str",
        type=str,
        help="Reservation time in ISO format (YYYY-MM-DDTHH:MM)",
    )
    parser_add_reservation.set_defaults(func=add_reservation)

    # Cancel Reservation
    parser_cancel_reservation = reservation_subparsers.add_parser(
        "cancel", help="Cancel a reservation"
    )
    parser_cancel_reservation.add_argument("id", type=int, help="Reservation ID")
    parser_cancel_reservation.set_defaults(func=cancel_reservation)

    # Modify Reservation
    parser_modify_reservation = reservation_subparsers.add_parser(
        "modify", help="Modify a reservation"
    )
    parser_modify_reservation.add_argument("id", type=int, help="Reservation ID")
    parser_modify_reservation.add_argument(
        "--table_number", type=int, help="New table number"
    )
    parser_modify_reservation.add_argument(
        "--number_of_people", type=int, help="New number of people"
    )
    parser_modify_reservation.add_argument(
        "--reservation_time_str",
        type=str,
        help="New reservation time in ISO format (YYYY-MM-DDTHH:MM)",
    )
    parser_modify_reservation.set_defaults(func=modify_reservation)

    # List Reservations
    parser_list_reservations = reservation_subparsers.add_parser(
        "list", help="List all reservations"
    )
    parser_list_reservations.set_defaults(func=list_reservations)

    # Order Commands
    order_parser = subparsers.add_parser("order", help="Manage orders")
    order_subparsers = order_parser.add_subparsers(dest="subcommand")

    # Add Order
    parser_add_order = order_subparsers.add_parser("add", help="Add a new order")
    parser_add_order.add_argument("id", type=int, help="Order ID")
    parser_add_order.add_argument("table_number", type=int, help="Table number")
    parser_add_order.add_argument(
        "items",
        nargs="+",
        help='Order items in the format "dish_name:quantity:price"',
    )
    parser_add_order.set_defaults(func=add_order)

    # Modify Order
    parser_modify_order = order_subparsers.add_parser("modify", help="Modify an order")
    parser_modify_order.add_argument("id", type=int, help="Order ID")
    parser_modify_order.add_argument(
        "--items",
        nargs="+",
        help='New order items in the format "dish_name:quantity:price"',
    )
    parser_modify_order.add_argument(
        "--status", type=str, help="New preparation status"
    )
    parser_modify_order.set_defaults(func=modify_order)

    # Delete Order
    parser_delete_order = order_subparsers.add_parser("delete", help="Delete an order")
    parser_delete_order.add_argument("id", type=int, help="Order ID")
    parser_delete_order.set_defaults(func=delete_order)

    # List Orders
    parser_list_orders = order_subparsers.add_parser("list", help="List all orders")
    parser_list_orders.set_defaults(func=list_orders)

    return parser


# Wrapper functions for table commands


def add_table(args, restaurant):
    command = AddTableCommand(
        restaurant=restaurant,
        table_number=args.id,
        capacity=args.capacity,
        status=TableStatus(args.status),
    )
    command.execute()


def delete_table(args, restaurant):
    command = DeleteTableCommand(
        restaurant=restaurant,
        table_number=args.id,
    )
    command.execute()


def update_table(args, restaurant):
    new_status = TableStatus(args.status) if args.status else None
    command = UpdateTableCommand(
        restaurant=restaurant,
        table_number=args.id,
        new_capacity=args.capacity,
        new_status=new_status,
    )
    command.execute()


def list_tables(args, restaurant):
    command = ListTablesCommand(restaurant=restaurant)
    command.execute()


# Wrapper functions for reservation commands


def add_reservation(args, restaurant):
    command = AddReservationCommand(
        restaurant=restaurant,
        reservation_id=args.id,
        customer_id=args.customer_id,
        table_number=args.table_number,
        number_of_people=args.number_of_people,
        reservation_time_str=args.reservation_time_str,
    )
    command.execute()


def cancel_reservation(args, restaurant):
    command = CancelReservationCommand(
        restaurant=restaurant,
        reservation_id=args.id,
    )
    command.execute()


def modify_reservation(args, restaurant):
    updates = {}
    if args.table_number is not None:
        updates["table_number"] = args.table_number
    if args.number_of_people is not None:
        updates["number_of_people"] = args.number_of_people
    if args.reservation_time is not None:
        updates["reservation_time"] = datetime.fromisoformat(args.reservation_time_str)
    command = ModifyReservationCommand(
        restaurant=restaurant,
        reservation_id=args.id,
        **updates,
    )
    command.execute()


def list_reservations(args, restaurant):
    command = ListReservationsCommand(restaurant=restaurant)
    command.execute()


# Wrapper functions for order commands


def add_order(args, restaurant):
    items_data = []
    for item_str in args.items:
        try:
            dish_name, quantity_str, price_str = item_str.split(":")
            items_data.append(
                {
                    "dish_name": dish_name,
                    "quantity": int(quantity_str),
                    "price": float(price_str),
                }
            )
        except ValueError:
            raise ValueError(
                f"Invalid item format: {item_str}. Expected format is 'dish_name:quantity:price'"
            )
    command = AddOrderCommand(
        restaurant=restaurant,
        order_id=args.id,
        table_number=args.table_number,
        items_data=items_data,
    )
    command.execute()


def modify_order(args, restaurant):
    items_data = None
    if args.items:
        items_data = []
        for item_str in args.items:
            try:
                dish_name, quantity_str, price_str = item_str.split(":")
                items_data.append(
                    {
                        "dish_name": dish_name,
                        "quantity": int(quantity_str),
                        "price": float(price_str),
                    }
                )
            except ValueError:
                raise ValueError(
                    f"Invalid item format: {item_str}. Expected format is 'dish_name:quantity:price'"
                )
    command = ModifyOrderCommand(
        restaurant=restaurant,
        order_id=args.id,
        items_data=items_data,
        preparation_status=args.status,
    )
    command.execute()


def delete_order(args, restaurant):
    command = DeleteOrderCommand(
        restaurant=restaurant,
        order_id=args.id,
    )
    command.execute()


def list_orders(args, restaurant):
    command = ListOrdersCommand(restaurant=restaurant)
    command.execute()


if __name__ == "__main__":
    main()
