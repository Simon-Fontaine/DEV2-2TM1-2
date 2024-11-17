import logging
from typing import Dict
import customtkinter as ctk
from datetime import datetime, timedelta

from .base_view import BaseView
from ..dialogs.new_order_dialog import NewOrderDialog
from ..dialogs.add_items_dialog import AddItemsDialog
from ..dialogs.payment_dialog import PaymentDialog
from ..components.order_card import OrderCard
from ...models.order import Order, OrderStatus
from ...services.order_service import OrderService
from ...services.table_service import TableService
from ...services.customer_service import CustomerService
from ...services.menu_item_service import MenuItemService

logger = logging.getLogger(__name__)


class OrdersView(BaseView[Order]):
    """Main view for order management"""

    def __init__(
        self,
        master: any,
        order_service: OrderService,
        table_service: TableService,
        customer_service: CustomerService,
        menu_service: MenuItemService,
    ):
        self.orders: Dict[int, Order] = {}
        self.table_service = table_service
        self.customer_service = customer_service
        self.menu_service = menu_service
        super().__init__(master, order_service)
        self.refresh()

    def initialize_ui(self):
        """Initialize the UI components"""
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_header()
        self._create_filters()
        self._create_orders_list()

    def _create_header(self):
        """Create header with title and controls"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        header.grid_columnconfigure(2, weight=1)

        # Title
        ctk.CTkLabel(
            header, text="Orders Management", font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=10)

        # New Order button
        ctk.CTkButton(
            header, text="New Order", width=120, command=self._handle_new_order
        ).grid(row=0, column=1, padx=10, pady=10)

        # Refresh button
        ctk.CTkButton(header, text="Refresh", width=100, command=self.refresh).grid(
            row=0, column=2, padx=10, pady=10
        )

    def _create_filters(self):
        """Create filter controls"""
        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        filters.grid_columnconfigure(3, weight=1)

        # Status filter
        status_frame = ctk.CTkFrame(filters, fg_color="transparent")
        status_frame.grid(row=0, column=0, padx=5)

        ctk.CTkLabel(status_frame, text="Status:").pack(side="left", padx=5)

        self.status_filter = ctk.StringVar(value="All")
        status_menu = ctk.CTkOptionMenu(
            status_frame,
            values=["All"] + [status.value for status in OrderStatus],
            variable=self.status_filter,
            command=self._apply_filters,
            width=120,
        )
        status_menu.pack(side="left", padx=5)

        # Time filter
        time_frame = ctk.CTkFrame(filters, fg_color="transparent")
        time_frame.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(time_frame, text="Time:").pack(side="left", padx=5)

        self.time_filter = ctk.StringVar(value="All")
        time_menu = ctk.CTkOptionMenu(
            time_frame,
            values=["All", "Today", "Last 3 Days", "Last Week", "Last Month"],
            variable=self.time_filter,
            command=self._apply_filters,
            width=120,
        )
        time_menu.pack(side="left", padx=5)

    def _create_orders_list(self):
        """Create scrollable orders list"""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.orders_frame = ctk.CTkScrollableFrame(container)
        self.orders_frame.grid(row=0, column=0, sticky="nsew")
        self.orders_frame.grid_columnconfigure(0, weight=1)

    def refresh(self):
        """Refresh the orders display with applied filters"""
        try:
            # Clear existing order cards
            for widget in self.orders_frame.winfo_children():
                widget.destroy()
            self.orders.clear()

            # Get all orders
            orders = self.service.get_all_orders()

            # Apply status filter
            status_filter = self.status_filter.get()
            if status_filter != "All":
                orders = [o for o in orders if o.status == OrderStatus(status_filter)]

            # Apply time filter
            time_filter = self.time_filter.get()
            if time_filter != "All":
                now = datetime.now()
                if time_filter == "Today":
                    cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
                elif time_filter == "Last 3 Days":
                    cutoff = now - timedelta(days=3)
                elif time_filter == "Last Week":
                    cutoff = now - timedelta(days=7)
                else:  # Last Month
                    cutoff = now - timedelta(days=30)
                orders = [o for o in orders if o.created_at >= cutoff]

            # Display filtered orders
            for idx, order in enumerate(orders):
                card = OrderCard(
                    self.orders_frame,
                    order,
                    on_status_change=self._handle_status_change,
                    on_add_items=self._handle_add_items,
                    on_remove_item=self._handle_remove_item,
                    on_payment=self._handle_payment,
                    on_cancel=self._handle_cancel_order,
                    on_delete=self._handle_delete_order,
                )
                card.grid(row=idx, column=0, padx=5, pady=5, sticky="ew")
                self.orders[order.id] = order

        except Exception as e:
            logger.error(f"Error refreshing orders view: {e}")
            self.show_error("Error", f"Failed to refresh orders: {str(e)}")

    def _apply_filters(self, *args):
        """Apply filters and refresh display"""
        self.refresh()

    def _handle_new_order(self):
        """Handle creating a new order"""
        try:
            dialog = NewOrderDialog(
                self, self.table_service, self.customer_service, self.menu_service
            )
            self.wait_window(dialog)

            if dialog.result:
                self.service.create_order(
                    table_id=dialog.result["table_id"],
                    customer_id=dialog.result.get("customer_id"),
                    items=dialog.result["items"],
                )
                self.refresh()
        except Exception as e:
            logger.error(f"Error creating new order: {e}")
            self.show_error("Error", f"Failed to create order: {str(e)}")

    def _handle_status_change(self, order: Order, new_status: OrderStatus):
        """Handle order status changes"""
        try:
            self.service.update_status(order.id, new_status)
            self.refresh()
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            self.show_error("Error", f"Failed to update order status: {str(e)}")

    def _handle_add_items(self, order: Order):
        """Handle adding items to an order"""
        try:
            dialog = AddItemsDialog(self, order, self.menu_service)
            self.wait_window(dialog)

            if dialog.result:
                self.service.add_items(order.id, dialog.result)
                self.refresh()
        except Exception as e:
            logger.error(f"Error adding items to order: {e}")
            self.show_error("Error", f"Failed to add items: {str(e)}")

    def _handle_remove_item(self, order: Order, item_id: int):
        """Handle removing an item from an order"""
        if self.show_confirm(
            "Confirm Removal", "Are you sure you want to remove this item?"
        ):
            try:
                self.service.remove_item(order.id, item_id)
                self.refresh()
            except Exception as e:
                logger.error(f"Error removing item: {e}")
                self.show_error("Error", f"Failed to remove item: {str(e)}")

    def _handle_payment(self, order: Order):
        """Handle processing payment for an order"""
        dialog = PaymentDialog(self, order)
        self.wait_window(dialog)

        if dialog.result:
            try:
                self.service.process_payment(
                    order.id,
                    dialog.result["payment_method"],
                    dialog.result["amount_paid"],
                )
                self.refresh()
            except Exception as e:
                logger.error(f"Error processing payment: {e}")
                self.show_error("Error", f"Failed to process payment: {str(e)}")

    def _handle_cancel_order(self, order: Order):
        """Handle order cancellation"""
        if self.show_confirm(
            "Confirm Cancellation",
            f"Are you sure you want to cancel Order #{order.id}?",
        ):
            try:
                self.service.cancel_order(order.id)
                self.refresh()
            except Exception as e:
                logger.error(f"Error cancelling order: {e}")
                self.show_error("Error", f"Failed to cancel order: {str(e)}")

    def _handle_delete_order(self, order: Order):
        """Handle order deletion"""
        if self.show_confirm(
            "Confirm Deletion",
            f"Are you sure you want to delete Order #{order.id}? This action cannot be undone.",
        ):
            try:
                self.service.delete_order(order.id)
                self.refresh()
            except Exception as e:
                logger.error(f"Error deleting order: {e}")
                self.show_error("Error", f"Failed to delete order: {str(e)}")
