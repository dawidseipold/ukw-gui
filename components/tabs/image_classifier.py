import tkinter as tk
from tkinter import filedialog, messagebox
from utils.image_classifier.classifier import process_images
import threading

class ImageClassifierTab(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.label = tk.Label(self, text="Klasyfikacja obrazów za pomocą ViT", font=("Arial", 16))
        self.label.pack(pady=10)

        self.mode = tk.StringVar(value="manual")  # Domyślny tryb: manual
        self.manual_radio = tk.Radiobutton(
            self, text="Manual (wybór obrazów)", variable=self.mode, value="manual", command=self.update_mode
        )
        self.manual_radio.pack(pady=5)

        self.folder_radio = tk.Radiobutton(
            self, text="Folder (wszystkie obrazy w folderze)", variable=self.mode, value="folder", command=self.update_mode
        )
        self.folder_radio.pack(pady=5)

        self.dynamic_frame = tk.Frame(self)
        self.dynamic_frame.pack(pady=10)

        self.file_button = tk.Button(
            self.dynamic_frame, text="Wybierz obrazy", command=self.browse_files
        )
        self.file_path_label = tk.Label(self.dynamic_frame, text="Nie wybrano obrazów", fg="gray")

        self.folder_button = tk.Button(
            self.dynamic_frame, text="Wybierz folder z obrazami", command=self.browse_folder
        )
        self.folder_path_label = tk.Label(self.dynamic_frame, text="Nie wybrano folderu", fg="gray")

        self.output_button = tk.Button(
            self, text="Wybierz plik wynikowy", command=self.browse_output_file
        )
        self.output_button.pack(pady=5)

        self.output_path_label = tk.Label(self, text="Nie wybrano pliku", fg="gray")
        self.output_path_label.pack(pady=5)

        self.classify_button = tk.Button(
            self, text="Klasyfikuj obrazy", command=self.start_classification, bg="green", fg="black"
        )
        self.classify_button.pack(pady=20)

        self.file_paths = None
        self.folder_path = None
        self.output_path = None

        self.update_mode()

    def update_mode(self):
        """
        Aktualizuje widoczność elementów GUI w zależności od wybranego trybu.
        """
        for widget in self.dynamic_frame.winfo_children():
            widget.pack_forget()

        if self.mode.get() == "manual":
            self.file_button.pack(pady=5)
            self.file_path_label.pack(pady=5)
        elif self.mode.get() == "folder":
            self.folder_button.pack(pady=5)
            self.folder_path_label.pack(pady=5)

    def browse_files(self):
        """
        Otwiera eksplorator plików do wyboru obrazów (dla trybu manual).
        """
        file_paths = filedialog.askopenfilenames(
            filetypes=[("Obrazy", "*.png *.jpg *.jpeg *.tiff *.tif *.bmp"), ("Wszystkie pliki", "*.*")]
        )
        if file_paths:
            self.file_paths = list(file_paths)  # Konwersja krotki na listę
            self.file_path_label.config(text=f"Wybrano {len(self.file_paths)} obrazów", fg="black")
        else:
            self.file_path_label.config(text="Nie wybrano obrazów", fg="gray")

    def browse_folder(self):
        """
        Otwiera eksplorator katalogów do wyboru folderu z obrazami (dla trybu folder).
        """
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_path = folder_path
            self.folder_path_label.config(text=f"Wybrano folder: {folder_path}", fg="black")
        else:
            self.folder_path_label.config(text="Nie wybrano folderu", fg="gray")

    def browse_output_file(self):
        """
        Otwiera eksplorator plików do wyboru pliku wynikowego.
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".txt")
        if file_path:
            self.output_path = file_path
            self.output_path_label.config(text=f"Wybrano plik: {file_path}", fg="black")
        else:
            self.output_path_label.config(text="Nie wybrano pliku", fg="gray")

    def start_classification(self):
        """
        Uruchamia klasyfikację obrazów w osobnym wątku.
        """
        if self.mode.get() == "manual" and not self.file_paths:
            messagebox.showerror("Błąd", "Proszę wybrać obrazy do klasyfikacji.")
            return
        if self.mode.get() == "folder" and not self.folder_path:
            messagebox.showerror("Błąd", "Proszę wybrać folder z obrazami.")
            return
        if not self.output_path:
            messagebox.showerror("Błąd", "Proszę wybrać plik wynikowy.")
            return

        threading.Thread(target=self.classify_images).start()

    def classify_images(self):
        """
        Wykonuje klasyfikację obrazów w zależności od wybranego trybu.
        """
        try:
            if self.mode.get() == "manual":
                process_images(self.file_paths, self.output_path)
            elif self.mode.get() == "folder":
                process_images(self.folder_path, self.output_path)

            messagebox.showinfo("Sukces", "Klasyfikacja zakończona pomyślnie! Wyniki zapisano do pliku.")
        except Exception as e:
            messagebox.showerror("Błąd", str(e))