import logging
from typing import Optional, List
from models.db import session_scope
from models.order import Order, OrderStatus, OrderItem
from models.menu_item import MenuItem
from models.table import Table, TableStatus
from sqlalchemy.exc import IntegrityError


def add_order(
    table_number: int,
    items: List[str],
    status: Optional[str] = None,
) -> None:
    with session_scope() as session:
        # Fetch the table
        table = session.query(Table).filter_by(table_number=table_number).first()
        if not table:
            logging.error(f"Table #{table_number} does not exist.")
            return

        # Check table status
        if table.current_status not in [TableStatus.RESERVED, TableStatus.OCCUPIED]:
            logging.error(
                f"Table #{table_number} is not reserved or occupied and cannot accept orders."
            )
            return

        # Determine the order status
        if status:
            try:
                # Ensure the provided status is valid and get its value
                order_status = OrderStatus(status).value
            except ValueError:
                logging.error(
                    f"Invalid order status: '{status}'. Must be one of {[s.value for s in OrderStatus]}."
                )
                return
        else:
            # Default status is 'Pending'
            order_status = OrderStatus.PENDING.value

        # Create a new Order
        new_order = Order(
            table=table, status=order_status  # Use the Enum's value, not name
        )
        session.add(new_order)

        # Process order items
        for item_str in items:
            try:
                menu_item_id, quantity = map(int, item_str.split(":"))
            except ValueError:
                logging.error(
                    f"Invalid item format: '{item_str}'. Use 'menu_item_id:quantity'."
                )
                session.rollback()
                return

            menu_item = session.query(MenuItem).filter_by(id=menu_item_id).first()
            if not menu_item:
                logging.error(f"Menu Item with ID {menu_item_id} does not exist.")
                session.rollback()
                return
            if not menu_item.is_available:
                logging.error(f"Menu Item '{menu_item.name}' is currently unavailable.")
                session.rollback()
                return

            order_item = OrderItem(
                order=new_order, menu_item=menu_item, quantity=quantity
            )
            session.add(order_item)

        try:
            session.commit()
            logging.info(
                f"Successfully added Order ID {new_order.id} for Table #{table_number}. "
                f"Items: {', '.join(items)}. Status: {new_order.status}."
            )
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to add order: {e.orig}")
        except ValueError as e:
            session.rollback()
            logging.error(f"Validation error: {e}")


def update_order(
    order_id: int,
    items: Optional[List[str]] = None,
    status: Optional[str] = None,
) -> None:
    with session_scope() as session:
        order = session.query(Order).filter_by(id=order_id).first()
        if not order:
            logging.error(f"Order with ID {order_id} does not exist.")
            return

        # Update status if provided
        if status:
            try:
                # Ensure the provided status is valid and get its value
                order.status = OrderStatus(status).value
            except ValueError:
                logging.error(
                    f"Invalid order status: '{status}'. Must be one of {[s.value for s in OrderStatus]}."
                )
                return

        # Update items if provided
        if items:
            # Clear existing order items
            order.order_items.clear()
            # Add new order items
            for item_str in items:
                try:
                    menu_item_id, quantity = map(int, item_str.split(":"))
                except ValueError:
                    logging.error(
                        f"Invalid item format: '{item_str}'. Use 'menu_item_id:quantity'."
                    )
                    session.rollback()
                    return

                menu_item = session.query(MenuItem).filter_by(id=menu_item_id).first()
                if not menu_item:
                    logging.error(f"Menu Item with ID {menu_item_id} does not exist.")
                    session.rollback()
                    return
                if not menu_item.is_available:
                    logging.error(
                        f"Menu Item '{menu_item.name}' is currently unavailable."
                    )
                    session.rollback()
                    return

                order_item = OrderItem(
                    order=order, menu_item=menu_item, quantity=quantity
                )
                session.add(order_item)

        try:
            session.commit()
            logging.info(f"Successfully updated Order ID {order.id}.")
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to update order: {e.orig}")
        except ValueError as e:
            session.rollback()
            logging.error(f"Validation error: {e}")


def cancel_order(order_id: int) -> None:
    with session_scope() as session:
        order = session.query(Order).filter_by(id=order_id).first()
        if not order:
            logging.error(f"Order with ID {order_id} does not exist.")
            return
        order.status = OrderStatus.CANCELLED.value  # Use the Enum's value
        try:
            session.commit()
            logging.info(f"Successfully cancelled Order ID {order.id}.")
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to cancel order: {e.orig}")
        except ValueError as e:
            session.rollback()
            logging.error(f"Validation error: {e}")


def list_orders(
    table_number: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> None:
    with session_scope() as session:
        query = session.query(Order)
        if table_number is not None:
            table = session.query(Table).filter_by(table_number=table_number).first()
            if not table:
                logging.error(f"Table #{table_number} does not exist.")
                return
            query = query.filter_by(table=table)
        if status:
            try:
                # Ensure the provided status is valid and get its value
                status_enum = OrderStatus(status).value
                query = query.filter_by(status=status_enum)
            except ValueError:
                logging.error(
                    f"Invalid order status: '{status}'. Must be one of {[s.value for s in OrderStatus]}."
                )
                return

        total_orders = query.count()
        orders = (
            query.order_by(Order.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        if not orders:
            logging.info("No orders found matching the criteria.")
        else:
            total_pages = ((total_orders - 1) // page_size) + 1
            logging.info(f"Displaying page {page} of {total_pages}")
            for order in orders:
                items = ", ".join(
                    f"{item.menu_item.name} (x{item.quantity})"
                    for item in order.order_items
                )
                logging.info(
                    f"Order ID: {order.id}, Table: {order.table.table_number}, "
                    f"Items: {items}, Status: {order.status}"
                )
