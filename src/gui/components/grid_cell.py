import logging
import customtkinter as ctk
from typing import Optional
from ...models.table import Table
from ...utils.colors import get_status_color

logger = logging.getLogger(__name__)


class GridCell(ctk.CTkButton):
    def __init__(
        self, master, grid_x: int, grid_y: int, size: int = 100, command=None, **kwargs
    ):
        super().__init__(
            master,
            width=size,
            height=size,
            fg_color="transparent",
            text="",
            hover_color="#2d2d2d",
            command=command,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=6,
            border_width=1,
            border_color="#3f3f3f",
            **kwargs,
        )

        self.grid_x = grid_x
        self.grid_y = grid_y
        self.size = size
        self.table = None
        self.grid_propagate(False)

    def set_table(self, table: Optional[Table]):
        self.table = table

        if table:
            text = f"Table {table.number}\n{table.capacity} seats"
            self.configure(
                text=text, fg_color=get_status_color(table.status), text_color="#ffffff"
            )
        else:
            self.configure(text="", fg_color="transparent")

    def highlight(self, highlight: bool = True):
        self.configure(
            border_color="#4CAF50" if highlight else "#3f3f3f",
            border_width=2 if highlight else 1,
        )

    def set_selected(self, selected: bool = True):
        self.configure(
            border_color="#2196F3" if selected else "#3f3f3f",
            border_width=2 if selected else 1,
        )
