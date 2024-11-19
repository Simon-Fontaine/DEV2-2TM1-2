import logging
import customtkinter as ctk
from ...models.menu_item import MenuItem

logger = logging.getLogger(__name__)


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
        self.name_label = ctk.CTkLabel(
            info_frame,
            text=f"{self.item.name}",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.name_label.pack(side="left", padx=(0, 10))

        self.price_label = ctk.CTkLabel(
            info_frame,
            text=f"${self.item.price:.2f}",
            font=ctk.CTkFont(size=14),
        )
        self.price_label.pack(side="left")

        # Middle section - Additional info
        details_frame = ctk.CTkFrame(self, fg_color="transparent")
        details_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        self.description_label = ctk.CTkLabel(
            details_frame,
            text=self.item.description or "",
            wraplength=400,
        )
        self.description_label.pack(side="left", padx=5)

        self.allergens_label = ctk.CTkLabel(
            details_frame,
            text=f"Allergens: {self.item.allergens}" if self.item.allergens else "",
            text_color="yellow",
        )
        self.allergens_label.pack(side="right", padx=5)

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

    def update_item(self, item: MenuItem):
        """Update the card with new item data"""
        self.item = item
        self.name_label.configure(text=f"{item.name}")
        self.price_label.configure(text=f"${item.price:.2f}")
        self.description_label.configure(text=item.description or "")
        self.allergens_label.configure(
            text=f"Allergens: {item.allergens}" if item.allergens else ""
        )
        self.avail_var.set(item.is_available)

    def _on_edit(self):
        if self.on_edit:
            self.on_edit(self.item)

    def _on_delete(self):
        if self.on_delete:
            self.on_delete(self.item)

    def _on_availability_change(self):
        if self.on_availability_change:
            self.on_availability_change(self.item, self.avail_var.get())
