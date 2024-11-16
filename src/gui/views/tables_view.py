import logging
from typing import Dict
import customtkinter as ctk
from ...models.table import TableStatus, Table
from ...controllers.table_controller import TableController
from ..components.table_card import TableCard
from ..dialogs.table_dialog import TableDialog
from ..dialogs.message_dialog import CTkMessageDialog
from ...utils.colors import get_status_color


logger = logging.getLogger(__name__)


class TablesView(ctk.CTkFrame):
    def __init__(self, master: any, controller: TableController):
        super().__init__(master)
        self.controller = controller
        self.table_cards: Dict[int, TableCard] = {}
        self.status_counts: Dict[TableStatus, int] = {
            status: 0 for status in TableStatus
        }

        self.initialize_ui()
        self.refresh_tables()

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
            self.header, text="Refresh", width=100, command=self.refresh_tables
        ).grid(row=0, column=2, padx=10, pady=10)

    def _create_status_summary(self):
        """Create status summary display"""
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.status_indicators = {}
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

    def refresh_tables(self):
        """Refresh the tables display"""
        try:
            # Clear existing table cards
            for card in self.table_cards.values():
                card.destroy()
            self.table_cards.clear()

            # Reset status counts
            self.status_counts = {status: 0 for status in TableStatus}

            # Get and display tables
            tables = self.controller.get_all_tables()
            for idx, table in enumerate(tables):
                self._add_table_card(table, idx)
                self.status_counts[table.status] += 1

            # Update status indicators
            self._update_status_summary()

        except Exception as e:
            self._show_error("Error refreshing tables", str(e))

    def _add_table_card(self, table: Table, row: int):
        """Add a new table card to the display"""
        card = TableCard(
            self.tables_frame,
            table,
            on_status_change=self._handle_status_change,
            on_delete=self._handle_delete_table,
        )
        card.grid(row=row, column=0, padx=5, pady=5, sticky="ew")
        self.table_cards[table.id] = card

    def _update_status_summary(self):
        """Update the status count display"""
        for status, count in self.status_counts.items():
            self.status_indicators[status].configure(text=f"{status.value}: {count}")

    def _handle_status_change(self, table: Table, new_status: TableStatus):
        """Handle table status changes"""
        try:
            old_status = table.status
            self.controller.update_table_status(table.id, new_status)

            # Update counts
            self.status_counts[old_status] -= 1
            self.status_counts[new_status] += 1
            self._update_status_summary()

        except Exception as e:
            self._show_error("Error updating table status", str(e))
            # Revert the display
            if table.id in self.table_cards:
                self.table_cards[table.id].update_status_display()

    def _handle_add_table(self):
        """Handle adding a new table"""
        dialog = TableDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            try:
                # Create new table
                new_table = self.controller.create_table(
                    number=dialog.result["number"],
                    capacity=dialog.result["capacity"],
                    location=dialog.result["location"],
                )

                # Refresh display
                self.refresh_tables()

            except Exception as e:
                self._show_error("Error creating table", str(e))

    def _handle_delete_table(self, table: Table):
        """Handle table deletion"""
        try:
            dialog = CTkMessageDialog(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete Table {table.number}?",
                is_confirm=True,
            )
            self.wait_window(dialog)

            if dialog.result:
                self.controller.delete_table(table.id)
                self.refresh_tables()

        except Exception as e:
            self._show_error("Error deleting table", str(e))

    def _show_error(self, title: str, message: str):
        """Show error dialog"""
        dialog = CTkMessageDialog(self, title, message)
        dialog.wait_window()
