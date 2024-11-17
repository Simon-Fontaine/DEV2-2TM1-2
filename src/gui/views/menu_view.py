import logging
from typing import Dict, List
import customtkinter as ctk
from ...models.menu_item import MenuItem, MenuItemCategory
from ...services.menu_item_service import MenuItemService
from .base_view import BaseView
from ..dialogs.menu_item_dialog import MenuItemDialog

logger = logging.getLogger(__name__)


class CategoryFrame(ctk.CTkFrame):
    """Frame for displaying menu items in a category"""

    def __init__(self, master, category: MenuItemCategory, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.category = category

        # Configure grid
        self.grid_columnconfigure(0, weight=1)

        # Category header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(
            header, text=category.value, font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        # Container for menu items
        self.items_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.items_frame.grid(row=1, column=0, sticky="ew")
        self.items_frame.grid_columnconfigure(0, weight=1)


class MenuItemCard(ctk.CTkFrame):
    """Card for displaying a menu item"""

    def __init__(
        self,
        master,
        item: MenuItem,
        on_edit=None,
        on_delete=None,
        on_availability_change=None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.item = item
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_availability_change = on_availability_change

        self.grid_columnconfigure(1, weight=1)
        self.create_widgets()

    def create_widgets(self):
        # Left section - Basic info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # Name and price
        ctk.CTkLabel(
            info_frame,
            text=f"{self.item.name}",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            info_frame,
            text=f"${self.item.price:.2f}",
            font=ctk.CTkFont(size=14),
        ).pack(side="left")

        # Middle section - Additional info
        details_frame = ctk.CTkFrame(self, fg_color="transparent")
        details_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        if self.item.description:
            ctk.CTkLabel(
                details_frame,
                text=self.item.description,
                wraplength=400,
            ).pack(side="left", padx=5)

        if self.item.allergens:
            ctk.CTkLabel(
                details_frame,
                text=f"Allergens: {self.item.allergens}",
                text_color="yellow",
            ).pack(side="right", padx=5)

        # Right section - Controls
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.grid(row=0, column=2, padx=10, pady=5, sticky="e")

        # Availability toggle
        self.avail_var = ctk.BooleanVar(value=self.item.is_available)
        ctk.CTkSwitch(
            controls_frame,
            text="Available",
            variable=self.avail_var,
            command=self._on_availability_change,
            width=100,
        ).pack(side="left", padx=5)

        # Edit button
        ctk.CTkButton(
            controls_frame,
            text="Edit",
            width=70,
            command=self._on_edit,
        ).pack(side="left", padx=5)

        # Delete button
        ctk.CTkButton(
            controls_frame,
            text="Delete",
            width=70,
            fg_color="red",
            hover_color="darkred",
            command=self._on_delete,
        ).pack(side="left", padx=5)

    def _on_edit(self):
        if self.on_edit:
            self.on_edit(self.item)

    def _on_delete(self):
        if self.on_delete:
            self.on_delete(self.item)

    def _on_availability_change(self):
        if self.on_availability_change:
            self.on_availability_change(self.item, self.avail_var.get())


class MenuView(BaseView[MenuItem]):
    """Main view for menu management"""

    def __init__(self, master: any, service: MenuItemService):
        self.category_frames: Dict[MenuItemCategory, CategoryFrame] = {}
        self.menu_items: Dict[int, MenuItem] = {}
        super().__init__(master, service)
        self.refresh()

    def initialize_ui(self):
        """Initialize the UI components"""
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_header()
        self._create_search_bar()
        self._create_menu_content()

    def _create_header(self):
        """Create header with title and buttons"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        header.grid_columnconfigure(2, weight=1)

        # Title
        ctk.CTkLabel(
            header,
            text="Menu Management",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=10)

        # Add Menu Item button
        ctk.CTkButton(
            header,
            text="Add Menu Item",
            width=120,
            command=self._handle_add_item,
        ).grid(row=0, column=1, padx=10, pady=10)

        # Refresh button
        ctk.CTkButton(
            header,
            text="Refresh",
            width=100,
            command=self.refresh,
        ).grid(row=0, column=2, padx=10, pady=10)

    def _create_search_bar(self):
        """Create search bar"""
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search)

        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search menu items...",
            textvariable=self.search_var,
        )
        search_entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

    def _create_menu_content(self):
        """Create scrollable content area with category sections"""
        # Container frame
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # Scrollable frame for menu items
        self.menu_frame = ctk.CTkScrollableFrame(container)
        self.menu_frame.grid(row=0, column=0, sticky="nsew")
        self.menu_frame.grid_columnconfigure(0, weight=1)

        # Create sections for each category
        for category in MenuItemCategory:
            frame = CategoryFrame(self.menu_frame, category)
            frame.grid(row=len(self.category_frames), column=0, sticky="ew", pady=10)
            self.category_frames[category] = frame

    def refresh(self, search_query: str = ""):
        """Refresh the menu items display"""
        try:
            # Clear existing menu items
            for frame in self.category_frames.values():
                for widget in frame.items_frame.winfo_children():
                    widget.destroy()
            self.menu_items.clear()

            # Get menu items (filtered if search query exists)
            items = (
                self.service.search_items(search_query)
                if search_query
                else self.service.get_all()
            )

            # Display items by category
            for item in items:
                if item.category in self.category_frames:
                    frame = self.category_frames[item.category].items_frame
                    card = MenuItemCard(
                        frame,
                        item,
                        on_edit=self._handle_edit_item,
                        on_delete=self._handle_delete_item,
                        on_availability_change=self._handle_availability_change,
                    )
                    card.grid(
                        row=len(frame.winfo_children()), column=0, sticky="ew", pady=2
                    )
                    self.menu_items[item.id] = item

            # Hide empty categories
            for category, frame in self.category_frames.items():
                if len(frame.items_frame.winfo_children()) == 0:
                    frame.grid_remove()
                else:
                    frame.grid()

        except Exception as e:
            logger.error(f"Error refreshing menu view: {e}")
            self.show_error("Error", f"Failed to refresh menu: {str(e)}")

    def _on_search(self, *args):
        """Handle search input changes"""
        search_text = self.search_var.get().strip()
        self.refresh(search_text)

    def _handle_add_item(self):
        """Handle adding a new menu item"""
        dialog = MenuItemDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            try:
                self.service.create(**dialog.result)
                self.refresh()
            except Exception as e:
                logger.error(f"Error creating menu item: {e}")
                self.show_error("Error", f"Failed to create menu item: {str(e)}")

    def _handle_edit_item(self, item: MenuItem):
        """Handle editing an existing menu item"""
        dialog = MenuItemDialog(self, title="Edit Menu Item", item=item)
        self.wait_window(dialog)

        if dialog.result:
            try:
                self.service.update(item.id, **dialog.result)
                self.refresh()
            except Exception as e:
                logger.error(f"Error updating menu item: {e}")
                self.show_error("Error", f"Failed to update menu item: {str(e)}")

    def _handle_delete_item(self, item: MenuItem):
        """Handle menu item deletion"""
        if self.show_confirm(
            "Confirm Deletion",
            f"Are you sure you want to delete {item.name} from the menu?",
        ):
            try:
                self.service.delete(item.id)
                self.refresh()
            except Exception as e:
                logger.error(f"Error deleting menu item: {e}")
                self.show_error("Error", f"Failed to delete menu item: {str(e)}")

    def _handle_availability_change(self, item: MenuItem, is_available: bool):
        """Handle menu item availability changes"""
        try:
            self.service.update_availability(item.id, is_available)
        except Exception as e:
            logger.error(f"Error updating item availability: {e}")
            self.show_error("Error", f"Failed to update item availability: {str(e)}")
