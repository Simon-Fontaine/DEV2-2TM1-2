import logging
import customtkinter as ctk

logger = logging.getLogger(__name__)


class CTkMessageDialog(ctk.CTkToplevel):
    """Custom dialog for messages and confirmations"""

    def __init__(self, parent, title: str, message: str, is_confirm: bool = False):
        super().__init__(parent)

        self.title(title)
        self.geometry("400x200")
        self.result = False

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Create widgets
        self.create_widgets(message, is_confirm)

        # Center the window
        self.center_window()

    def create_widgets(self, message: str, is_confirm: bool):
        # Message
        message_label = ctk.CTkLabel(
            self, text=message, wraplength=350  # Allow text wrapping
        )
        message_label.pack(pady=(20, 30), padx=20, expand=True)

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        if is_confirm:
            # Cancel button
            ctk.CTkButton(
                button_frame, text="Cancel", width=100, command=self.cancel
            ).pack(side="right", padx=5)

            # Confirm button
            ctk.CTkButton(
                button_frame,
                text="Confirm",
                width=100,
                command=self.confirm,
                fg_color="red",
                hover_color="darkred",
            ).pack(side="right", padx=5)
        else:
            # OK button
            ctk.CTkButton(
                button_frame, text="OK", width=100, command=self.confirm
            ).pack(side="right", padx=5)

    def confirm(self):
        self.result = True
        self.destroy()

    def cancel(self):
        self.result = False
        self.destroy()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
