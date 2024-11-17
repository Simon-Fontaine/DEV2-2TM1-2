import logging
import customtkinter as ctk
from typing import Optional

from .message_dialog import CTkMessageDialog
from ...models.menu_item import MenuItem, MenuItemCategory

logger = logging.getLogger(__name__)


class MenuItemDialog(ctk.CTkToplevel):
    """Dialog for adding/editing menu items"""

    def __init__(self, parent, title="Add Menu Item", item=None):
        super().__init__(parent)

        self.title(title)
        self.geometry("500x600")

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Initialize result
        self.result = None
        self.item = item

        # Create form fields
        self.create_widgets()

        # Fill fields if editing
        if item:
            self.fill_fields(item)

        # Center the dialog
        self.center_window()

    def create_widgets(self):
        # Main form container
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Name field
        name_frame = self.create_field_frame(form_frame, "Name:")
        self.name_var = ctk.StringVar()
        self.name_entry = ctk.CTkEntry(name_frame, textvariable=self.name_var)
        self.name_entry.pack(side="right", expand=True, fill="x", padx=(10, 0))

        # Category field
        category_frame = self.create_field_frame(form_frame, "Category:")
        self.category_var = ctk.StringVar()
        self.category_menu = ctk.CTkOptionMenu(
            category_frame,
            values=[cat.value for cat in MenuItemCategory],
            variable=self.category_var,
        )
        self.category_menu.pack(side="right", expand=True, fill="x", padx=(10, 0))

        # Price field
        price_frame = self.create_field_frame(form_frame, "Price:")
        self.price_var = ctk.StringVar()
        self.price_entry = ctk.CTkEntry(price_frame, textvariable=self.price_var)
        self.price_entry.pack(side="right", expand=True, fill="x", padx=(10, 0))

        # Preparation time field
        prep_frame = self.create_field_frame(form_frame, "Prep Time:")
        self.prep_var = ctk.StringVar()
        prep_container = ctk.CTkFrame(prep_frame, fg_color="transparent")
        prep_container.pack(side="right", expand=True, fill="x", padx=(10, 0))

        self.prep_entry = ctk.CTkEntry(prep_container, textvariable=self.prep_var)
        self.prep_entry.pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(prep_container, text="minutes").pack(side="right", padx=(5, 0))

        # Description field
        desc_frame = self.create_field_frame(form_frame, "Description:")
        self.desc_text = ctk.CTkTextbox(desc_frame, height=100)
        self.desc_text.pack(side="right", expand=True, fill="both", padx=(10, 0))

        # Allergens field
        allergens_frame = self.create_field_frame(form_frame, "Allergens:")
        self.allergens_var = ctk.StringVar()
        self.allergens_entry = ctk.CTkEntry(
            allergens_frame, textvariable=self.allergens_var
        )
        self.allergens_entry.pack(side="right", expand=True, fill="x", padx=(10, 0))

        # Availability checkbox
        avail_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        avail_frame.pack(fill="x", pady=5)
        self.avail_var = ctk.BooleanVar(value=True)
        self.avail_check = ctk.CTkCheckBox(
            avail_frame, text="Available", variable=self.avail_var
        )
        self.avail_check.pack(side="left", padx=80)

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(button_frame, text="Cancel", command=self.cancel, width=100).pack(
            side="right", padx=5
        )
        ctk.CTkButton(button_frame, text="Save", command=self.save, width=100).pack(
            side="right", padx=5
        )

    def create_field_frame(self, parent, label_text: str) -> ctk.CTkFrame:
        """Create a frame for a form field with label"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text=label_text, width=80).pack(side="left")
        return frame

    def fill_fields(self, item: MenuItem):
        """Fill the form fields with menu item data"""
        self.name_var.set(item.name)
        self.category_var.set(item.category.value)
        self.price_var.set(f"{item.price:.2f}")
        self.prep_var.set(str(item.preparation_time))
        self.desc_text.delete("0.0", "end")
        if item.description:
            self.desc_text.insert("0.0", item.description)
        self.allergens_var.set(item.allergens or "")
        self.avail_var.set(item.is_available)

    def validate_and_get_data(self) -> Optional[dict]:
        """Validate form fields and return data if valid"""
        name = self.name_var.get().strip()
        if not name:
            raise ValueError("Name is required")

        try:
            price = float(self.price_var.get())
            if price < 0:
                raise ValueError()
        except ValueError:
            raise ValueError("Valid price is required")

        try:
            prep_time = int(self.prep_var.get())
            if prep_time < 0:
                raise ValueError()
        except ValueError:
            raise ValueError("Valid preparation time is required")

        return {
            "name": name,
            "category": MenuItemCategory(self.category_var.get()),
            "price": price,
            "description": self.desc_text.get("0.0", "end").strip() or None,
            "is_available": self.avail_var.get(),
            "preparation_time": prep_time,
            "allergens": self.allergens_var.get().strip() or None,
        }

    def save(self):
        try:
            data = self.validate_and_get_data()
            if data:
                self.result = data
                self.destroy()
        except ValueError as e:
            self._show_error("Validation Error", str(e))

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
