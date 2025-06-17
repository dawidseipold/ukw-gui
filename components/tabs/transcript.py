import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import queue
import pyaudio
from utils.transcript.stt_from_file import GladiaFromFileSTT
from utils.transcript.stt_real_time import GladiaRealTimeSTT


# --- Klasa dla sekcji "Transkrypcja z pliku" ---
# Ta klasa będzie dziedziczyć po tk.Frame i zawierać całą logikę i widżety dla transkrypcji z pliku.
class FileTranscriptionSection(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.input_file_path = None
        self.last_transcription_utterances = None

        self.create_widgets()
        self.setup_styles()

    def setup_styles(self):
        style = ttk.Style()
        style.configure("SaveButton.TButton", background="#FFC107", foreground="black", font=("Arial", 10, "bold"))
        style.map("SaveButton.TButton", background=[("disabled", "#a6a6a6"), ("!disabled", "#FFC107")],
                  foreground=[("disabled", "#eeeeee"), ("!disabled", "black")])
        style.configure("GreenButton.TButton", background="#4CAF50", foreground="white", font=("Arial", 10, "bold"))
        style.map("GreenButton.TButton", background=[("disabled", "#a6a6a6"), ("!disabled", "#4CAF50")],
                  foreground=[("disabled", "#eeeeee"), ("!disabled", "white")])
        style.configure("LightButton.TButton", background="#e0e0e0", foreground="black", font=("Arial", 10))
        style.map("LightButton.TButton", background=[("disabled", "#d0d0d0"), ("!disabled", "#e0e0e0")],
                  foreground=[("disabled", "#808080"), ("!disabled", "black")])

    def create_widgets(self):
        # Usunięto wewnętrzny nagłówek "Transkrypcja z pliku" - jest wybierane na górze

        self.input_button = ttk.Button(self, text="Wybierz plik audio/wideo", command=self.browse_input_file,
                                       style="LightButton.TButton")
        self.input_button.pack(pady=5)

        self.input_path_label = tk.Label(self, text="Nie wybrano pliku", fg="gray")
        self.input_path_label.pack(pady=5)

        self.status_label = tk.Label(self, text="Gotowy", fg="blue")
        self.status_label.pack(pady=10)

        self.transcribe_button = ttk.Button(self, text="Rozpocznij Transkrypcję", command=self.start_transcription,
                                            style="GreenButton.TButton")
        self.transcribe_button.pack(pady=20)

        self.transcript_text = tk.Text(self, wrap=tk.WORD, height=10, width=80)
        self.transcript_text.pack(pady=10)
        self.transcript_text.insert(tk.END, "Transkrypcja pojawi się tutaj...")
        self.transcript_text.config(state=tk.DISABLED)

        self.save_button = ttk.Button(self, text="Zapisz Transkrypcję", command=self.save_transcript_to_file,
                                      state=tk.DISABLED, style="SaveButton.TButton")
        self.save_button.pack(pady=10)

    def browse_input_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Pliki audio", "*.mp3 *.wav *.ogg *.m4a *.flac"),
                ("Pliki wideo", "*.mp4 *.avi *.mov *.mkv"),
                ("Wszystkie pliki", "*.*"),
            ]
        )
        if file_path:
            self.input_file_path = file_path
            self.input_path_label.config(text=f"Wybrano: {os.path.basename(file_path)}", fg="black")
            self.status_label.config(text="Plik wejściowy wybrany. Gotowy do transkrypcji.", fg="blue")
            self.save_button.config(state=tk.DISABLED)
            self.last_transcription_utterances = None
            self.transcript_text.config(state=tk.NORMAL)
            self.transcript_text.delete(1.0, tk.END)
            self.transcript_text.insert(tk.END, "Transkrypcja pojawi się tutaj...")
            self.transcript_text.config(state=tk.DISABLED)
        else:
            self.input_file_path = None
            self.input_path_label.config(text="Nie wybrano pliku", fg="gray")
            self.status_label.config(text="Gotowy", fg="blue")

    def start_transcription(self):
        if not self.input_file_path:
            messagebox.showerror("Błąd", "Proszę wybrać plik audio/wideo do transkrypcji.")
            return

        self.status_label.config(text="Transkrypcja w toku...", fg="blue")
        self.transcribe_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)

        self.transcript_text.config(state=tk.NORMAL)
        self.transcript_text.delete(1.0, tk.END)
        self.transcript_text.insert(tk.END, "Transkrypcja w toku, proszę czekać...")
        self.transcript_text.config(state=tk.DISABLED)

        threading.Thread(target=self.run_gladia_transcription).start()

    def update_status_ui(self, message, color="blue"):
        self.after(0, lambda: self.status_label.config(text=message, fg=color))

    def update_transcript_ui(self, utterances):
        self.after(0, lambda: self._display_transcript(utterances))

    def _display_transcript(self, utterances):
        self.transcript_text.config(state=tk.NORMAL)
        self.transcript_text.delete(1.0, tk.END)

        formatted_transcript_lines = []
        if utterances:
            self.last_transcription_utterances = utterances
            for entry in utterances:
                if isinstance(entry, dict):
                    speaker = entry.get("speaker", "Unknown")
                    text = entry.get("text", "")
                    start = entry.get("start", 0.0)
                    end = entry.get("end", 0.0)
                    line = f'[{start:06.2f}s - {end:06.2f}s] Mówca {speaker}: {text}'
                    self.transcript_text.insert(tk.END, line + "\n")
                    formatted_transcript_lines.append(line)
                else:
                    line = f'[Nieznany format] {entry}'
                    self.transcript_text.insert(tk.END, line + "\n")
                    formatted_transcript_lines.append(line)
        else:
            self.transcript_text.insert(tk.END, "Brak transkrypcji do wyświetlenia lub błąd podczas jej pobierania.")
            self.last_transcription_utterances = None

        self.transcript_text.config(state=tk.DISABLED)

        if self.last_transcription_utterances:
            self.save_button.config(state=tk.NORMAL)
            self.status_label.config(text="Transkrypcja gotowa do zapisu.", fg="green")
        else:
            self.save_button.config(state=tk.DISABLED)
            self.status_label.config(text="Błąd podczas transkrypcji. Brak danych do wyświetlenia.", fg="red")

    def save_transcript_to_file(self):
        if not self.last_transcription_utterances:
            messagebox.showerror("Błąd", "Brak transkrypcji do zapisania.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Pliki tekstowe", "*.txt"), ("Wszystkie pliki", "*.*")],
            title="Zapisz transkrypcję jako..."
        )

        if not output_path:
            self.status_label.config(text="Zapis anulowany.", fg="gray")
            return

        formatted_transcript_lines = []
        for entry in self.last_transcription_utterances:
            if isinstance(entry, dict):
                speaker = entry.get("speaker", "Unknown")
                text = entry.get("text", "")
                start = entry.get("start", 0.0)
                end = entry.get("end", 0.0)
                formatted_transcript_lines.append(f'[{start:06.2f}s - {end:06.2f}s] Mówca {speaker}: {text}')
            else:
                formatted_transcript_lines.append(f'[Nieznany format] {entry}')

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(formatted_transcript_lines))
            self.update_status_ui("Transkrypcja zakończona pomyślnie i zapisana do pliku!", "green")
            messagebox.showinfo("Sukces", "Transkrypcja zakończona pomyślnie i zapisana do pliku!")
        except Exception as e:
            self.update_status_ui(f"Błąd zapisu transkrypcji: {e}", "red")
            messagebox.showerror("Błąd zapisu", f"Nie udało się zapisać transkrypcji: {e}")

    def run_gladia_transcription(self):
        try:
            gladia_stt = GladiaFromFileSTT(self.input_file_path)

            transcription_result = gladia_stt.doTranscription(
                update_status_callback=lambda msg: self.update_status_ui(msg),
                show_transcript_callback=lambda utterances: self.update_transcript_ui(utterances)
            )

            if transcription_result is None:
                self.update_status_ui(
                    "Transkrypcja nie powiodła się. Sprawdź plik wejściowy lub konfigurację klucza API Gladia w .env",
                    "red")
                messagebox.showerror("Błąd Transkrypcji",
                                     "Transkrypcja nie powiodła się. Upewnij się, że klucz API jest w pliku .env i plik wejściowy jest poprawny.")

        except Exception as e:
            self.update_status_ui(f"Wystąpił błąd ogólny: {e}", "red")
            messagebox.showerror("Błąd Transkrypcji", f"Wystąpił błąd ogólny podczas transkrypcji: {e}")
        finally:
            self.transcribe_button.config(state=tk.NORMAL)


# --- Klasa dla sekcji "Transkrypcja w czasie rzeczywistym" ---
# Podobnie, dziedziczy po tk.Frame i zawiera widżety oraz logikę dla transkrypcji na żywo.
class RealtimeTranscriptionSection(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.gladia_realtime_stt = None
        self.transcription_queue = queue.Queue()
        self.is_recording = False
        self.all_transcribed_lines = []
        self.stop_event_received_from_thread = False  # Nowa flaga do zarządzania zamknięciem UI

        self.create_widgets()
        self.setup_styles()

    def setup_styles(self):
        style = ttk.Style()
        style.configure("StartButton.TButton", background="#4CAF50", foreground="white", font=("Arial", 10, "bold"))
        style.map("StartButton.TButton", background=[("disabled", "#a6a6a6"), ("!disabled", "#4CAF50")],
                  foreground=[("disabled", "#eeeeee"), ("!disabled", "white")])
        style.configure("StopButton.TButton", background="#F44336", foreground="white", font=("Arial", 10, "bold"))
        style.map("StopButton.TButton", background=[("disabled", "#a6a6a6"), ("!disabled", "#F44336")],
                  foreground=[("disabled", "#eeeeee"), ("!disabled", "white")])
        style.configure("SaveButton.TButton", background="#FFC107", foreground="black", font=("Arial", 10, "bold"))
        style.map("SaveButton.TButton", background=[("disabled", "#a6a6a6"), ("!disabled", "#FFC107")],
                  foreground=[("disabled", "#eeeeee"), ("!disabled", "black")])

    def create_widgets(self):
        # Usunięto wewnętrzny nagłówek "Transkrypcja w czasie rzeczywistym"

        tk.Label(self, text="Wybierz urządzenie wejściowe:").pack(pady=5)
        self.device_var = tk.StringVar(self)
        self.device_options = self._get_audio_input_devices()

        # Jeśli są urządzenia, ustaw pierwsze jako domyślne. W przeciwnym razie "Brak urządzeń"
        if self.device_options:
            self.device_var.set(self.device_options[0][0])
        else:
            self.device_var.set("Brak urządzeń audio")

        # Tworzenie OptionMenu
        # Upewnij się, że self.device_var.get() jest pierwszym elementem *args, aby ustawić początkową wartość
        self.device_menu = ttk.OptionMenu(self, self.device_var, self.device_var.get(),
                                          *[name for name, _ in self.device_options])
        self.device_menu.pack(pady=5)

        self.status_label = tk.Label(self, text="Gotowy do nagrywania", fg="blue")
        self.status_label.pack(pady=10)

        self.start_button = ttk.Button(self, text="Rozpocznij nagrywanie", command=self.start_recording,
                                       style="StartButton.TButton")
        self.start_button.pack(pady=5)

        self.stop_button = ttk.Button(self, text="Zatrzymaj nagrywanie", command=self.stop_recording, state=tk.DISABLED,
                                      style="StopButton.TButton")
        self.stop_button.pack(pady=5)

        self.transcript_text = tk.Text(self, wrap=tk.WORD, height=15, width=80)
        self.transcript_text.pack(pady=10)
        self.transcript_text.insert(tk.END, "Transkrypcja w czasie rzeczywistym pojawi się tutaj...")
        self.transcript_text.config(state=tk.DISABLED)

        self.save_button = ttk.Button(self, text="Zapisz Transkrypcję", command=self.save_realtime_transcript,
                                      state=tk.DISABLED, style="SaveButton.TButton")
        self.save_button.pack(pady=10)

        # Jeżeli nie ma urządzeń, wyłącz przycisk Start
        if not self.device_options:
            self.start_button.config(state=tk.DISABLED)

    def _get_audio_input_devices(self):
        devices = []
        p = None  # Upewnij się, że p jest zainicjowane
        try:
            p = pyaudio.PyAudio()
            info = p.get_host_api_info_by_index(0)
            num_devices = info.get('deviceCount')
            for i in range(0, num_devices):
                device_info = p.get_device_info_by_host_api_device_index(0, i)
                if device_info.get('maxInputChannels') > 0:
                    devices.append((device_info.get('name'), i))
        except Exception as e:
            messagebox.showerror("Błąd audio", f"Nie udało się pobrać urządzeń audio: {e}")
            # Nie ustawiaj statusu tutaj, to GUI się tym zajmie
        finally:
            if p:  # Zakończ PyAudio tylko jeśli zostało zainicjowane
                p.terminate()
        return devices

    def _get_selected_device_index(self):
        selected_name = self.device_var.get()
        # Obsłuż przypadek "Brak urządzeń audio"
        if selected_name == "Brak urządzeń audio" and not self.device_options:
            return None

        for name, index in self.device_options:
            if name == selected_name:
                return index
        return None

    def start_recording(self):
        if self.is_recording:
            return

        selected_device_index = self._get_selected_device_index()
        # Sprawdzamy, czy urządzenie zostało wybrane, jeśli lista urządzeń nie jest pusta
        if not self.device_options or (selected_device_index is None and self.device_options):
            messagebox.showerror("Błąd", "Proszę wybrać urządzenie wejściowe audio.")
            return

        self.status_label.config(text="Rozpoczynam nagrywanie...", fg="blue")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.DISABLED)
        self.transcript_text.config(state=tk.NORMAL)
        self.transcript_text.delete(1.0, tk.END)
        self.transcript_text.insert(tk.END, "Słucham i transkrybuję w czasie rzeczywistym...\n")
        self.transcript_text.config(state=tk.DISABLED)

        self.is_recording = True
        self.all_transcribed_lines = []
        self.stop_event_received_from_thread = False  # Resetuj flagę

        try:
            self.gladia_realtime_stt = GladiaRealTimeSTT(
                on_transcription=self._handle_realtime_transcription,
                on_status_update=self._handle_status_update,  # Przekaż nowy callback
                input_device_index=selected_device_index
            )
            # Metoda run() w GladiaRealTimeSTT została zmieniona by tylko startować,
            # więc uruchom ją w oddzielnym wątku.
            threading.Thread(target=self.gladia_realtime_stt.run, daemon=True).start()
            self.after(100, self._process_transcription_queue)

        except Exception as e:
            messagebox.showerror("Błąd uruchamiania", f"Nie udało się uruchomić transkrypcji: {e}")
            self.status_label.config(text="Błąd uruchamiania.", fg="red")
            self.stop_recording_ui()

    def _run_gladia_realtime_stt(self):
        # Ta metoda już nie jest potrzebna, bo bezpośrednio wywołujemy gladia_realtime_stt.run()
        # z main loop, a ona sama zarządza startConnection.
        pass

    def _handle_realtime_transcription(self, text):
        self.transcription_queue.put(("transcript", text))

    def _handle_status_update(self, message, color):
        """Callback dla aktualizacji statusu z GladiaRealTimeSTT."""
        self.transcription_queue.put(("status", (message, color)))
        # Możesz także przekazać sygnał zatrzymania UI, jeśli status jest błędem lub zamknięciem
        if "Błąd" in message or "zamknięte" in message:
            self.transcription_queue.put(("stop_ui_from_thread", None))

    def _process_transcription_queue(self):
        while not self.transcription_queue.empty():
            item_type, data = self.transcription_queue.get()
            if item_type == "transcript":
                self.transcript_text.config(state=tk.NORMAL)
                self.transcript_text.insert(tk.END, data + "\n")
                self.transcript_text.see(tk.END)
                self.transcript_text.config(state=tk.DISABLED)
                self.all_transcribed_lines.append(data)
            elif item_type == "status":
                self.status_label.config(text=data[0], fg=data[1])
            elif item_type == "error":
                messagebox.showerror("Błąd transkrypcji", data)
                self.stop_recording_ui()
            elif item_type == "stop_ui_from_thread":  # Jeśli wątek dał sygnał do zatrzymania UI
                self.stop_event_received_from_thread = True
                self.stop_recording_ui()

        # Kontynuuj sprawdzanie kolejki, jeśli nagrywanie jest aktywne
        if self.is_recording and not self.stop_event_received_from_thread:
            self.after(100, self._process_transcription_queue)

    def stop_recording_ui(self):
        self.is_recording = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.NORMAL if self.all_transcribed_lines else tk.DISABLED)
        # Opcjonalnie zresetuj status tylko jeśli nie jest to status błędu od wątku
        if not self.stop_event_received_from_thread:
            self.status_label.config(text="Nagrywanie zakończone.", fg="green")

    def stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False  # Ustaw flagę is_recording na False zanim zamkniesz połączenie
        if self.gladia_realtime_stt:
            self.gladia_realtime_stt.stopConnection()
            # Nie ustawiaj self.gladia_realtime_stt = None natychmiast
            # Daj czas wątkowi WebSocket na czyste zamknięcie.
            # Zostanie zresetowane przy następnym start_recording

        # Jeśli nie zatrzymaliśmy UI przez kolejkę (np. manualne kliknięcie Stop)
        if not self.stop_event_received_from_thread:
            self.stop_recording_ui()

    def save_realtime_transcript(self):
        if not self.all_transcribed_lines:
            messagebox.showerror("Błąd", "Brak transkrypcji do zapisania.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Pliki tekstowe", "*.txt"), ("Wszystkie pliki", "*.*")],
            title="Zapisz transkrypcję w czasie rzeczywistym jako..."
        )

        if not output_path:
            self.status_label.config(text="Zapis anulowany.", fg="gray")
            return

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.all_transcribed_lines))
            self.status_label.config(text="Transkrypcja zapisana pomyślnie!", fg="green")
            messagebox.showinfo("Sukces",
                                "Transkrypcja w czasie rzeczywistym zakończona pomyślnie i zapisana do pliku!")
        except Exception as e:
            self.status_label.config(text=f"Błąd zapisu transkrypcji: {e}", fg="red")
            messagebox.showerror("Błąd zapisu", f"Nie udało się zapisać transkrypcji: {e}")


# --- KLASA KONTENEROWA DLA ZAKŁADEK TRANSLACYJNYCH (TranscriptTab) ---
class TranscriptTab(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        tk.Label(self, text="Transkrypcja mowy na tekst (Gladia)", font=("Arial", 16, "bold")).pack(pady=10)

        # Kontrolka do wyboru typu transkrypcji (radiobuttons)
        self.transcription_mode_var = tk.StringVar(value="file_transcription")  # Domyślnie: z pliku

        mode_frame = ttk.Frame(self)
        mode_frame.pack(pady=10)

        # Radiobutton dla transkrypcji z pliku
        self.file_mode_radio = ttk.Radiobutton(
            mode_frame,
            text="Transkrypcja z pliku",
            variable=self.transcription_mode_var,
            value="file_transcription",
            command=self._show_selected_mode
        )
        self.file_mode_radio.pack(side=tk.LEFT, padx=10)

        # Radiobutton dla transkrypcji w czasie rzeczywistym
        self.realtime_mode_radio = ttk.Radiobutton(
            mode_frame,
            text="Transkrypcja w czasie rzeczywistym",
            variable=self.transcription_mode_var,
            value="realtime_transcription",
            command=self._show_selected_mode
        )
        self.realtime_mode_radio.pack(side=tk.LEFT, padx=10)

        # Kontenery dla obu typów transkrypcji
        self.file_transcription_section = FileTranscriptionSection(self)
        self.realtime_transcription_section = RealtimeTranscriptionSection(self)

        # Pokaż domyślną sekcję (transkrypcja z pliku)
        self._show_selected_mode()

        # Dodaj handler na zamknięcie głównego okna, aby zatrzymać nagrywanie na żywo
        # To jest bardzo ważne, aby nie zostawiać procesów mikrofonu w tle
        parent.winfo_toplevel().protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _show_selected_mode(self):
        selected_mode = self.transcription_mode_var.get()

        # Ukryj wszystkie sekcje
        self.file_transcription_section.pack_forget()
        self.realtime_transcription_section.pack_forget()

        # Zawsze zatrzymaj nagrywanie na żywo, gdy zmieniasz tryb
        # Jest to obsłużone w _on_tab_change w poprzedniej strukturze,
        # teraz robimy to bezpośrednio przy zmianie Radiobuttona
        if self.realtime_transcription_section.is_recording:
            print("Zmieniono tryb, zatrzymuję nagrywanie realtime.")
            self.realtime_transcription_section.stop_recording()

        # Pokaż wybraną sekcję
        if selected_mode == "file_transcription":
            self.file_transcription_section.pack(expand=True, fill="both")
        elif selected_mode == "realtime_transcription":
            self.realtime_transcription_section.pack(expand=True, fill="both")

    def _on_window_close(self):
        """Obsługa zamykania okna głównego, aby zatrzymać procesy audio."""
        if self.realtime_transcription_section.is_recording:
            print("Zamykanie okna, zatrzymuję nagrywanie realtime.")
            self.realtime_transcription_section.stop_recording()
        self.master.destroy()  # Zamyka główne okno Tkinter


# Przykład użycia
if __name__ == "__main__":
    root = tk.Tk()
    root.title("GUI - Tłumaczenie, Ekstrakcja tekstu i Klasyfikacja obrazów")
    root.geometry("800x800")  # Zwiększono rozmiar, aby pomieścić więcej

    main_notebook = ttk.Notebook(root)
    main_notebook.pack(expand=True, fill="both")

    # Zakładka Transkrypcja (która zawiera radiobuttons i sekcje)
    transcript_main_tab = TranscriptTab(main_notebook)
    main_notebook.add(transcript_main_tab, text="Transkrypcja")


    # Inne przykładowe zakładki
    class DummyTab(tk.Frame):
        def __init__(self, parent, text):
            super().__init__(parent)
            tk.Label(self, text=text, font=("Arial", 16)).pack(pady=50)


    dummy_translator = DummyTab(main_notebook, "Zakładka: Tłumacz")
    main_notebook.add(dummy_translator, text="Tłumacz")
    dummy_extractor = DummyTab(main_notebook, "Zakładka: Ekstraktor Tekstu")
    main_notebook.add(dummy_extractor, text="Ekstraktor Tekstu")
    dummy_classifier = DummyTab(main_notebook, "Zakładka: Klasyfikator Obrazów")
    main_notebook.add(dummy_classifier, text="Klasyfikator Obrazów")

    root.mainloop()