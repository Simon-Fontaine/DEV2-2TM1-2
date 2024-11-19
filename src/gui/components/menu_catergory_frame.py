import logging
import customtkinter as ctk
from ...models.menu_item import MenuItemCategory

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
