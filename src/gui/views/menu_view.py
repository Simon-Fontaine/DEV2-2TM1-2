import logging
from typing import Dict, Optional
import customtkinter as ctk
from ...models.menu_item import MenuItem, MenuItemCategory
from ...services.menu_item_service import MenuItemService
from .base_view import BaseView
from ..dialogs.menu_item_dialog import MenuItemDialog
from ..components.menu_card import MenuItemCard
from ..components.menu_catergory_frame import CategoryFrame

logger = logging.getLogger(__name__)


class MenuView(BaseView[MenuItem]):
    """Main view for menu management"""

    def __init__(self, master: any, service: MenuItemService):
        self.category_frames: Dict[MenuItemCategory, CategoryFrame] = {}
        self.menu_item_cards: Dict[int, MenuItemCard] = {}
        super().__init__(master, service)

    def initialize_ui(self):
        """Initialize the UI components"""
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_header()
        self._create_search_bar()
        self._create_menu_content()

        self.refresh()

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
            # Get menu items (filtered if search query exists)
            items = (
                self.service.search_items(search_query)
                if search_query
                else self.service.get_all()
            )

            # Clear previous grid placements
            for card in self.menu_item_cards.values():
                card.grid_remove()

            # Prepare to track which items are displayed
            displayed_item_ids = set()

            # Prepare to track row indices for each category
            category_row_indices = {
                category: 0 for category in self.category_frames.keys()
            }

            # Display items by category
            for item in items:
                displayed_item_ids.add(item.id)
                if item.category in self.category_frames:
                    frame = self.category_frames[item.category].items_frame
                    row_index = category_row_indices[item.category]

                    if item.id in self.menu_item_cards:
                        # Update existing card
                        card = self.menu_item_cards[item.id]
                        card.update_item(item)
                    else:
                        # Create new card
                        card = MenuItemCard(
                            frame,
                            item,
                            on_edit=self._handle_edit_item,
                            on_delete=self._handle_delete_item,
                            on_availability_change=self._handle_availability_change,
                        )
                        self.menu_item_cards[item.id] = card

                    # Grid the card at the correct position
                    card.grid(row=row_index, column=0, sticky="ew", pady=2)

                    # Increment row index for this category
                    category_row_indices[item.category] += 1
                else:
                    logger.warning(f"Unknown category: {item.category}")

            # Hide cards that are not in the current items
            for item_id, card in self.menu_item_cards.items():
                if item_id not in displayed_item_ids:
                    card.grid_remove()

            # Hide empty categories
            for category, frame in self.category_frames.items():
                if category_row_indices[category] == 0:
                    # No items displayed in this category
                    frame.grid_remove()
                else:
                    frame.grid()

        except Exception as e:
            logger.error(f"Error refreshing menu view: {e}")
            self.show_error("Error", f"Failed to refresh menu: {str(e)}")

    def _on_search(self, *args):
        """Handle search input changes with debounce."""
        if hasattr(self, "_search_after_id"):
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, self._perform_search)

    def _perform_search(self):
        """Execute the search after debounce period"""
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
