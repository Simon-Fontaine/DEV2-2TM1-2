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

    restaurant.update_order(args.order_id, **updates)

    logging.info(
        f"Updated order: #{args.order_id} "
        f"(table: {args.table_number}, status: {args.status.value}, "
        f"items: {len(args.items)})"
    )


def list_orders(args, restaurant: Restaurant) -> None:
    orders = restaurant.list_orders()

    if args.table:
        orders = [order for order in orders if order.table_number == args.table]

    if args.status:
        orders = [order for order in orders if order.status == OrderStatus(args.status)]

    if not orders:
        logging.info("No orders found matching the criteria.")
    else:
        for order in orders:
            logging.info(f"\n{order}\n")


def cancel_order(args, restaurant: Restaurant) -> None:
    restaurant.remove_order(args.order_id)
    logging.info(f"Cancelled order: #{args.order_id}")
