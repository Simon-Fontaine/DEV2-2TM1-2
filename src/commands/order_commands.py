import logging
from models.order import Order, OrderStatus
from models.order_item import OrderItem
from models.restaurant import Restaurant


def add_order(args, restaurant: Restaurant) -> None:
    order_items = []
    for item_str in args.items:
        dish_name, quantity, price = item_str.split(":")
        order_item = OrderItem(dish_name, int(quantity), float(price))
        order_items.append(order_item)

    new_order = Order(args.order_id, args.table_number, order_items)
    restaurant.add_order(new_order)
    logging.info(f"Added order: #{new_order.id} for table {new_order.table_number}")


def update_order(args, restaurant: Restaurant) -> None:
    order = restaurant.get_order(args.order_id)
    if not order:
        raise ValueError(f"Order {args.order_id} not found.")

    updates = {}
    if args.table_number:
        updates["table_number"] = args.table_number
    if args.status:
        updates["status"] = OrderStatus(args.status)
    if args.items:
        new_items = []
        for item_str in args.items:
            dish_name, quantity, price = item_str.split(":")
            order_item = OrderItem(dish_name, int(quantity), float(price))
            new_items.append(order_item)
        updates["items"] = new_items

    restaurant.update_order(order.id, **updates)

    logging.info(
        f"Updated order: #{order.id} "
        f"(table: {order.table_number}, status: {order.status.value}, "
        f"items: {len(order.items)})"
    )


def list_orders(args, restaurant: Restaurant) -> None:
    orders = restaurant.list_orders()

    # Filter by table if specified
    if args.table:
        orders = [order for order in orders if order.table_number == args.table]

    # Filter by status if specified
    if args.status:
        orders = [order for order in orders if order.status == OrderStatus(args.status)]

    if not orders:
        logging.info("No orders found matching the criteria.")
    else:
        for order in orders:
            logging.info(
                f"Order #{order.id}: Table {order.table_number}, Status: {order.status.value}"
            )
            for item in order.items:
                logging.info(f"  - {item}")
            logging.info(f"  Total: ${order.total:.2f}")
            logging.info("---")


def cancel_order(args, restaurant: Restaurant) -> None:
    order = restaurant.get_order(args.order_id)
    if not order:
        raise ValueError(f"Order {args.order_id} not found.")

    restaurant.remove_order(args.order_id)
    logging.info(f"Cancelled order: #{args.order_id}")
