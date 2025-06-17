import tkinter as tk
from tkinter import ttk
import sv_ttk
from components.topmenu import TopMenu
from components.tabs.translator import TranslatorTab
from components.tabs.text_extractor import TextExtractorTab
from components.tabs.image_classifier import ImageClassifierTab  # Import nowej zakładki
from components.tabs.transcript import TranscriptTab
from components.tabs.recorder import AudioEditorTab
from components.tabs.tts import TTSTab


# Tworzenie głównego okna aplikacji
root = tk.Tk()
root.title("GUI - Tłumaczenie, Ekstrakcja tekstu i Klasyfikacja obrazów")
root.geometry("800x600")

# Tworzenie menu zakładek
top_menu = TopMenu(root)
top_menu.pack(fill=tk.BOTH, expand=True)

# Dodanie zakładek
top_menu.add_tab("Tłumacz", TranslatorTab)
top_menu.add_tab("Ekstraktor Tekstu", TextExtractorTab)
top_menu.add_tab("Klasyfikator Obrazów", ImageClassifierTab)  # Dodanie zakładki klasyfikacji obrazów
top_menu.add_tab("Transkrypcja", TranscriptTab)
top_menu.add_tab("Nagrywanie", AudioEditorTab)
top_menu.add_tab("TTS", TTSTab)

# Ustawienie motywu
sv_ttk.set_theme("light")

# Uruchomienie aplikacji
root.mainloop()