import tkinter as tk
from tkinter import ttk

class TopMenu(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tabs = {}

    def add_tab(self, tab_name, tab_content):
        tab = tab_content(self.notebook)  # Parent to the notebook
        self.notebook.add(tab, text=tab_name)
        self.tabs[tab_name] = tab