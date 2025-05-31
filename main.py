import tkinter as tk
from tkinter import ttk

import sv_ttk

from components.topmenu import TopMenu, TabContent1, TabContent2

root = tk.Tk()

root.title("Cwiczenie 5")
root.geometry("600x400")

top_menu = TopMenu(root)
top_menu.pack(fill=tk.BOTH, expand=True)

top_menu.add_tab("Tab 1", TabContent1)
top_menu.add_tab("Tab 2", TabContent2)

sv_ttk.set_theme("light")

root.mainloop()