import logging
import customtkinter as ctk
from ...models.order import Order
from ...models.menu_item import MenuItem, MenuItemCategory
from ...services.menu_item_service import MenuItemService
from .message_dialog import CTkMessageDialog

logger = logging.getLogger(__name__)


class AddItemsDialog(ctk.CTkToplevel):
    """Dialog for adding items to an existing order"""

    def __init__(self, parent, order: Order, menu_service: MenuItemService):
        super().__init__(parent)
        self.order = order
        self.menu_service = menu_service
        self.result = None

        self.title(f"Add Items to Order #{order.id}")
        self.geometry("600x500")

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Track selected items
        self.selected_items = {}  # menu_item_id -> quantity

        self.create_widgets()
        self.center_window()

    def create_widgets(self):
        """Initialize dialog widgets"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Search bar
        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        search_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            search_frame, text="Search Menu:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=5, pady=5)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search)

        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search menu items...",
            textvariable=self.search_var,
        )
        search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Split view for available and selected items
        content = ctk.CTkFrame(self)
        content.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # Available items
        available_frame = ctk.CTkFrame(content)
        available_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        available_frame.grid_rowconfigure(1, weight=1)
        available_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            available_frame, text="Available Items", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.available_items = ctk.CTkScrollableFrame(available_frame)
        self.available_items.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Selected items
        selected_frame = ctk.CTkFrame(content)
        selected_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        selected_frame.grid_rowconfigure(1, weight=1)
        selected_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            selected_frame, text="Selected Items", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.selected_list = ctk.CTkScrollableFrame(selected_frame)
        self.selected_list.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Bottom controls
        controls = ctk.CTkFrame(self)
        controls.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

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
            controls, text="Add Items", width=120, command=self.add_items
        ).pack(side="right", padx=5)

        # Initial load
        self._load_menu_items()

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

    def _add_item(self, item):
        """Add an item to the selected items"""
        if item.id in self.selected_items:
            self.selected_items[item.id]["quantity"] += 1
            self._update_selected_item_display(item)
        else:
            self.selected_items[item.id] = {"item": item, "quantity": 1, "notes": ""}
            self._create_selected_item_display(item)

        self._update_total()

    def _create_selected_item_display(self, item):
        """Create display for a newly selected item"""
        frame = ctk.CTkFrame(self.selected_list)
        frame.pack(fill="x", padx=5, pady=2)
        frame.item_id = item.id

        # Main info frame
        main_frame = ctk.CTkFrame(frame, fg_color="transparent")
        main_frame.pack(fill="x", expand=True)

        # Item info
        info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(info_frame, text=item.name, font=ctk.CTkFont(size=12)).pack(
            side="left", padx=5
        )

        # Quantity controls
        qty_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        qty_frame.pack(side="right", padx=5)

        # Decrease button
        ctk.CTkButton(
            qty_frame,
            text="-",
            width=30,
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
            command=lambda: self._change_quantity(item, 1),
        ).pack(side="left", padx=2)

        # Notes frame
        notes_frame = ctk.CTkFrame(frame, fg_color="transparent")
        notes_frame.pack(fill="x", padx=5, pady=(2, 0))

        ctk.CTkLabel(notes_frame, text="Notes:", font=ctk.CTkFont(size=11)).pack(
            side="left", padx=(20, 5)
        )

        notes_entry = ctk.CTkEntry(notes_frame)
        notes_entry.pack(side="left", fill="x", expand=True, padx=5)
        frame.notes_entry = notes_entry
        notes_entry.bind("<KeyRelease>", lambda e, i=item: self._update_notes(i))

    def _update_selected_item_display(self, item):
        """Update the display of a selected item"""
        for widget in self.selected_list.winfo_children():
            if hasattr(widget, "item_id") and widget.item_id == item.id:
                widget.qty_label.configure(
                    text=str(self.selected_items[item.id]["quantity"])
                )
                break

    def _change_quantity(self, item, delta):
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

    def _update_notes(self, item):
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

    def _on_search(self, *args):
        """Handle search input changes"""
        search_text = self.search_var.get().strip()
        self._load_menu_items(search_text)

    def add_items(self):
        """Add selected items to the order"""
        try:
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

            self.result = items_data
            self.destroy()

        except Exception as e:
            self._show_error("Error", str(e))

    def cancel(self):
        self.destroy()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _show_error(self, title: str, message: str):
        dialog = CTkMessageDialog(self, title, message)
        dialog.wait_window()
