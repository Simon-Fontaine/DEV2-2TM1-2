import logging
import customtkinter as ctk
from typing import Optional
from ...services.table_service import TableService
from ...services.customer_service import CustomerService
from ...services.menu_item_service import MenuItemService
from ...models.menu_item import MenuItem, MenuItemCategory
from ...models.customer import Customer
from .message_dialog import CTkMessageDialog

logger = logging.getLogger(__name__)


class NewOrderDialog(ctk.CTkToplevel):
    """Dialog for creating a new order"""

    def __init__(self, parent, table_service, customer_service, menu_service):
        super().__init__(parent)
        self.table_service = table_service
        self.customer_service = customer_service
        self.menu_service = menu_service
        self.result = None
        self.selected_customer: Optional[Customer] = None

        self.title("New Order")
        self.geometry("800x600")

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Track selected items
        self.selected_items = {}  # menu_item_id -> quantity

        self.create_widgets()
        self.center_window()

    def create_widgets(self):
        # Configure main grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Top section: Table and Customer selection
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(
            row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew"
        )
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_columnconfigure(3, weight=1)

        # Table selection
        ctk.CTkLabel(
            top_frame, text="Select Table:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=(10, 5), pady=5)

        # Get available tables
        tables = [t for t in self.table_service.get_all() if t.status == "Available"]
        table_options = [f"Table {t.number} ({t.capacity} seats)" for t in tables]

        self.table_var = ctk.StringVar()
        self.table_menu = ctk.CTkOptionMenu(
            top_frame, values=table_options, variable=self.table_var, width=150
        )
        self.table_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Customer selection
        ctk.CTkLabel(top_frame, text="Customer:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=2, padx=(10, 5), pady=5
        )

        self.customer_search = ctk.StringVar()
        self.customer_search.trace_add("write", self._on_customer_search)

        self.customer_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="Search customers...",
            textvariable=self.customer_search,
            width=200,
        )
        self.customer_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # Customer search results
        self.customer_results = ctk.CTkScrollableFrame(top_frame, height=80)
        self.customer_results.grid(
            row=1, column=2, columnspan=2, padx=5, pady=(0, 5), sticky="ew"
        )

        # Menu items search
        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        search_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            search_frame, text="Search Menu:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=5, pady=5)

        self.items_search = ctk.StringVar()
        self.items_search.trace_add("write", self._on_items_search)

        ctk.CTkEntry(
            search_frame,
            placeholder_text="Search menu items...",
            textvariable=self.items_search,
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Split view container
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(
            row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew"
        )
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Available items (left side)
        available_frame = ctk.CTkFrame(content_frame)
        available_frame.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="nsew")
        available_frame.grid_rowconfigure(1, weight=1)
        available_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            available_frame,
            text="Available Items",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.available_items = ctk.CTkScrollableFrame(available_frame)
        self.available_items.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Selected items (right side)
        selected_frame = ctk.CTkFrame(content_frame)
        selected_frame.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="nsew")
        selected_frame.grid_rowconfigure(1, weight=1)
        selected_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            selected_frame,
            text="Selected Items",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.selected_list = ctk.CTkScrollableFrame(selected_frame)
        self.selected_list.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Bottom controls
        controls = ctk.CTkFrame(self)
        controls.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # Total
        self.total_label = ctk.CTkLabel(
            controls, text="Total: $0.00", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.total_label.pack(side="left", padx=10)

        # Buttons
        ctk.CTkButton(controls, text="Cancel", width=100, command=self.cancel).pack(
            side="right", padx=5
        )

        ctk.CTkButton(
            controls, text="Create Order", width=120, command=self.create_order
        ).pack(side="right", padx=5)

        # Initial load
        self._load_menu_items()

    def _create_category_section(self, category: MenuItemCategory) -> ctk.CTkFrame:
        """Create a section for a menu category"""
        frame = ctk.CTkFrame(self.available_items, fg_color="transparent")
        frame.pack(fill="x", pady=(10, 0))

        # Category label
        ctk.CTkLabel(
            frame,
            text=category.value,
            font=ctk.CTkFont(weight="bold", size=13),
            anchor="w",
        ).pack(fill="x", padx=10, pady=5)

        return frame

    def _create_menu_item_row(self, parent: ctk.CTkFrame, item: MenuItem):
        """Create a menu item row with bullet point"""
        item_frame = ctk.CTkFrame(parent, fg_color="transparent")
        item_frame.pack(fill="x")

        # Bullet point and name
        ctk.CTkLabel(item_frame, text="•", font=ctk.CTkFont(size=12), width=20).pack(
            side="left", padx=(20, 0)
        )

        ctk.CTkLabel(
            item_frame, text=item.name, font=ctk.CTkFont(size=12), anchor="w"
        ).pack(side="left", padx=5, fill="x", expand=True)

        # Price
        ctk.CTkLabel(
            item_frame, text=f"${item.price:.2f}", font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=10)

        # Add button
        ctk.CTkButton(
            item_frame,
            text="+",
            width=30,
            height=24,
            command=lambda i=item: self._add_item(i),
        ).pack(side="right", padx=10)

    def _load_menu_items(self, search_text: str = ""):
        """Load menu items into the available items list"""
        # Clear existing items
        for widget in self.available_items.winfo_children():
            widget.destroy()

        # Get items
        items = (
            self.menu_service.search_items(search_text)
            if search_text
            else self.menu_service.get_available_items()
        )

        # Group items by category
        categorized_items = {}
        for item in items:
            if item.category not in categorized_items:
                categorized_items[item.category] = []
            categorized_items[item.category].append(item)

        # Display items by category
        for category in MenuItemCategory:
            if category in categorized_items and categorized_items[category]:
                category_frame = self._create_category_section(category)

                # Create rows for each item in category
                for item in sorted(categorized_items[category], key=lambda x: x.name):
                    if item.is_available:
                        self._create_menu_item_row(category_frame, item)

    def _create_selected_item_display(self, item: MenuItem):
        """Create display for a selected item"""
        frame = ctk.CTkFrame(self.selected_list, fg_color="transparent")
        frame.pack(fill="x", padx=5, pady=2)
        frame.item_id = item.id

        # Item info
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            info_frame,
            text=f"{item.name} (${item.price:.2f})",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=5)

        # Quantity controls
        qty_frame = ctk.CTkFrame(frame, fg_color="transparent")
        qty_frame.pack(side="right", padx=5)

        # Decrease button
        ctk.CTkButton(
            qty_frame,
            text="-",
            width=30,
            height=24,
            command=lambda: self._change_quantity(item, -1),
        ).pack(side="left", padx=2)

        # Quantity label
        label = ctk.CTkLabel(qty_frame, text="1", width=30)
        label.pack(side="left", padx=2)
        frame.qty_label = label

        # Increase button
        ctk.CTkButton(
            qty_frame,
            text="+",
            width=30,
            height=24,
            command=lambda: self._change_quantity(item, 1),
        ).pack(side="left", padx=2)

        # Notes
        notes_frame = ctk.CTkFrame(frame, fg_color="transparent")
        notes_frame.pack(fill="x", padx=5, pady=(2, 0))

        notes_entry = ctk.CTkEntry(notes_frame, placeholder_text="Notes...", height=24)
        notes_entry.pack(fill="x", padx=(20, 5))
        frame.notes_entry = notes_entry
        notes_entry.bind("<KeyRelease>", lambda e, i=item: self._update_notes(i))

    def _on_customer_search(self, *args):
        """Handle customer search"""
        search_text = self.customer_search.get().strip()

        # Clear previous results
        for widget in self.customer_results.winfo_children():
            widget.destroy()

        if search_text:
            customers = self.customer_service.search_customers(search_text)

            for customer in customers:
                customer_frame = ctk.CTkFrame(
                    self.customer_results, fg_color="transparent"
                )
                customer_frame.pack(fill="x", padx=2, pady=1)

                ctk.CTkLabel(
                    customer_frame,
                    text=f"{customer.name} ({customer.phone})",
                    font=ctk.CTkFont(size=12),
                ).pack(side="left", padx=5)

                ctk.CTkButton(
                    customer_frame,
                    text="Select",
                    width=60,
                    height=24,
                    command=lambda c=customer: self._select_customer(c),
                ).pack(side="right", padx=5)

    def _select_customer(self, customer: Customer):
        """Handle customer selection"""
        self.selected_customer = customer
        self.customer_search.set(f"{customer.name} ({customer.phone})")

        # Clear customer list
        for widget in self.customer_results.winfo_children():
            widget.destroy()

    def _add_item(self, item: MenuItem):
        """Add an item to the selected items"""
        if item.id in self.selected_items:
            self.selected_items[item.id]["quantity"] += 1
            self._update_selected_item_display(item)
        else:
            self.selected_items[item.id] = {"item": item, "quantity": 1, "notes": ""}
            self._create_selected_item_display(item)

        self._update_total()

    def _update_selected_item_display(self, item: MenuItem):
        """Update the display of a selected item"""
        for widget in self.selected_list.winfo_children():
            if hasattr(widget, "item_id") and widget.item_id == item.id:
                widget.qty_label.configure(
                    text=str(self.selected_items[item.id]["quantity"])
                )
                break

    def _change_quantity(self, item: MenuItem, delta: int):
        """Change the quantity of a selected item"""
        if item.id in self.selected_items:
            new_qty = self.selected_items[item.id]["quantity"] + delta

            if new_qty <= 0:
                # Remove item
                self.selected_items.pop(item.id)
                for widget in self.selected_list.winfo_children():
                    if hasattr(widget, "item_id") and widget.item_id == item.id:
                        widget.destroy()
                        break
            else:
                # Update quantity
                self.selected_items[item.id]["quantity"] = new_qty
                self._update_selected_item_display(item)

            self._update_total()

    def _update_notes(self, item: MenuItem):
        """Update notes for an item"""
        for widget in self.selected_list.winfo_children():
            if hasattr(widget, "item_id") and widget.item_id == item.id:
                self.selected_items[item.id]["notes"] = widget.notes_entry.get()
                break

    def _update_total(self):
        """Update the total amount display"""
        total = sum(
            data["item"].price * data["quantity"]
            for data in self.selected_items.values()
        )
        self.total_label.configure(text=f"Total: ${total:.2f}")

    def _on_items_search(self, *args):
        """Handle menu items search"""
        search_text = self.items_search.get().strip()
        self._load_menu_items(search_text)

    def create_order(self):
        """Create the order with selected items"""
        try:
            # Validate table selection
            table_str = self.table_var.get()
            if not table_str:
                self._show_error("Error", "Please select a table")
                return

            # Extract table number
            import re

            table_num = int(re.search(r"Table (\d+)", table_str).group(1))
            table = self.table_service.get_by_number(table_num)

            if not table:
                self._show_error("Error", "Invalid table selected")
                return

            # Validate items
            if not self.selected_items:
                self._show_error("Error", "Please select at least one item")
                return

            # Prepare items data
            items_data = [
                {
                    "menu_item_id": item_id,
                    "quantity": data["quantity"],
                    "notes": data["notes"].strip() or None,
                }
                for item_id, data in self.selected_items.items()
            ]

            # Prepare result
            self.result = {
                "table_id": table.id,
                "customer_id": getattr(self.selected_customer, "id", None),
                "items": items_data,
            }

            self.destroy()

        except Exception as e:
            self._show_error("Error", str(e))

    def cancel(self):
        self.destroy()

    def center_window(self):
        """Center the dialog on the screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _show_error(self, title: str, message: str):
        """Show error dialog"""
        dialog = CTkMessageDialog(self, title, message)
        dialog.wait_window()
