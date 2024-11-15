import logging
import argparse

from models.table import TableStatus
from models.menu_item import MenuCategory
from models.order import OrderStatus

from commands.table_commands import (
    create_table,
    delete_table,
    list_tables,
    update_table,
)

from commands.menu_item_commands import (
    add_menu_item,
    update_menu_item,
    delete_menu_item,
    list_menu_items,
)

from commands.order_commands import (
    add_order,
    update_order,
    cancel_order,
    list_orders,
)

from commands.customer_commands import (
    add_customer,
    update_customer,
    delete_customer,
    list_customers,
)

from commands.reservation_commands import (
    add_reservation,
    update_reservation,
    cancel_reservation,
    list_reservations,
)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    setup_logging()
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "table":
        if args.table_command == "create":
            create_table(args.table_number, args.capacity, args.status)
        elif args.table_command == "delete":
            delete_table(args.table_number)
        elif args.table_command == "list":
            list_tables(args.status, args.capacity_min, args.capacity_max)
        elif args.table_command == "update":
            update_table(args.table_number, args.capacity, args.status)
        else:
            logging.error("Available table commands: create, delete, list, update.")
    elif args.command == "menu":
        if args.menu_command == "add":
            add_menu_item(
                name=args.name,
                category=args.category,
                price=args.price,
                description=args.description,
                is_available=args.is_available,
            )
        elif args.menu_command == "update":
            update_menu_item(
                item_id=args.item_id,
                name=args.name,
                category=args.category,
                price=args.price,
                description=args.description,
                is_available=args.is_available,
            )
        elif args.menu_command == "delete":
            delete_menu_item(args.item_id)
        elif args.menu_command == "list":
            list_menu_items(
                category=args.category,
                is_available=args.is_available,
                price_min=args.price_min,
                price_max=args.price_max,
            )
        else:
            logging.error("Available menu commands: add, update, delete, list.")
    elif args.command == "order":
        if args.order_command == "add":
            add_order(
                table_number=args.table_number,
                items=args.items,
            )
        elif args.order_command == "update":
            update_order(
                order_id=args.order_id,
                items=args.items,
                status=args.status,
            )
        elif args.order_command == "cancel":
            cancel_order(args.order_id)
        elif args.order_command == "list":
            list_orders(
                table_number=args.table_number,
                status=args.status,
                page=args.page,
                page_size=args.page_size,
            )
        else:
            logging.error("Available order commands: add, update, cancel, list.")
    elif args.command == "customer":
        if args.customer_command == "add":
            add_customer(args.name, args.contact_info)
        elif args.customer_command == "update":
            update_customer(args.customer_id, args.name, args.contact_info)
        elif args.customer_command == "delete":
            delete_customer(args.customer_id)
        elif args.customer_command == "list":
            list_customers()
        else:
            logging.error("Available customer commands: add, update, delete, list.")
    elif args.command == "reservation":
        if args.reservation_command == "add":
            add_reservation(
                customer_id=args.customer_id,
                table_numbers=args.table_numbers,
                reservation_time_str=args.reservation_time,
                number_of_people=args.number_of_people,
                duration_minutes=args.duration,
            )
        elif args.reservation_command == "update":
            update_reservation(
                reservation_id=args.reservation_id,
                table_numbers=args.table_numbers,
                reservation_time_str=args.reservation_time,
                number_of_people=args.number_of_people,
                duration_minutes=args.duration,
            )
        elif args.reservation_command == "cancel":
            cancel_reservation(args.reservation_id)
        elif args.reservation_command == "list":
            list_reservations(
                customer_id=args.customer_id,
                table_number=args.table_number,
                page=args.page,
                page_size=args.page_size,
            )
        else:
            logging.error("Available reservation commands: add, update, cancel, list.")
    else:
        parser.print_help()


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
    add_table_parser = table_subparsers.add_parser("create", help="Create a new table")
    add_table_parser.add_argument("table_number", type=int, help="Table number")
    add_table_parser.add_argument("capacity", type=int, help="Table capacity")
    add_table_parser.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in TableStatus],
        default=TableStatus.AVAILABLE.value,
        help="Table status (default: Available)",
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
        help="Filter by table status",
    )
    list_tables_parser.add_argument(
        "--capacity_min",
        type=int,
        help="Filter by minimum capacity",
    )
    list_tables_parser.add_argument(
        "--capacity_max",
        type=int,
        help="Filter by maximum capacity",
    )

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

    # Menu Item Commands
    menu_parser = subparsers.add_parser("menu", help="Manage menu items")
    menu_subparsers = menu_parser.add_subparsers(
        dest="menu_command", help="Available menu commands"
    )

    # Add Menu Item
    add_menu_item_parser = menu_subparsers.add_parser("add", help="Add a new menu item")
    add_menu_item_parser.add_argument("name", type=str, help="Menu item name")
    add_menu_item_parser.add_argument(
        "category",
        type=str,
        choices=[category.value for category in MenuCategory],
        help="Menu item category",
    )
    add_menu_item_parser.add_argument("price", type=float, help="Menu item price")
    add_menu_item_parser.add_argument(
        "--description", type=str, help="Menu item description", default=""
    )
    add_menu_item_parser.add_argument(
        "--is_available",
        type=bool,
        nargs="?",
        const=True,
        default=True,
        help="Menu item availability (default: True)",
    )

    # Update Menu Item
    update_menu_item_parser = menu_subparsers.add_parser(
        "update", help="Update a menu item"
    )
    update_menu_item_parser.add_argument("item_id", type=int, help="Menu item ID")
    update_menu_item_parser.add_argument("--name", type=str, help="New name")
    update_menu_item_parser.add_argument(
        "--category",
        type=str,
        choices=[category.value for category in MenuCategory],
        help="New category",
    )
    update_menu_item_parser.add_argument("--price", type=float, help="New price")
    update_menu_item_parser.add_argument(
        "--description", type=str, help="New description"
    )
    update_menu_item_parser.add_argument(
        "--is_available",
        type=bool,
        nargs="?",
        const=True,
        help="Menu item availability",
    )

    # Delete Menu Item
    delete_menu_item_parser = menu_subparsers.add_parser(
        "delete", help="Delete a menu item"
    )
    delete_menu_item_parser.add_argument("item_id", type=int, help="Menu item ID")

    # List Menu Items
    list_menu_items_parser = menu_subparsers.add_parser("list", help="List menu items")
    list_menu_items_parser.add_argument(
        "--category",
        type=str,
        choices=[category.value for category in MenuCategory],
        help="Filter by category",
    )
    list_menu_items_parser.add_argument(
        "--is_available",
        type=bool,
        nargs="?",
        const=True,
        help="Filter by availability",
    )
    list_menu_items_parser.add_argument(
        "--price_min",
        type=float,
        help="Filter by minimum price",
    )
    list_menu_items_parser.add_argument(
        "--price_max",
        type=float,
        help="Filter by maximum price",
    )

    # Order Commands
    order_parser = subparsers.add_parser("order", help="Manage orders")
    order_subparsers = order_parser.add_subparsers(
        dest="order_command", help="Available order commands"
    )

    # Add Order
    add_order_parser = order_subparsers.add_parser("add", help="Add a new order")
    add_order_parser.add_argument("table_number", type=int, help="Table number")
    add_order_parser.add_argument(
        "items",
        nargs="+",
        type=str,
        help="Order items in format 'menu_item_id:quantity'",
    )

    # Update Order
    update_order_parser = order_subparsers.add_parser("update", help="Update an order")
    update_order_parser.add_argument("order_id", type=int, help="Order ID")
    update_order_parser.add_argument(
        "--items",
        nargs="+",
        type=str,
        help="New order items in format 'menu_item_id:quantity'",
    )
    update_order_parser.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in OrderStatus],
        help="New order status",
    )

    # Cancel Order
    cancel_order_parser = order_subparsers.add_parser("cancel", help="Cancel an order")
    cancel_order_parser.add_argument("order_id", type=int, help="Order ID")

    # List Orders
    list_orders_parser = order_subparsers.add_parser("list", help="List orders")
    list_orders_parser.add_argument(
        "--table_number", type=int, help="Filter by table number"
    )
    list_orders_parser.add_argument(
        "--status",
        type=str,
        choices=[status.value for status in OrderStatus],
        help="Filter by order status",
    )
    list_orders_parser.add_argument(
        "--page", type=int, default=1, help="Page number (default: 1)"
    )
    list_orders_parser.add_argument(
        "--page_size",
        type=int,
        default=10,
        help="Number of orders per page (default: 10)",
    )

    # Customer Commands
    customer_parser = subparsers.add_parser("customer", help="Manage customers")
    customer_subparsers = customer_parser.add_subparsers(
        dest="customer_command", help="Available customer commands"
    )

    # Add Customer
    add_customer_parser = customer_subparsers.add_parser(
        "add", help="Add a new customer"
    )
    add_customer_parser.add_argument("name", type=str, help="Customer name")
    add_customer_parser.add_argument(
        "contact_info", type=str, help="Contact information"
    )

    # Update Customer
    update_customer_parser = customer_subparsers.add_parser(
        "update", help="Update a customer"
    )
    update_customer_parser.add_argument("customer_id", type=int, help="Customer ID")
    update_customer_parser.add_argument("--name", type=str, help="New customer name")
    update_customer_parser.add_argument(
        "--contact_info", type=str, help="New contact information"
    )

    # Delete Customer
    delete_customer_parser = customer_subparsers.add_parser(
        "delete", help="Delete a customer"
    )
    delete_customer_parser.add_argument("customer_id", type=int, help="Customer ID")

    # List Customers
    list_customers_parser = customer_subparsers.add_parser(
        "list", help="List all customers"
    )

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
    add_reservation_parser.add_argument("customer_id", type=int, help="Customer ID")
    add_reservation_parser.add_argument(
        "--table_numbers",
        nargs="+",
        type=int,
        help="Table numbers (optional). If not provided, suitable tables will be assigned.",
    )
    add_reservation_parser.add_argument(
        "reservation_time", type=str, help="Reservation time (YYYY-MM-DD HH:MM)"
    )
    add_reservation_parser.add_argument(
        "number_of_people", type=int, help="Number of people"
    )
    add_reservation_parser.add_argument(
        "--duration",
        type=int,
        default=120,
        help="Reservation duration in minutes (default: 120)",
    )

    # Update Reservation
    update_reservation_parser = reservation_subparsers.add_parser(
        "update", help="Update a reservation"
    )
    update_reservation_parser.add_argument(
        "reservation_id", type=int, help="Reservation ID"
    )
    update_reservation_parser.add_argument(
        "--table_numbers", nargs="+", type=int, help="New table numbers"
    )
    update_reservation_parser.add_argument(
        "--reservation_time", type=str, help="New reservation time (YYYY-MM-DD HH:MM)"
    )
    update_reservation_parser.add_argument(
        "--number_of_people", type=int, help="New number of people"
    )
    update_reservation_parser.add_argument(
        "--duration",
        type=int,
        help="New reservation duration in minutes",
    )

    # Cancel Reservation
    cancel_reservation_parser = reservation_subparsers.add_parser(
        "cancel", help="Cancel a reservation"
    )
    cancel_reservation_parser.add_argument(
        "reservation_id", type=int, help="Reservation ID"
    )

    # List Reservations
    list_reservations_parser = reservation_subparsers.add_parser(
        "list", help="List reservations"
    )
    list_reservations_parser.add_argument(
        "--customer_id", type=int, help="Filter by customer ID"
    )
    list_reservations_parser.add_argument(
        "--table_number", type=int, help="Filter by table number"
    )
    list_reservations_parser.add_argument(
        "--page", type=int, default=1, help="Page number (default: 1)"
    )
    list_reservations_parser.add_argument(
        "--page_size",
        type=int,
        default=10,
        help="Number of reservations per page (default: 10)",
    )

    return parser


if __name__ == "__main__":
    main()
