import logging
from typing import Dict
import customtkinter as ctk

from .base_view import BaseView
from ...models.table import TableStatus, Table
from ...services.table_service import TableService
from ..dialogs.table_dialog import TableDialog
from ..components.table_card import TableCard
from ...utils.colors import get_status_color

logger = logging.getLogger(__name__)


class TablesView(BaseView[Table]):
    def __init__(self, master: any, service: TableService):
        self.table_cards: Dict[int, TableCard] = {}
        self.status_indicators: Dict[TableStatus, ctk.CTkLabel] = {}
        super().__init__(master, service)
        self.refresh()

    def initialize_ui(self):
        """Initialize the UI components"""
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_header()
        self._create_status_summary()
        self._create_tables_area()

    def _create_header(self):
        """Create header with title and buttons"""
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        self.header.grid_columnconfigure(3, weight=1)

        # Title
        ctk.CTkLabel(
            self.header,
            text="Tables Management",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=10)

        # Buttons
        ctk.CTkButton(
            self.header, text="Add Table", width=100, command=self._handle_add_table
        ).grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkButton(
            self.header, text="Refresh", width=100, command=self.refresh
        ).grid(row=0, column=2, padx=10, pady=10)

    def _create_status_summary(self):
        """Create status summary display"""
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        # Initialize status indicators for each TableStatus
        for idx, status in enumerate(TableStatus):
            label = ctk.CTkLabel(
                self.status_frame,
                text=f"{status.value}: 0",
                fg_color=get_status_color(status),
                corner_radius=6,
                padx=10,
            )
            label.grid(row=0, column=idx, padx=5, pady=5)
            self.status_indicators[status] = label

    def _create_tables_area(self):
        """Create scrollable area for table cards"""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.tables_frame = ctk.CTkScrollableFrame(container)
        self.tables_frame.grid(row=0, column=0, sticky="nsew")
        self.tables_frame.grid_columnconfigure(0, weight=1)

    def _add_table_card(self, table: Table, row: int):
        """Add a new table card to the display"""
        card = TableCard(
            self.tables_frame,
            table,
            on_status_change=self._handle_status_change,
            on_delete=self._handle_delete_table,
            on_edit=self._handle_edit_table,
        )
        card.grid(row=row, column=0, padx=5, pady=5, sticky="ew")
        self.table_cards[table.id] = card

    def _update_status_summary(self, status_counts: dict):
        """Update the status count display"""
        try:
            for status in TableStatus:
                count = status_counts.get(status.value, 0)
                if status in self.status_indicators:
                    self.status_indicators[status].configure(
                        text=f"{status.value}: {count}"
                    )
        except Exception as e:
            logger.error(f"Error updating status summary: {e}")
            self.show_error("Error", f"Failed to update status summary: {str(e)}")

    def _handle_status_change(self, table: Table, new_status: TableStatus):
        """Handle table status changes"""
        try:
            updated_table = self.service.update_status(table.id, new_status)

            if updated_table:
                self.refresh()
            else:
                self.show_error(
                    "Error", f"Failed to update status for Table {table.number}"
                )
                if table.id in self.table_cards:
                    card = self.table_cards[table.id]
                    if not card.is_destroyed and card.winfo_exists():
                        card.status_var.set(table.status.value)
                        card.update_status_display()

        except Exception as e:
            logger.error(f"Error handling status change: {e}")
            self.show_error("Error updating table status", str(e))

            if table.id in self.table_cards:
                card = self.table_cards[table.id]
                if not card.is_destroyed and card.winfo_exists():
                    card.status_var.set(table.status.value)
                    card.update_status_display()

    def _handle_add_table(self):
        """Handle adding a new table"""
        dialog = TableDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            try:
                self.service.create(**dialog.result)
                self.refresh()
            except ValueError as e:
                self.show_error("Duplicate Table Number", str(e))
            except Exception as e:
                self.show_error("Error creating table", str(e))

    def _handle_edit_table(self, table: Table):
        """Handle editing an existing table"""
        dialog = TableDialog(self, title="Edit Table", table=table)
        self.wait_window(dialog)

        if dialog.result:
            try:
                self.service.update(table.id, **dialog.result)
                self.refresh()
            except ValueError as e:
                self.show_error("Validation Error", str(e))
            except Exception as e:
                self.show_error("Error updating table", str(e))

    def _handle_delete_table(self, table: Table):
        """Handle table deletion"""
        if self.show_confirm(
            "Confirm Deletion", f"Are you sure you want to delete Table {table.number}?"
        ):
            try:
                self.service.delete(table.id)
                self.refresh()
            except Exception as e:
                self.show_error("Error deleting table", str(e))

    def refresh(self):
        """Refresh the tables display"""
        try:
            # Clear existing table cards
            for card in self.table_cards.values():
                card.destroy()
            self.table_cards.clear()

            # Get and display tables
            tables = self.service.get_all()
            for idx, table in enumerate(tables):
                self._add_table_card(table, idx)

            # Update status indicators
            status_counts = self.service.get_status_counts()
            self._update_status_summary(status_counts)

        except Exception as e:
            self.show_error("Error refreshing tables", str(e))
