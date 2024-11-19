import logging
import customtkinter as ctk
from typing import Dict, Optional, List, Tuple
from ...models.table import Table, TableStatus
from .base_view import BaseView
from ..dialogs.table_dialog import TableDialog
from ...services.table_service import TableService
from ..components.grid_cell import GridCell

logger = logging.getLogger(__name__)


class TablesView(BaseView[Table]):
    """Grid-based floor plan view for tables"""

    def __init__(self, master: any, service: TableService):
        # Define grid dimensions
        self.GRID_WIDTH = 7
        self.GRID_HEIGHT = 6
        self.CELL_SIZE = 100  # 100x100 pixels per cell

        self.cells: List[List[GridCell]] = []
        self.selected_table: Optional[Table] = None
        self.valid_moves: List[Tuple[int, int]] = []

        super().__init__(master, service)
        self.refresh()

    def initialize_ui(self):
        """Initialize the UI components"""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header with controls
        self._create_header()

        # Main content container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, minsize=300, weight=0)

        # Floor plan area (left side)
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Create the grid
        self._create_grid()

        # Details sidebar (right side)
        self.sidebar = ctk.CTkFrame(self.main_container, width=300)
        self.sidebar.grid(row=0, column=1, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(0, weight=1)

        # Create the details panel
        self._create_details_panel()

    def _create_header(self):
        """Create header with title and controls"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        header.grid_columnconfigure(2, weight=1)

        # Title
        ctk.CTkLabel(
            header,
            text="Floor Plan",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=10)

        # Grid table status label
        table_status = self.service.get_table_utilization()
        ctk.CTkLabel(
            header,
            text=f"{table_status["total"]} Tables | {table_status["available"]} Available | {table_status["occupied"]} Occupied | {table_status["reserved"]} Reserved | {table_status["maintenance"]} In maintenance | {table_status["cleaning"]} In cleaning",
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=1, padx=10, pady=10)

        # Controls
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.grid(row=0, column=2, sticky="e")

        ctk.CTkButton(
            controls, text="Add Table", width=120, command=self._handle_add_table
        ).pack(side="right", padx=5)

        ctk.CTkButton(controls, text="Refresh", width=100, command=self.refresh).pack(
            side="right", padx=5
        )

    def _create_grid(self):
        """Create the grid of cells"""
        self.grid_container = ctk.CTkFrame(self.content_frame)
        self.grid_container.grid(row=0, column=0, sticky="nsew")

        for i in range(self.GRID_WIDTH):
            self.grid_container.grid_columnconfigure(i, weight=1)
        for i in range(self.GRID_HEIGHT):
            self.grid_container.grid_rowconfigure(i, weight=1)

        self.cells = []
        for y in range(self.GRID_HEIGHT):
            row = []
            for x in range(self.GRID_WIDTH):
                cell = GridCell(
                    self.grid_container,
                    x,
                    y,
                    self.CELL_SIZE,
                    command=lambda x=x, y=y: self._handle_cell_click(x, y),
                )
                cell.grid(row=y, column=x, padx=1, pady=1)
                row.append(cell)
            self.cells.append(row)

    def _create_details_panel(self):
        """Create the details panel"""
        self.details_panel = ctk.CTkFrame(self.sidebar)
        self.details_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.details_panel.grid_columnconfigure(0, weight=1)

        # Empty state message
        self.empty_state_label = ctk.CTkLabel(
            self.details_panel,
            text="Select a table to view details",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        self.empty_state_label.grid(row=0, column=0, pady=20)

        # Title
        self.details_title_label = ctk.CTkLabel(
            self.details_panel,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.details_title_label.grid_remove()

        # Info section
        self.info_frame = ctk.CTkFrame(self.details_panel)
        self.info_frame.grid_columnconfigure(0, weight=1)
        self.info_frame.grid_remove()

        self.capacity_label = ctk.CTkLabel(self.info_frame)
        self.capacity_label.grid(row=0, column=0, pady=2)

        # Status section
        self.status_frame = ctk.CTkFrame(self.details_panel)
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_remove()

        ctk.CTkLabel(
            self.status_frame, text="Status:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, pady=2)

        self.status_var = ctk.StringVar()
        self.status_menu = ctk.CTkOptionMenu(
            self.status_frame,
            values=[status.value for status in TableStatus],
            variable=self.status_var,
            width=250,
            command=lambda s: self._handle_status_change(
                self.selected_table, TableStatus(s)
            ),
        )
        self.status_menu.grid(row=1, column=0, pady=2)

        # Actions section
        self.actions_frame = ctk.CTkFrame(self.details_panel)
        self.actions_frame.grid_columnconfigure(0, weight=1)
        self.actions_frame.grid_remove()

        # Edit button
        self.edit_button = ctk.CTkButton(
            self.actions_frame,
            text="Edit Table",
            width=250,
        )
        self.edit_button.grid(row=0, column=0, pady=2)

        # Delete button
        self.delete_button = ctk.CTkButton(
            self.actions_frame,
            text="Delete Table",
            fg_color="red",
            hover_color="darkred",
            width=250,
        )
        self.delete_button.grid(row=1, column=0, pady=2)

    def _update_details_panel(self, table: Table):
        """Update the details panel with selected table info"""
        # Hide empty state
        self.empty_state_label.grid_remove()

        # Update title
        self.details_title_label.configure(text=f"Table {table.number}")
        self.details_title_label.grid(row=0, column=0, pady=5, sticky="ew")

        # Update info section
        self.capacity_label.configure(text=f"Capacity: {table.capacity}")
        self.info_frame.grid(row=1, column=0, sticky="ew", pady=5)

        # Update status section
        self.status_var.set(table.status.value)
        self.status_frame.grid(row=2, column=0, sticky="ew", pady=5)

        # Update actions
        self.edit_button.configure(command=lambda: self._handle_edit_table(table))
        self.delete_button.configure(command=lambda: self._handle_delete_table(table))
        self.actions_frame.grid(row=3, column=0, sticky="ew", pady=10)

    def _get_valid_moves(self, table: Table) -> List[Tuple[int, int]]:
        """Get valid positions where the table can be moved"""
        valid = []
        for y in range(self.GRID_HEIGHT):
            for x in range(self.GRID_WIDTH):
                # Skip current table's position
                if table.grid_x == x and table.grid_y == y:
                    continue

                # Check if position is empty
                cell = self.cells[y][x]
                if not cell.table:
                    valid.append((x, y))
        return valid

    def _handle_cell_click(self, x: int, y: int):
        """Handle click on a grid cell"""
        cell = self.cells[y][x]

        if self.selected_table:
            # If a table is selected and we clicked a valid move target
            if (x, y) in self.valid_moves:
                try:
                    # Move table to new position
                    self.service.move_table(self.selected_table.id, x, y)
                    self.refresh()
                except Exception as e:
                    self.show_error("Error", f"Failed to move table: {str(e)}")

            # Clear selection and highlights
            self._clear_selection()

        elif cell.table:
            # Select table and show valid moves
            self.selected_table = cell.table
            cell.configure(border_color="#2196F3", border_width=2)

            # Calculate valid moves
            self.valid_moves = self._get_valid_moves(cell.table)
            for vx, vy in self.valid_moves:
                self.cells[vy][vx].highlight()

            # Show details
            self._update_details_panel(cell.table)

        else:
            # Clicked empty cell with no selection
            self._clear_selection()

    def _clear_selection(self):
        """Clear table selection and highlights"""
        self.selected_table = None
        self.valid_moves = []

        # Clear all highlights
        for row in self.cells:
            for cell in row:
                cell.highlight(False)
                if cell.table:
                    cell.configure(border_color="#3f3f3f", border_width=1)

        # Show empty state in details panel
        self.details_title_label.grid_remove()
        self.info_frame.grid_remove()
        self.status_frame.grid_remove()
        self.actions_frame.grid_remove()
        self.empty_state_label.grid()

    def refresh(self):
        """Refresh the floor plan view"""
        try:
            # Get all tables
            tables = self.service.get_all()

            # Create a mapping of positions to tables
            table_positions = {(table.grid_x, table.grid_y): table for table in tables}

            # Update cells
            for y in range(self.GRID_HEIGHT):
                for x in range(self.GRID_WIDTH):
                    cell = self.cells[y][x]
                    table = table_positions.get((x, y))
                    cell.set_table(table)

            # Clear any selection
            self._clear_selection()

        except Exception as e:
            logger.error(f"Error refreshing floor plan: {e}")
            self.show_error("Error", f"Failed to refresh floor plan: {str(e)}")

    def _handle_add_table(self):
        """Handle adding a new table"""
        # Find first empty cell
        empty_pos = None
        for y in range(self.GRID_HEIGHT):
            for x in range(self.GRID_WIDTH):
                if not self.cells[y][x].table:
                    empty_pos = (x, y)
                    break
            if empty_pos:
                break

        if not empty_pos:
            self.show_error("Error", "No empty cells available for new table")
            return

        dialog = TableDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            try:
                # Add grid position
                dialog.result["grid_x"] = empty_pos[0]
                dialog.result["grid_y"] = empty_pos[1]
                self.service.create(**dialog.result)
                self.refresh()
            except Exception as e:
                self.show_error("Error", f"Failed to create table: {str(e)}")

    def _handle_status_change(self, table: Table, new_status: TableStatus):
        """Handle table status changes"""
        try:
            updated_table = self.service.update_status(table.id, new_status)
            if updated_table:
                cell = self.cells[table.grid_y][table.grid_x]
                cell.set_table(updated_table)

        except Exception as e:
            self.show_error("Error", f"Failed to update table status: {str(e)}")

    def _handle_edit_table(self, table: Table):
        """Handle editing a table"""
        dialog = TableDialog(self, title="Edit Table", table=table)
        self.wait_window(dialog)

        if dialog.result:
            try:
                # Preserve grid position
                dialog.result["grid_x"] = table.grid_x
                dialog.result["grid_y"] = table.grid_y
                self.service.update(table.id, **dialog.result)
                self.refresh()
            except Exception as e:
                self.show_error("Error", f"Failed to update table: {str(e)}")

    def _handle_delete_table(self, table: Table):
        """Handle deleting a table"""
        if self.show_confirm(
            "Confirm Deletion", f"Are you sure you want to delete Table {table.number}?"
        ):
            try:
                self.service.delete(table.id)
                self.refresh()
                self._clear_selection()  # Clear selection after deletion
            except Exception as e:
                self.show_error("Error", f"Failed to delete table: {str(e)}")
