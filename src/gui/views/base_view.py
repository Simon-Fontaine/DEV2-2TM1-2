import customtkinter as ctk
from typing import Generic, TypeVar
from ...services.base_service import BaseService

T = TypeVar("T")


class BaseView(Generic[T], ctk.CTkFrame):
    """Base view class with common functionality"""

    def __init__(self, master: ctk.CTk, service: BaseService[T]):
        super().__init__(master)
        self.service = service
        self.initialize_ui()

    def initialize_ui(self):
        """Initialize the UI components - to be implemented by subclasses"""
        raise NotImplementedError

    def refresh(self):
        """Refresh the view - to be implemented by subclasses"""
        raise NotImplementedError

    def show_error(self, title: str, message: str):
        """Show error dialog"""
        from ..dialogs.message_dialog import CTkMessageDialog

        dialog = CTkMessageDialog(self, title, message)
        dialog.wait_window()

    def show_confirm(self, title: str, message: str) -> bool:
        """Show confirmation dialog"""
        from ..dialogs.message_dialog import CTkMessageDialog

        dialog = CTkMessageDialog(self, title, message, is_confirm=True)
        self.wait_window(dialog)
        return dialog.result
