import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from utils.translator.translator import Translator
import threading

class TranslatorTab(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.translator = Translator()

        # Nagłówek
        self.label = tk.Label(self, text="Tłumacz plików tekstowych", font=("Arial", 16))
        self.label.pack(pady=10)

        # Wybór pliku wejściowego
        self.input_button = tk.Button(
            self, text="Wybierz plik wejściowy", command=self.browse_input_file
        )
        self.input_button.pack(pady=5)

        self.input_path_label = tk.Label(self, text="Nie wybrano pliku", fg="gray")
        self.input_path_label.pack(pady=5)

        # Wybór pliku wyjściowego
        self.output_button = tk.Button(
            self, text="Wybierz plik wyjściowy", command=self.browse_output_file
        )
        self.output_button.pack(pady=5)

        self.output_path_label = tk.Label(self, text="Nie wybrano pliku", fg="gray")
        self.output_path_label.pack(pady=5)

        # Pasek postępu
        self.progress = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)

        # Etykieta statusu
        self.status_label = tk.Label(self, text="", fg="blue")
        self.status_label.pack(pady=10)

        # Przycisk tłumaczenia
        self.translate_button = tk.Button(
            self, text="Tłumacz", command=self.start_translation, bg="green", fg="black"
        )
        self.translate_button.pack(pady=20)

        # Ścieżki do plików
        self.input_path = None
        self.output_path = None

    def browse_input_file(self):
        """
        Otwiera eksplorator plików do wyboru pliku wejściowego.
        """
        file_path = filedialog.askopenfilename(
            filetypes=[("Pliki tekstowe", "*.txt"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            self.input_path = file_path
            self.input_path_label.config(text=f"Wybrano: {file_path}", fg="black")
        else:
            self.input_path_label.config(text="Nie wybrano pliku", fg="gray")

    def browse_output_file(self):
        """
        Otwiera eksplorator plików do wyboru pliku wyjściowego.
        """
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Pliki tekstowe", "*.txt"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            self.output_path = file_path
            self.output_path_label.config(text=f"Wybrano: {file_path}", fg="black")
        else:
            self.output_path_label.config(text="Nie wybrano pliku", fg="gray")

    def start_translation(self):
        """
        Uruchamia tłumaczenie w osobnym wątku.
        """
        if not self.input_path or not self.output_path:
            messagebox.showerror("Błąd", "Proszę wybrać plik wejściowy i wyjściowy.")
            return

        # Zresetuj pasek postępu i status
        self.progress["value"] = 0
        self.status_label.config(text="Tłumaczenie w toku...", fg="blue")

        # Uruchom tłumaczenie w osobnym wątku
        threading.Thread(target=self.translate_file).start()

    def translate_file(self):
        """
        Wykonuje tłumaczenie pliku.
        """
        try:
            # Oblicz liczbę linii w pliku wejściowym
            total_lines = sum(1 for _ in open(self.input_path, 'r', encoding='utf-8'))
            self.progress["maximum"] = total_lines

            def update_progress(processed_lines):
                self.progress["value"] = processed_lines

            # Przetwarzanie pliku z aktualizacją postępu
            self.translator.process_file_with_progress(
                self.input_path, self.output_path, update_progress
            )

            # Aktualizacja statusu po zakończeniu
            self.status_label.config(text="Tłumaczenie zakończone pomyślnie!", fg="green")
            messagebox.showinfo("Sukces", "Tłumaczenie zakończone pomyślnie!")
        except Exception as e:
            self.status_label.config(text="Błąd podczas tłumaczenia.", fg="red")
            messagebox.showerror("Błąd", str(e))