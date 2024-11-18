import logging
import customtkinter as ctk
from typing import Dict, Optional, List, Tuple
from ...models.table import Table, TableStatus
from .base_view import BaseView
from ..dialogs.table_dialog import TableDialog
from ...services.table_service import TableService
from ...utils.colors import get_status_color

logger = logging.getLogger(__name__)


class GridCell(ctk.CTkFrame):
    """A single cell in the grid"""

    def __init__(self, master, grid_x: int, grid_y: int, size: int = 100, **kwargs):
        super().__init__(
            master,
            width=size,
            height=size,
            fg_color="transparent",
            border_width=1,
            border_color="#3f3f3f",
            **kwargs,
        )

        self.grid_x = grid_x
        self.grid_y = grid_y
        self.size = size
        self.table = None

        # Make the cell non-expandable
        self.grid_propagate(False)

    def set_table(self, table: Optional[Table]):
        """Set or remove table from this cell"""
        self.table = table

        # Clear existing contents
        for widget in self.winfo_children():
            widget.destroy()

        if table:
            # Create table display
            self.configure(fg_color=get_status_color(table.status))

            # Table number
            ctk.CTkLabel(
                self,
                text=f"Table {table.number}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="white",
            ).place(relx=0.5, rely=0.3, anchor="center")

            # Capacity
            ctk.CTkLabel(
                self,
                text=f"{table.capacity} seats",
                font=ctk.CTkFont(size=12),
                text_color="white",
            ).place(relx=0.5, rely=0.7, anchor="center")
        else:
            self.configure(fg_color="transparent")

    def highlight(self, highlight: bool = True):
        """Highlight cell as a valid move target"""
        if highlight:
            self.configure(border_color="#4CAF50", border_width=2)
        else:
            self.configure(border_color="#3f3f3f", border_width=1)


class TablesView(BaseView[Table]):
    """Grid-based floor plan view for tables"""

    def __init__(self, master: any, service: TableService):
        self.GRID_SIZE = 6  # 6x6 grid
        self.CELL_SIZE = 100  # 100x100 pixels per cell

        self.cells: List[List[GridCell]] = []
        self.selected_table: Optional[Table] = None
        self.valid_moves: List[Tuple[int, int]] = []

        super().__init__(master, service)
        self.refresh()

    def initialize_ui(self):
        """Initialize the UI components"""
        self.grid_rowconfigure(1, weight=1)  # Main content row expands
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        header.grid_columnconfigure(2, weight=1)

        # Title
        ctk.CTkLabel(
            header,
            text="Tables Management",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=10)

        # Controls
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.grid(row=0, column=2, sticky="e")

        ctk.CTkButton(
            controls, text="Add Table", width=120, command=self._handle_add_table
        ).pack(side="right", padx=5)

        ctk.CTkButton(controls, text="Refresh", width=100, command=self.refresh).pack(
            side="right", padx=5
        )

        # Main content container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Configure columns with fixed width for sidebar
        self.main_container.grid_columnconfigure(0, weight=1)  # Grid area expands
        self.main_container.grid_columnconfigure(
            1, minsize=300, weight=0
        )  # Fixed width sidebar

        # Floor plan area (left side)
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Create the grid
        self._create_grid()

        # Details sidebar (right side) - always visible with fixed width
        self.sidebar = ctk.CTkFrame(self.main_container, width=300)
        self.sidebar.grid(row=0, column=1, sticky="nsew")
        self.sidebar.grid_propagate(False)  # Prevent sidebar from shrinking
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(0, weight=1)

        # Create empty details panel
        self._create_empty_details()

    def _create_empty_details(self):
        """Create empty details panel to maintain layout"""
        # First destroy existing panel if it exists
        if hasattr(self, "details_panel"):
            self.details_panel.destroy()

        # Create new panel with fixed width
        self.details_panel = ctk.CTkFrame(self.sidebar)
        self.details_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Configure panel grid
        self.details_panel.grid_columnconfigure(0, weight=1)
        self.details_panel.grid_rowconfigure(0, weight=1)

        # Empty state message in center
        ctk.CTkLabel(
            self.details_panel,
            text="Select a table to view details",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).grid(row=0, column=0, pady=20)

    def _create_header(self):
        """Create header with title and controls"""
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        header.grid_columnconfigure(2, weight=1)

        # Title
        ctk.CTkLabel(
            header,
            text="Floor Plan",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=10)

        # Controls
        controls = ctk.CTkFrame(header)
        controls.grid(row=0, column=2, sticky="e")

        ctk.CTkButton(controls, text="Add Table", command=self._handle_add_table).pack(
            side="right", padx=5
        )

        ctk.CTkButton(controls, text="Refresh", command=self.refresh).pack(
            side="right", padx=5
        )

    def _create_grid(self):
        """Create the grid of cells"""
        # Container for the grid
        self.grid_container = ctk.CTkFrame(self.content_frame)
        self.grid_container.grid(row=0, column=0, sticky="nsew")

        # Configure grid container to center the grid
        for i in range(self.GRID_SIZE):
            self.grid_container.grid_columnconfigure(i, weight=1)
            self.grid_container.grid_rowconfigure(i, weight=1)

        # Create cells
        for y in range(self.GRID_SIZE):
            row = []
            for x in range(self.GRID_SIZE):
                cell = GridCell(self.grid_container, x, y, self.CELL_SIZE)
                cell.grid(row=y, column=x, padx=1, pady=1)
                cell.bind(
                    "<Button-1>", lambda e, x=x, y=y: self._handle_cell_click(x, y)
                )
                row.append(cell)
            self.cells.append(row)

    def _create_details_panel(self):
        """Create the details panel for selected table"""
        self.details_panel = ctk.CTkFrame(self)
        self.details_panel.grid(row=1, column=1, padx=10, pady=5, sticky="n")
        self.details_panel.grid_columnconfigure(0, weight=1)

        # Initially hide the panel
        self.details_panel.grid_remove()

    def _update_details_panel(self, table: Table):
        """Update the details panel with selected table info"""
        # First destroy existing panel
        if hasattr(self, "details_panel"):
            self.details_panel.destroy()

        # Create new panel with fixed width
        self.details_panel = ctk.CTkFrame(self.sidebar)
        self.details_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Configure panel grid
        self.details_panel.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            self.details_panel,
            text=f"Table {table.number}",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, pady=5, sticky="ew")

        # Info section
        info_frame = ctk.CTkFrame(self.details_panel)
        info_frame.grid(row=1, column=0, sticky="ew", pady=5)
        info_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            info_frame,
            text=f"Capacity: {table.capacity}",
        ).grid(row=0, column=0, pady=2)

        ctk.CTkLabel(
            info_frame,
            text=f"Location: {table.location}",
        ).grid(row=1, column=0, pady=2)

        # Status section
        status_frame = ctk.CTkFrame(self.details_panel)
        status_frame.grid(row=2, column=0, sticky="ew", pady=5)
        status_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            status_frame, text="Status:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, pady=2)

        # Status dropdown
        status_var = ctk.StringVar(value=table.status.value)
        status_menu = ctk.CTkOptionMenu(
            status_frame,
            values=[status.value for status in TableStatus],
            variable=status_var,
            command=lambda s: self._handle_status_change(table, TableStatus(s)),
            width=250,
        )
        status_menu.grid(row=1, column=0, pady=2)

        # Actions section
        actions_frame = ctk.CTkFrame(self.details_panel)
        actions_frame.grid(row=3, column=0, sticky="ew", pady=10)
        actions_frame.grid_columnconfigure(0, weight=1)

        # Edit button
        ctk.CTkButton(
            actions_frame,
            text="Edit Table",
            command=lambda: self._handle_edit_table(table),
            width=250,
        ).grid(row=0, column=0, pady=2)

        # Delete button
        ctk.CTkButton(
            actions_frame,
            text="Delete Table",
            command=lambda: self._handle_delete_table(table),
            fg_color="red",
            hover_color="darkred",
            width=250,
        ).grid(row=1, column=0, pady=2)

    def _get_valid_moves(self, table: Table) -> List[Tuple[int, int]]:
        """Get valid grid positions where the table can be moved"""
        valid = []
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
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
                # Move table to new position
                old_x, old_y = self.selected_table.grid_x, self.selected_table.grid_y
                self.selected_table.set_grid_position(x, y)

                # Update service
                try:
                    self.service.update(self.selected_table.id, grid_x=x, grid_y=y)

                    # Update cells
                    self.cells[old_y][old_x].set_table(None)
                    cell.set_table(self.selected_table)

                except Exception as e:
                    self.show_error("Error", f"Failed to move table: {str(e)}")

            # Clear selection and highlights
            self._clear_selection()

        elif cell.table:
            # Select table and show valid moves
            self.selected_table = cell.table
            cell.configure(border_color="#2196F3", border_width=2)

            # Show valid moves
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

        # Reset to empty details panel
        self._create_empty_details()

    def refresh(self):
        """Refresh the floor plan view"""
        try:
            # Clear all cells
            for row in self.cells:
                for cell in row:
                    cell.set_table(None)

            # Get all tables
            tables = self.service.get_all()

            # Place tables in grid
            for table in tables:
                # Ensure table has valid grid position
                if not hasattr(table, "grid_x") or not hasattr(table, "grid_y"):
                    table.grid_x = 0
                    table.grid_y = 0

                if (
                    0 <= table.grid_x < self.GRID_SIZE
                    and 0 <= table.grid_y < self.GRID_SIZE
                ):
                    self.cells[table.grid_y][table.grid_x].set_table(table)

            # Clear any selection
            self._clear_selection()

        except Exception as e:
            logger.error(f"Error refreshing floor plan: {e}")
            self.show_error("Error", f"Failed to refresh floor plan: {str(e)}")

    def _handle_add_table(self):
        """Handle adding a new table"""
        # Find first empty cell
        empty_pos = None
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
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
