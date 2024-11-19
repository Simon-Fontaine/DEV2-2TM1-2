from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload
from .base_service import BaseService, handle_db_operation
from ..models.order import Order, OrderStatus, PaymentMethod
from ..models.order_item import OrderItem
from ..models.table import Table, TableStatus
from ..models.menu_item import MenuItem


class OrderService(BaseService[Order]):
    """Service for managing order-related operations"""

    @handle_db_operation("create_order")
    def create_order(
        self,
        session: Session,
        table_id: int,
        customer_id: Optional[int] = None,
        items: List[Dict] = None,
    ) -> Order:
        """Create a new order with optional items and return it with relationships loaded"""
        # Check table availability
        table = session.query(Table).get(table_id)
        if not table or table.status not in [
            TableStatus.AVAILABLE,
            TableStatus.RESERVED,
        ]:
            raise ValueError("Table is not available for new orders")

        # Create order
        order = Order(
            table_id=table_id,
            customer_id=customer_id,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
        )
        session.add(order)
        session.flush()

        # Add items if provided
        if items:
            for item_data in items:
                menu_item = session.query(MenuItem).get(item_data["menu_item_id"])
                if not menu_item or not menu_item.is_available:
                    raise ValueError(
                        f"Menu item {item_data['menu_item_id']} is not available"
                    )

                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=menu_item.id,
                    quantity=item_data["quantity"],
                    unit_price=menu_item.price,
                    notes=item_data.get("notes"),
                )
                session.add(order_item)

        # Update table status
        table.status = TableStatus.OCCUPIED

        # Calculate total
        order.total_amount = order.calculate_total()
        session.flush()

        # Eagerly load related attributes before returning
        created_order = (
            session.query(self.model)
            .options(
                joinedload(Order.table),
                joinedload(Order.customer),
                joinedload(Order.items).joinedload(OrderItem.menu_item),
            )
            .filter(Order.id == order.id)
            .one()
        )
        return created_order

    @handle_db_operation("delete_order")
    def delete_order(self, session: Session, order_id: int) -> bool:
        """Delete an order if it's in a deletable state"""
        order = session.query(self.model).get(order_id)
        if not order:
            raise ValueError("Order not found")

        if order.status not in [OrderStatus.PENDING, OrderStatus.CANCELLED]:
            raise ValueError("Only pending or cancelled orders can be deleted")

        # Update table status if this is the only order
        table = order.table
        other_active_orders = [
            o
            for o in table.orders
            if o.id != order_id
            and o.status not in [OrderStatus.CANCELLED, OrderStatus.PAID]
        ]

        if not other_active_orders:
            table.status = TableStatus.AVAILABLE

        session.delete(order)
        return True

    @handle_db_operation("cancel_order")
    def cancel_order(self, session: Session, order_id: int) -> Order:
        """Cancel an order and update related entities, returning updated order with relationships loaded"""
        order = session.query(self.model).get(order_id)
        if not order:
            raise ValueError("Order not found")

        if order.status in [OrderStatus.PAID, OrderStatus.CANCELLED]:
            raise ValueError("Cannot cancel a paid or already cancelled order")

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now()

        # Update table status if this is the last active order
        table = order.table
        other_active_orders = [
            o
            for o in table.orders
            if o.id != order_id
            and o.status not in [OrderStatus.CANCELLED, OrderStatus.PAID]
        ]

        if not other_active_orders:
            table.status = TableStatus.AVAILABLE

        session.flush()

        # Eagerly load related attributes before returning
        updated_order = (
            session.query(self.model)
            .options(
                joinedload(Order.table),
                joinedload(Order.customer),
                joinedload(Order.items).joinedload(OrderItem.menu_item),
            )
            .filter(Order.id == order_id)
            .one()
        )
        return updated_order

    @handle_db_operation("add_items")
    def add_items(self, session: Session, order_id: int, items: List[Dict]) -> Order:
        """Add items to an existing order and return updated order with relationships loaded"""
        order = session.query(self.model).get(order_id)
        if not order or order.status in [
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
            OrderStatus.PAID,
        ]:
            raise ValueError("Cannot add items to this order")

        for item_data in items:
            menu_item = session.query(MenuItem).get(item_data["menu_item_id"])
            if not menu_item or not menu_item.is_available:
                raise ValueError(
                    f"Menu item {item_data['menu_item_id']} is not available"
                )

            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=menu_item.id,
                quantity=item_data["quantity"],
                unit_price=menu_item.price,
                notes=item_data.get("notes"),
            )
            session.add(order_item)

        order.total_amount = order.calculate_total()
        order.updated_at = datetime.now()
        session.flush()

        # Eagerly load related attributes before returning
        updated_order = (
            session.query(self.model)
            .options(
                joinedload(Order.table),
                joinedload(Order.customer),
                joinedload(Order.items).joinedload(OrderItem.menu_item),
            )
            .filter(Order.id == order_id)
            .one()
        )
        return updated_order

    @handle_db_operation("remove_item")
    def remove_item(self, session: Session, order_id: int, item_id: int) -> Order:
        """Remove an item from an order and return updated order with relationships loaded"""
        order = session.query(self.model).get(order_id)
        if not order or order.status in [
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
            OrderStatus.PAID,
        ]:
            raise ValueError("Cannot modify this order")

        item = session.query(OrderItem).get(item_id)
        if item and item.order_id == order_id:
            session.delete(item)
            order.total_amount = order.calculate_total()
            order.updated_at = datetime.now()
            session.flush()

            # Eagerly load related attributes before returning
            updated_order = (
                session.query(self.model)
                .options(
                    joinedload(Order.table),
                    joinedload(Order.customer),
                    joinedload(Order.items).joinedload(OrderItem.menu_item),
                )
                .filter(Order.id == order_id)
                .one()
            )
            return updated_order
        else:
            raise ValueError("Item not found in order")

    @handle_db_operation("update_status")
    def update_status(
        self, session: Session, order_id: int, new_status: OrderStatus
    ) -> Order:
        """Update order status with validation"""
        order = session.query(self.model).get(order_id)
        if not order:
            raise ValueError("Order not found")

        # Validate status transitions
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED],
            OrderStatus.IN_PROGRESS: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
            OrderStatus.COMPLETED: [OrderStatus.PAID],
            OrderStatus.CANCELLED: [],
            OrderStatus.PAID: [],
        }

        if new_status not in valid_transitions[order.status]:
            raise ValueError(
                f"Invalid status transition from {order.status.value} to {new_status.value}"
            )

        # If transitioning to PAID, ensure payment is processed
        if new_status == OrderStatus.PAID and not order.is_paid:
            return self.process_payment(
                order.id, PaymentMethod.CASH, order.total_amount
            )

        order.update_status(new_status)
        order.updated_at = datetime.now()

        # Handle table status updates
        if new_status in [OrderStatus.PAID, OrderStatus.CANCELLED]:
            table = order.table
            if not any(
                o
                for o in table.orders
                if o.status not in [OrderStatus.PAID, OrderStatus.CANCELLED]
            ):
                table.status = TableStatus.CLEANING

        session.flush()

        # Return updated order with relationships loaded
        return (
            session.query(self.model)
            .options(
                joinedload(Order.table),
                joinedload(Order.customer),
                joinedload(Order.items).joinedload(OrderItem.menu_item),
            )
            .filter(Order.id == order_id)
            .one()
        )

    @handle_db_operation("process_payment")
    def process_payment(
        self,
        session: Session,
        order_id: int,
        payment_method: PaymentMethod,
        amount_paid: float,
    ) -> Order:
        """Process payment for an order"""
        order = session.query(self.model).get(order_id)
        if not order:
            raise ValueError("Order not found")

        if order.is_paid:
            raise ValueError("Order is already paid")

        if amount_paid < order.total_amount:
            raise ValueError("Payment amount is less than order total")

        order.payment_method = payment_method
        order.is_paid = True
        order.update_status(OrderStatus.PAID)
        order.updated_at = datetime.now()

        # Update table status if this is the last active order
        table = order.table
        other_active_orders = [
            o
            for o in table.orders
            if o.id != order_id
            and o.status not in [OrderStatus.PAID, OrderStatus.CANCELLED]
        ]

        if not other_active_orders:
            table.status = TableStatus.CLEANING

        session.flush()

        # Return updated order with relationships loaded
        return (
            session.query(self.model)
            .options(
                joinedload(Order.table),
                joinedload(Order.customer),
                joinedload(Order.items).joinedload(OrderItem.menu_item),
            )
            .filter(Order.id == order_id)
            .one()
        )

    @handle_db_operation("get_all_orders")
    def get_all_orders(self, session: Session, limit: int = 100) -> List[Order]:
        """Get all orders with optional limit, sorted by creation date"""
        return (
            session.query(self.model)
            .options(
                joinedload(Order.table),
                joinedload(Order.customer),
                joinedload(Order.items).joinedload(OrderItem.menu_item),
            )
            .order_by(desc(Order.created_at))
            .limit(limit)
            .all()
        )

    @handle_db_operation("get_active_orders")
    def get_active_orders(self, session: Session) -> List[Order]:
        """Get all active orders (not cancelled or paid)"""
        return (
            session.query(self.model)
            .filter(
                self.model.status.in_(
                    [
                        OrderStatus.PENDING,
                        OrderStatus.IN_PROGRESS,
                        OrderStatus.COMPLETED,
                    ]
                )
            )
            .options(
                joinedload(Order.table),
                joinedload(Order.customer),
                joinedload(Order.items).joinedload(OrderItem.menu_item),
            )
            .order_by(self.model.created_at.desc())
            .all()
        )

    @handle_db_operation("get_table_orders")
    def get_table_orders(
        self, session: Session, table_id: int, include_completed: bool = False
    ) -> List[Order]:
        """Get orders for a specific table"""
        query = session.query(self.model).filter(self.model.table_id == table_id)

        if not include_completed:
            query = query.filter(
                self.model.status.in_([OrderStatus.PENDING, OrderStatus.IN_PROGRESS])
            )

        return (
            query.options(
                joinedload(Order.table),
                joinedload(Order.customer),
                joinedload(Order.items).joinedload(OrderItem.menu_item),
            )
            .order_by(self.model.created_at.desc())
            .all()
        )

    @handle_db_operation("get_filtered_orders")
    def get_filtered_orders(
        self, session: Session, status: str, time_period: str
    ) -> List[Order]:
        """Get orders filtered by status and time period"""
        query = session.query(self.model).options(
            joinedload(Order.table),
            joinedload(Order.customer),
            joinedload(Order.items).joinedload(OrderItem.menu_item),
        )

        # Apply status filter
        if status != "All":
            query = query.filter(self.model.status == OrderStatus(status))

        # Apply time filter
        if time_period != "All":
            now = datetime.now()
            if time_period == "Today":
                cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_period == "Last 3 Days":
                cutoff = now - timedelta(days=3)
            elif time_period == "Last Week":
                cutoff = now - timedelta(days=7)
            else:  # Last Month
                cutoff = now - timedelta(days=30)
            query = query.filter(self.model.created_at >= cutoff)

        orders = query.order_by(desc(Order.created_at)).all()
        return orders

    @handle_db_operation("search_orders")
    def search_orders(
        self,
        session: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[OrderStatus] = None,
        table_id: Optional[int] = None,
        customer_id: Optional[int] = None,
    ) -> List[Order]:
        """Search orders with various filters"""
        query = session.query(self.model).options(
            joinedload(Order.table),
            joinedload(Order.customer),
            joinedload(Order.items).joinedload(OrderItem.menu_item),
        )

        if start_date:
            query = query.filter(self.model.created_at >= start_date)
        if end_date:
            query = query.filter(self.model.created_at <= end_date)
        if status:
            query = query.filter(self.model.status == status)
        if table_id:
            query = query.filter(self.model.table_id == table_id)
        if customer_id:
            query = query.filter(self.model.customer_id == customer_id)

        return query.order_by(self.model.created_at.desc()).all()

    @handle_db_operation("get_order_statistics")
    def get_order_statistics(
        self, session: Session, start_date: datetime, end_date: datetime
    ) -> Dict:
        """Get order statistics for a date range"""
        orders = self.search_orders(session, start_date, end_date)

        total_orders = len(orders)
        total_revenue = sum(
            o.total_amount for o in orders if o.status == OrderStatus.PAID
        )
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

        status_counts = {}
        for status in OrderStatus:
            status_counts[status.value] = len([o for o in orders if o.status == status])

        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "average_order_value": avg_order_value,
            "status_counts": status_counts,
        }
