import customtkinter as ctk

import logging

logger = logging.getLogger(__name__)


class OrdersView(ctk.CTkFrame):
    def __init__(self, master: any):
        super().__init__(master)
        self.controller = None

        self.initialize_ui()

    def initialize_ui(self):
        label = ctk.CTkLabel(self, text="Orders Management", font=ctk.CTkFont(size=20))
        label.pack(pady=20)
