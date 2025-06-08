import tkinter as tk
from tkinter import ttk
import sv_ttk
from components.topmenu import TopMenu
from components.tabs.translator import TranslatorTab
from components.tabs.text_extractor import TextExtractorTab

root = tk.Tk()
root.title("Translator GUI")
root.geometry("800x600")

top_menu = TopMenu(root)
top_menu.pack(fill=tk.BOTH, expand=True)

top_menu.add_tab("Translator", TranslatorTab)
top_menu.add_tab("Text Extractor", TextExtractorTab)

sv_ttk.set_theme("light")

root.mainloop()