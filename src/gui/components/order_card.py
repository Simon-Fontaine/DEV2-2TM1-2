import logging
import customtkinter as ctk
from ...models.order import Order, OrderStatus

logger = logging.getLogger(__name__)


class OrderCard(ctk.CTkFrame):
    """Card component for displaying an order"""

    def __init__(
        self,
        master,
        order: Order,
        on_status_change=None,
        on_add_items=None,
        on_remove_item=None,
        on_payment=None,
        on_cancel=None,
        on_delete=None,
    ):
        super().__init__(master)
        self.order = order
        self.on_status_change = on_status_change
        self.on_add_items = on_add_items
        self.on_remove_item = on_remove_item
        self.on_payment = on_payment
        self.on_cancel = on_cancel
        self.on_delete = on_delete

        self.grid_columnconfigure(1, weight=1)
        self.create_widgets()

    def create_widgets(self):
        """Create order card widgets with better visual separation"""
        # Main container with border and background
        self.configure(
            fg_color="#2d2d2d",
            corner_radius=6,
            border_width=1,
            border_color=self._get_border_color(),
        )

        # Header section with status indicator
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        header.grid_columnconfigure(2, weight=1)

        # Status indicator color
        status_color = self._get_status_color()
        self.indicator = ctk.CTkFrame(header, width=4, height=24, fg_color=status_color)
        self.indicator.pack(side="left", padx=(0, 10))

        # Order basic info with emphasized title
        info_text = f"Order #{self.order.id} - Table {self.order.table.number}"
        if self.order.customer:
            info_text += f"    Customer: {self.order.customer.name}"

        info_frame = ctk.CTkFrame(header, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        self.order_id_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff",
        )
        self.order_id_label.pack(side="left")

        status_tag = f"[{self.order.status.value}]"
        self.status_label = ctk.CTkLabel(
            info_frame,
            text=status_tag,
            font=ctk.CTkFont(size=12),
            text_color=status_color,
        )
        self.status_label.pack(side="left", padx=10)

        # Timestamps right-aligned
        time_frame = ctk.CTkFrame(header, fg_color="transparent")
        time_frame.pack(side="right")

        created_time = f"Created: {self.order.created_at.strftime('%H:%M:%S')}"
        self.created_time_label = ctk.CTkLabel(
            time_frame,
            text=created_time,
            font=ctk.CTkFont(size=12),
            text_color="#888888",
        )
        self.created_time_label.pack(side="right", padx=5)

        if self.order.updated_at and self.order.updated_at != self.order.created_at:
            updated_time = f"Updated: {self.order.updated_at.strftime('%H:%M:%S')}"
        else:
            updated_time = ""
        self.updated_time_label = ctk.CTkLabel(
            time_frame,
            text=updated_time,
            font=ctk.CTkFont(size=12),
            text_color="#888888",
        )
        self.updated_time_label.pack(side="right", padx=5)

        # Separator line
        separator = ctk.CTkFrame(self, height=1, fg_color="#3d3d3d")
        separator.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        # Items list with subtle background
        self.items_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.items_frame.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 5)
        )
        self._populate_items()

        # Bottom separator
        separator2 = ctk.CTkFrame(self, height=1, fg_color="#3d3d3d")
        separator2.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        # Controls and total section
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.grid(
            row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=5
        )
        self.actions_frame.grid_columnconfigure(1, weight=1)
        self._create_action_buttons()

    def _populate_items(self):
        """Populate the items list in the order card"""
        # Clear existing items
        for widget in self.items_frame.winfo_children():
            widget.destroy()

        # Add items
        for item in self.order.items:
            item_frame = ctk.CTkFrame(self.items_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=1)

            # Quantity and name
            text = f"{item.quantity}x {item.menu_item.name}"
            item_label = ctk.CTkLabel(
                item_frame,
                text=text,
                font=ctk.CTkFont(size=12),
                anchor="w",
                text_color="#dddddd",
            )
            item_label.pack(side="left", padx=(20, 5))

            # Right side container for price and delete button
            right_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            right_frame.pack(side="right", padx=5)

            # Price
            price_label = ctk.CTkLabel(
                right_frame,
                text=f"${item.get_subtotal():.2f}",
                font=ctk.CTkFont(size=12),
                text_color="#dddddd",
            )
            price_label.pack(side="left", padx=(0, 10))

            # Delete button - only show for pending/in-progress orders
            if self.order.status in [OrderStatus.PENDING, OrderStatus.IN_PROGRESS]:
                delete_button = ctk.CTkButton(
                    right_frame,
                    text="×",
                    width=24,
                    height=24,
                    fg_color="#e74c3c",
                    hover_color="#c0392b",
                    command=lambda i=item: self._on_remove_item(i.id),
                    font=ctk.CTkFont(size=14, weight="bold"),
                )
                delete_button.pack(side="right")

            if item.notes:
                notes_frame = ctk.CTkFrame(self.items_frame, fg_color="transparent")
                notes_frame.pack(fill="x")
                notes_label = ctk.CTkLabel(
                    notes_frame,
                    text=f"Note: {item.notes}",
                    font=ctk.CTkFont(size=11),
                    text_color="#888888",
                )
                notes_label.pack(side="left", padx=(40, 5))

    def _create_action_buttons(self):
        """Create or update action buttons based on order status"""
        # Clear existing buttons
        for widget in self.actions_frame.winfo_children():
            widget.destroy()

        # Left side - Status controls
        if self.order.status not in [OrderStatus.CANCELLED, OrderStatus.PAID]:
            left_controls = ctk.CTkFrame(self.actions_frame, fg_color="transparent")
            left_controls.grid(row=0, column=0, sticky="w")

            valid_statuses = self._get_valid_status_transitions()
            if valid_statuses:
                self.status_var = ctk.StringVar(value=self.order.status.value)
                status_menu = ctk.CTkOptionMenu(
                    left_controls,
                    values=valid_statuses,
                    variable=self.status_var,
                    command=self._on_status_change,
                    width=120,
                    height=28,
                )
                status_menu.pack(side="left", padx=5)

            if self.order.status in [OrderStatus.PENDING, OrderStatus.IN_PROGRESS]:
                add_items_button = ctk.CTkButton(
                    left_controls,
                    text="Add Items",
                    width=90,
                    height=28,
                    command=self._on_add_items,
                )
                add_items_button.pack(side="left", padx=5)

                cancel_button = ctk.CTkButton(
                    left_controls,
                    text="Cancel",
                    width=80,
                    height=28,
                    fg_color="#e74c3c",
                    hover_color="#c0392b",
                    command=self._on_cancel,
                )
                cancel_button.pack(side="left", padx=5)

        # Right side - Total and buttons
        right_controls = ctk.CTkFrame(self.actions_frame, fg_color="transparent")
        right_controls.grid(row=0, column=1, sticky="e")

        if self.order.is_paid:
            self.payment_status_label = ctk.CTkLabel(
                right_controls,
                text=f"Paid via {self.order.payment_method.value}",
                font=ctk.CTkFont(size=12),
                text_color="#2ecc71",
            )
            self.payment_status_label.pack(side="left", padx=10)
        else:
            self.payment_status_label = ctk.CTkLabel(right_controls, text="")
            self.payment_status_label.pack(side="left", padx=10)

        total_text = f"Total: ${self.order.total_amount:.2f}"
        self.total_label = ctk.CTkLabel(
            right_controls,
            text=total_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff",
        )
        self.total_label.pack(side="left", padx=10)

        if self.order.status == OrderStatus.COMPLETED and not self.order.is_paid:
            payment_button = ctk.CTkButton(
                right_controls,
                text="Process Payment",
                width=120,
                height=28,
                command=self._on_payment,
            )
            payment_button.pack(side="right", padx=5)

        if self.order.status in [OrderStatus.PENDING, OrderStatus.CANCELLED]:
            delete_button = ctk.CTkButton(
                right_controls,
                text="Delete",
                width=80,
                height=28,
                fg_color="#c0392b",
                hover_color="#992d22",
                command=self._on_delete,
            )
            delete_button.pack(side="right", padx=5)

    def _get_status_color(self) -> str:
        """Get color based on order status"""
        colors = {
            OrderStatus.PENDING: "#FFA726",  # Orange
            OrderStatus.IN_PROGRESS: "#42A5F5",  # Blue
            OrderStatus.COMPLETED: "#66BB6A",  # Green
            OrderStatus.CANCELLED: "#EF5350",  # Red
            OrderStatus.PAID: "#26A69A",  # Teal
        }
        return colors.get(self.order.status, "#9E9E9E")  # Default gray

    def _get_border_color(self) -> str:
        """Get border color based on status"""
        if self.order.is_paid:
            return "#1abc9c"  # Teal for paid orders
        elif self.order.status == OrderStatus.CANCELLED:
            return "#e74c3c"  # Red for cancelled
        return "#3d3d3d"  # Default subtle border

    def _get_valid_status_transitions(self) -> list:
        """Get valid status transitions based on current status"""
        transitions = {
            OrderStatus.PENDING: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED],
            OrderStatus.IN_PROGRESS: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
            OrderStatus.COMPLETED: [OrderStatus.PAID],
            OrderStatus.CANCELLED: [],
            OrderStatus.PAID: [],
        }
        valid_statuses = transitions.get(self.order.status, [])

        return [
            status.value for status in valid_statuses if status != self.order.status
        ]

    def _on_status_change(self, new_status: str):
        """Handle status change event"""
        new_status_enum = OrderStatus(new_status)
        if new_status_enum == self.order.status:
            return
        if self.on_status_change:
            self.on_status_change(self.order, new_status_enum)

    def _on_add_items(self):
        """Handle add items event"""
        if self.on_add_items:
            self.on_add_items(self.order)

    def _on_remove_item(self, item_id: int):
        """Handle remove item event"""
        if self.on_remove_item:
            self.on_remove_item(self.order, item_id)

    def _on_payment(self):
        """Handle payment event"""
        if self.on_payment:
            self.on_payment(self.order)

    def _on_cancel(self):
        """Handle cancel order event"""
        if self.on_cancel:
            self.on_cancel(self.order)

    def _on_delete(self):
        """Handle delete order event"""
        if self.on_delete:
            self.on_delete(self.order)

    def update_order(self, order: Order):
        """Update the card with new order data"""
        self.order = order

        # Update border and status colors
        self.configure(border_color=self._get_border_color())
        status_color = self._get_status_color()
        self.indicator.configure(fg_color=status_color)

        # Update Order ID and Customer Info
        info_text = f"Order #{self.order.id} - Table {self.order.table.number}"
        if self.order.customer:
            info_text += f"    Customer: {self.order.customer.name}"
        self.order_id_label.configure(text=info_text)

        # Update Status Tag
        status_tag = f"[{self.order.status.value}]"
        self.status_label.configure(text=status_tag, text_color=status_color)

        # Update Timestamps
        created_time = f"Created: {self.order.created_at.strftime('%H:%M:%S')}"
        self.created_time_label.configure(text=created_time)
        if self.order.updated_at and self.order.updated_at != self.order.created_at:
            updated_time = f"Updated: {self.order.updated_at.strftime('%H:%M:%S')}"
            self.updated_time_label.configure(text=updated_time)
        else:
            self.updated_time_label.configure(text="")

        # Update Items List
        self._populate_items()

        # Update Total Amount
        total_text = f"Total: ${self.order.total_amount:.2f}"
        self.total_label.configure(text=total_text)

        # Update Payment Status
        if self.order.is_paid:
            payment_text = f"Paid via {self.order.payment_method.value}"
            self.payment_status_label.configure(text=payment_text)
        else:
            self.payment_status_label.configure(text="")

        # Update Action Buttons
        self._create_action_buttons()
