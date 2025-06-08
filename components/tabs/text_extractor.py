import tkinter as tk
from tkinter import filedialog, messagebox
from utils.text_extractor.document_processor import DocumentProcessor
import threading

class TextExtractorTab(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.processor = None

        self.label = tk.Label(self, text="Ekstrakcja tekstu z dokumentów", font=("Arial", 16))
        self.label.pack(pady=10)

        self.input_button = tk.Button(
            self, text="Wybierz pliki wejściowe", command=self.browse_input_files
        )
        self.input_button.pack(pady=5)

        self.input_path_label = tk.Label(self, text="Nie wybrano plików", fg="gray")
        self.input_path_label.pack(pady=5)

        self.output_button = tk.Button(
            self, text="Wybierz katalog wyjściowy", command=self.browse_output_dir
        )
        self.output_button.pack(pady=5)

        self.output_path_label = tk.Label(self, text="Nie wybrano katalogu", fg="gray")
        self.output_path_label.pack(pady=5)

        self.process_button = tk.Button(
            self, text="Przetwarzaj", command=self.start_processing, bg="green", fg="black"
        )
        self.process_button.pack(pady=20)

        self.input_files = None
        self.output_dir = None

    def browse_input_files(self):
        """
        Otwiera eksplorator plików do wyboru plików wejściowych (PDF, DOCX, obrazy).
        """
        file_paths = filedialog.askopenfilenames(
            filetypes=[
                ("Obsługiwane pliki", "*.pdf *.docx *.png *.jpg *.jpeg *.tiff *.tif *.bmp"),
                ("Pliki PDF", "*.pdf"),
                ("Pliki DOCX", "*.docx"),
                ("Obrazy", "*.png *.jpg *.jpeg *.tiff *.tif *.bmp"),
                ("Wszystkie pliki", "*.*")
            ]
        )
        if file_paths:
            self.input_files = file_paths
            self.input_path_label.config(text=f"Wybrano {len(file_paths)} plików", fg="black")
        else:
            self.input_path_label.config(text="Nie wybrano plików", fg="gray")

    def browse_output_dir(self):
        """
        Otwiera eksplorator katalogów do wyboru katalogu wyjściowego.
        """
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir = dir_path
            self.output_path_label.config(text=f"Wybrano katalog: {dir_path}", fg="black")
        else:
            self.output_path_label.config(text="Nie wybrano katalogu", fg="gray")

    def start_processing(self):
        """
        Uruchamia przetwarzanie plików w osobnym wątku.
        """
        if not self.input_files or not self.output_dir:
            messagebox.showerror("Błąd", "Proszę wybrać pliki wejściowe i katalog wyjściowy.")
            return

        self.processor = DocumentProcessor(output_dir=self.output_dir)
        threading.Thread(target=self.process_files).start()

    def process_files(self):
        """
        Przetwarza wybrane pliki i generuje raporty.
        """
        try:
            for file_path in self.input_files:
                self.processor.process_file(file_path)

            self.processor.generate_report_file()

            messagebox.showinfo("Sukces", "Przetwarzanie zakończone pomyślnie! Raporty zostały wygenerowane.")
        except Exception as e:
            messagebox.showerror("Błąd", str(e))