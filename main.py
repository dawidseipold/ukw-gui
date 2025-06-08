import tkinter as tk
from tkinter import ttk
import sv_ttk
from components.topmenu import TopMenu
from components.tabs.translator import TranslatorTab

root = tk.Tk()
root.title("Translator GUI")
root.geometry("800x600")

top_menu = TopMenu(root)
top_menu.pack(fill=tk.BOTH, expand=True)

top_menu.add_tab("Translator", TranslatorTab)

sv_ttk.set_theme("light")

root.mainloop()