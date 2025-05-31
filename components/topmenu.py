import tkinter as tk
from tkinter import ttk

class TopMenu(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent

        self.buttons_frame = tk.Frame(self)
        self.buttons_frame.pack(side=tk.TOP, fill=tk.X)

        self.content_frame = tk.Frame(self)
        self.content_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.tabs = {}
        self.current_tab = None

    def add_tab(self, tab_name, tab_content):
        button = tk.Button(
            self.buttons_frame,
            text=tab_name,
            command=lambda name=tab_name: self.show_tab(name),
        )
        button.pack(side=tk.LEFT, fill=tk.X)

        content = tab_content(self.content_frame)
        content.pack(fill=tk.BOTH, expand=True)
        content.pack_forget()

        self.tabs[tab_name] = {"button": button, "content": content}

        if self.current_tab is None:
            self.show_tab(tab_name)

    def show_tab(self, tab_name):
        if self.current_tab:
            self.tabs[self.current_tab]["content"].pack_forget()

        self.tabs[tab_name]["content"].pack(fill=tk.BOTH, expand=True)
        self.current_tab = tab_name


# Zakładki
class TabContent1(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        label = tk.Label(self, text="This is Tab 1 Content")
        label.pack(padx=20, pady=20)


class TabContent2(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        label = tk.Label(self, text="This is Tab 2 Content")
        label.pack(padx=20, pady=20)