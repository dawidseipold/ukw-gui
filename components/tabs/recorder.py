import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pydub import AudioSegment
from pydub.playback import play
import threading
import os
import wave
import pyaudio  # Ważne: upewnij się, że pyaudio jest zainstalowane (pip install pyaudio)


class AudioEditorTab(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.audio_file_path = None
        self.audio_segment = None
        self.modified_audio_segment = None
        self.playback_thread = None  # Wątek do odtwarzania podglądu (ffplay)

        # Zmienne do nagrywania audio
        self.pyaudio_instance = None
        self.audio_stream_record = None
        self.frames = []  # Przechowuje fragmenty nagranego audio
        self.is_recording_active = False
        self.recording_thread = None  # Wątek dla pętli nagrywania

        self.create_widgets()
        self.setup_styles()

    def setup_styles(self):
        """Konfiguruje style dla widżetów ttk."""
        style = ttk.Style()

        # Ogólne style dla przycisków
        style.configure("TButton", font=("Arial", 10, "bold"))
        style.map("TButton",
                  background=[("disabled", "#e0e0e0")],
                  foreground=[("disabled", "#808080")])

        # Specyficzne style przycisków akcji
        style.configure("EditorButton.TButton", background="#2196F3", foreground="white")  # Niebieski
        style.map("EditorButton.TButton", background=[("!disabled", "#2196F3")])

        style.configure("PlayButton.TButton", background="#00C853", foreground="white")  # Zielony
        style.map("PlayButton.TButton", background=[("!disabled", "#00C853")])

        style.configure("SaveEditorButton.TButton", background="#FFC107", foreground="black")  # Pomarańczowy
        style.map("SaveEditorButton.TButton", background=[("!disabled", "#FFC107")])

        # Style dla przycisków nagrywania
        style.configure("RecordStartButton.TButton", background="#F44336", foreground="white")  # Czerwony
        style.map("RecordStartButton.TButton", background=[("!disabled", "#F44336")])

        style.configure("RecordStopButton.TButton", background="#9E9E9E", foreground="white")  # Szary
        style.map("RecordStopButton.TButton", background=[("!disabled", "#9E9E9E")])

        # Style dla etykiet
        style.configure("TLabel", font=("Arial", 10))

        # Style dla etykiet statusu (z dynamiczną zmianą koloru)
        style.configure("Status.Blue.TLabel", foreground="blue", font=("Arial", 10, "italic"))
        style.configure("Status.Green.TLabel", foreground="green", font=("Arial", 10, "italic"))
        style.configure("Status.Red.TLabel", foreground="red", font=("Arial", 10, "italic"))
        style.configure("Status.Orange.TLabel", foreground="orange", font=("Arial", 10, "italic"))
        style.configure("Status.Gray.TLabel", foreground="gray", font=("Arial", 10, "italic"))

    def create_widgets(self):
        """Tworzy i rozmieszcza widżety w zakładce."""
        self.label = ttk.Label(self, text="Edytor Audio: Nagrywanie i Manipulacja", font=("Arial", 16, "bold"))
        self.label.pack(pady=15)

        # Ramka do nagrywania
        record_frame = ttk.LabelFrame(self, text="Nagrywanie Audio", padding=15)
        record_frame.pack(pady=10, padx=20, fill="x", expand=False)
        record_frame.columnconfigure(0, weight=1)
        record_frame.columnconfigure(1, weight=1)
        record_frame.columnconfigure(2, weight=2)  # Kolumna dla statusu

        self.record_start_button = ttk.Button(record_frame, text="Rozpocznij nagrywanie", command=self.start_recording,
                                              style="RecordStartButton.TButton")
        self.record_start_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.record_stop_button = ttk.Button(record_frame, text="Zatrzymaj nagrywanie", command=self.stop_recording,
                                             state=tk.DISABLED, style="RecordStopButton.TButton")
        self.record_stop_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.record_status_label = ttk.Label(record_frame, text="Gotowy do nagrywania", style="Status.Blue.TLabel")
        self.record_status_label.grid(row=0, column=2, padx=10, pady=5, sticky="ew")

        # Ramka do ładowania plików
        load_frame = ttk.LabelFrame(self, text="Załaduj Plik Audio", padding=15)
        load_frame.pack(pady=10, padx=20, fill="x", expand=False)
        load_frame.columnconfigure(0, weight=1)
        load_frame.columnconfigure(1, weight=3)

        self.load_button = ttk.Button(load_frame, text="Załaduj plik audio", command=self.load_audio_file,
                                      style="EditorButton.TButton")
        self.load_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.file_path_label = ttk.Label(load_frame, text="Nie wybrano pliku", foreground="gray")
        self.file_path_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Ramka do regulacji tempa i tonu
        control_frame = ttk.LabelFrame(self, text="Regulacja Tempa i Wysokości Tonu", padding=15)
        control_frame.pack(pady=10, padx=20, fill="x", expand=False)
        control_frame.columnconfigure(1, weight=3)  # Suwak będzie rozciągliwy

        # Tempo (Speed)
        ttk.Label(control_frame, text="Tempo (x):", style="TLabel").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.speed_scale = ttk.Scale(control_frame, from_=0.5, to_=2.0, orient="horizontal", command=self.update_audio,
                                     length=200)
        self.speed_scale.set(1.0)
        self.speed_scale.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.speed_label = ttk.Label(control_frame, text="1.0x", style="TLabel")
        self.speed_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Wysokość tonu (Pitch)
        ttk.Label(control_frame, text="Wysokość tonu (półtony):", style="TLabel").grid(row=1, column=0, padx=5, pady=5,
                                                                                       sticky="w")
        self.pitch_scale = ttk.Scale(control_frame, from_=-6, to_=6, orient="horizontal", command=self.update_audio,
                                     length=200)
        self.pitch_scale.set(0)
        self.pitch_scale.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.pitch_label = ttk.Label(control_frame, text="0 półtonów", style="TLabel")
        self.pitch_label.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        # Ramka do odtwarzania i zapisu
        action_frame = ttk.LabelFrame(self, text="Odtwarzanie i Zapis", padding=15)
        action_frame.pack(pady=10, padx=20, fill="x", expand=False)
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)
        action_frame.columnconfigure(2, weight=2)

        self.play_button = ttk.Button(action_frame, text="Odtwórz podgląd", command=self.play_preview,
                                      state=tk.DISABLED, style="PlayButton.TButton")
        self.play_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.stop_play_button = ttk.Button(action_frame, text="Zatrzymaj odtwarzanie", command=self.stop_playback,
                                           state=tk.DISABLED, style="PlayButton.TButton")
        self.stop_play_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.save_button = ttk.Button(action_frame, text="Zapisz zmodyfikowany plik", command=self.save_audio_file,
                                      style="SaveEditorButton.TButton")
        self.save_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.status_label = ttk.Label(action_frame, text="Załaduj plik lub nagraj audio, aby rozpocząć edycję.",
                                      style="Status.Blue.TLabel")
        self.status_label.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Inicjalne wyłączenie kontrolek edycji i odtwarzania
        self._set_editor_controls_state(tk.DISABLED)

    def _set_editor_controls_state(self, state):
        """Ustawia stan kontrolek edycji (suwaków i przycisków odtwarzania/zapisu pliku)."""
        self.speed_scale.config(state=state)
        self.pitch_scale.config(state=state)
        self.play_button.config(state=state)
        self.save_button.config(state=state)
        # Przycisk zatrzymania odtwarzania jest sterowany w play_preview/stop_playback
        # Przyciski nagrywania (record_start/stop) są kontrolowane oddzielnie.

    def _update_record_status_label(self, text, color_name="blue"):
        """Aktualizuje etykietę statusu nagrywania z odpowiednim stylem koloru."""
        self.record_status_label.config(text=text, style=f"Status.{color_name.capitalize()}.TLabel")

    def _update_status_label(self, text, color_name="blue"):
        """Aktualizuje główną etykietę statusu z odpowiednim stylem koloru."""
        self.status_label.config(text=text, style=f"Status.{color_name.capitalize()}.TLabel")

    def load_audio_file(self):
        """Otwiera okno dialogowe wyboru pliku audio i ładuje go do edytora."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Pliki audio", "*.mp3 *.wav *.flac *.ogg *.m4a"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            # Zapewnij, że nagrywanie jest zatrzymane przed załadowaniem nowego pliku
            if self.is_recording_active:
                self.stop_recording()  # Automatycznie zatrzymaj, jeśli nagrywa

            try:
                file_extension = os.path.splitext(file_path)[1].lower()
                if file_extension == '.m4a':  # pydub miewa problemy z m4a, wymagany jest kodek aac
                    self.audio_segment = AudioSegment.from_file(file_path, format="m4a")
                else:
                    self.audio_segment = AudioSegment.from_file(file_path)

                self.audio_file_path = file_path
                self.file_path_label.config(text=f"Załadowano: {os.path.basename(file_path)}", foreground="black")

                # Zresetuj suwaki do wartości domyślnych i zaktualizuj audio
                self.speed_scale.set(1.0)
                self.pitch_scale.set(0)
                self.update_audio()  # Wstępna aktualizacja po załadowaniu
                self._set_editor_controls_state(tk.NORMAL)
                self._update_status_label("Plik załadowany. Dostosuj ustawienia.", "blue")

            except Exception as e:
                messagebox.showerror("Błąd ładowania audio",
                                     f"Nie udało się załadować pliku audio: {e}\nUpewnij się, że FFmpeg jest zainstalowany i jest w PATH.")
                self.audio_segment = None
                self.audio_file_path = None
                self.file_path_label.config(text="Błąd ładowania pliku", fg="red")
                self._set_editor_controls_state(tk.DISABLED)
                self._update_status_label("Błąd ładowania pliku.", "red")
        else:
            self.file_path_label.config(text="Nie wybrano pliku", foreground="gray")
            self._set_editor_controls_state(tk.DISABLED)
            self._update_status_label("Załaduj plik, aby rozpocząć edycję.", "blue")

    # --- Logika nagrywania audio ---
    def start_recording(self):
        """Rozpoczyna nagrywanie audio z mikrofonu."""
        if self.is_recording_active:
            return

        # Wyłącz wszystkie kontrolki edytora i ładowania pliku podczas nagrywania
        self._set_editor_controls_state(tk.DISABLED)
        self.load_button.config(state=tk.DISABLED)

        self.frames = []  # Wyczyść poprzednie nagranie
        self.is_recording_active = True
        self._update_record_status_label("Nagrywam...", "red")
        self.record_start_button.config(state=tk.DISABLED)
        self.record_stop_button.config(state=tk.NORMAL)

        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            # Użyj tych samych ustawień co w _process_recorded_audio dla spójności
            self.audio_stream_record = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,  # Standardowa częstotliwość próbkowania dla nagrań
                input=True,
                frames_per_buffer=1024  # Rozmiar bufora
            )
            self.recording_thread = threading.Thread(target=self._record_audio_loop, daemon=True)
            self.recording_thread.start()
        except Exception as e:
            messagebox.showerror("Błąd nagrywania",
                                 f"Nie udało się rozpocząć nagrywania: {e}\nSprawdź, czy mikrofon jest podłączony i PyAudio działa poprawnie.")
            self.stop_recording()  # Spróbuj zatrzymać i zresetować UI

    def _record_audio_loop(self):
        """Pętla nagrywająca audio w tle."""
        while self.is_recording_active:
            try:
                # exception_on_overflow=False jest ważne, aby uniknąć wyjątków, jeśli bufor się przepełni
                data = self.audio_stream_record.read(1024, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                # Jeśli wystąpi błąd podczas czytania (np. mikrofon odłączony)
                print(f"DEBUG: Błąd podczas nagrywania audio: {e}")
                self.after(0, lambda: messagebox.showerror("Błąd nagrywania", f"Błąd podczas nagrywania: {e}"))
                self.after(0, self.stop_recording)  # Zatrzymaj nagrywanie i zresetuj UI
                break  # Wyjdź z pętli

    def stop_recording(self):
        """Zatrzymuje nagrywanie audio i przetwarza nagrane dane."""
        if not self.is_recording_active:
            return

        self.is_recording_active = False
        self._update_record_status_label("Zatrzymuję...", "orange")
        self.record_start_button.config(state=tk.NORMAL)
        self.record_stop_button.config(state=tk.DISABLED)
        self.load_button.config(state=tk.NORMAL)  # Włącz przycisk ładowania

        if self.audio_stream_record:
            try:
                self.audio_stream_record.stop_stream()
                self.audio_stream_record.close()
                self.pyaudio_instance.terminate()
                self.pyaudio_instance = None
                self.audio_stream_record = None

                # Zapisz nagrane dane do tymczasowego pliku WAV i załaduj je
                self._process_recorded_audio()

            except Exception as e:
                messagebox.showerror("Błąd zatrzymywania nagrywania",
                                     f"Wystąpił błąd podczas zamykania strumienia: {e}")
                self._update_record_status_label("Błąd zatrzymywania.", "red")
            finally:
                # Kontrolki edycji zostaną włączone przez _process_recorded_audio
                # lub tutaj, jeśli audio_stream_record nie istniało (czyli błąd był w start_recording)
                if self.audio_segment is not None or not self.frames:  # Jeśli jest coś do edycji lub nagranie było puste
                    self._set_editor_controls_state(tk.NORMAL)
                self._update_record_status_label("Gotowy do nagrywania.", "blue")
        else:
            self._set_editor_controls_state(tk.NORMAL)  # Włącz edytor, jeśli strumień nie był aktywny

    def _process_recorded_audio(self):
        """Zapisuje nagrane audio do tymczasowego pliku WAV i ładuje je do edytora."""
        if not self.frames:
            self._update_record_status_label("Brak nagranego dźwięku.", "orange")
            self._set_editor_controls_state(tk.DISABLED)  # Nagranie puste, wyłącz edytor
            return

        temp_wav_path = "recorded_audio_temp.wav"

        try:
            # Zapisz do pliku WAV
            wf = wave.open(temp_wav_path, 'wb')
            wf.setnchannels(1)  # Mono
            # Pamiętaj, że pyaudio.paInt16 to 2 bajty, więc setsampwidth to 2
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)  # Częstotliwość próbkowania nagrywania
            wf.writeframes(b''.join(self.frames))
            wf.close()

            # Załaduj nagranie do edytora
            self.audio_segment = AudioSegment.from_wav(temp_wav_path)
            self.audio_file_path = "Nagrane audio"  # Ustaw specjalną ścieżkę dla nagrania
            self.file_path_label.config(text="Nagrano: tymczasowy plik WAV", foreground="black")

            # Zresetuj suwaki i zaktualizuj audio
            self.speed_scale.set(1.0)
            self.pitch_scale.set(0)
            self.update_audio()  # Wstępna aktualizacja po załadowaniu
            self._set_editor_controls_state(tk.NORMAL)  # Włącz kontrolki edycji
            self._update_status_label("Nagranie załadowane. Dostosuj ustawienia.", "blue")
            self._update_record_status_label("Nagrywanie zakończone. Audio gotowe do edycji.", "green")

        except Exception as e:
            messagebox.showerror("Błąd przetwarzania nagrania", f"Nie udało się przetworzyć nagranego audio: {e}")
            self._update_record_status_label("Błąd przetwarzania nagrania.", "red")
            self.audio_segment = None
            self.audio_file_path = None
            self.file_path_label.config(text="Błąd podczas nagrywania", fg="red")  # To jest tk.Label, więc fg OK
            self._set_editor_controls_state(tk.DISABLED)
        finally:
            # Usuń tymczasowy plik WAV po załadowaniu
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)

    def update_audio(self, event=None):
        """Modyfikuje segment audio na podstawie wartości suwaków tempa i wysokości tonu."""
        if self.audio_segment is None:
            return

        current_speed = round(self.speed_scale.get(), 2)
        current_pitch = int(self.pitch_scale.get())

        self.speed_label.config(text=f"{current_speed:.1f}x")
        self.pitch_label.config(text=f"{current_pitch} półtonów")

        # Zastosuj regulację tempa (bez zmiany wysokości tonu)
        if current_speed == 1.0:
            modified_by_speed = self.audio_segment
        else:
            try:
                # Zmiana frame_rate wpływa na tempo i pitch.
                # Ustawiamy frame_rate, a potem ponownie ustawiamy na oryginał,
                # aby pydub użył filtru atempo dla samej zmiany tempa.
                modified_by_speed = self.audio_segment.set_frame_rate(
                    int(self.audio_segment.frame_rate * current_speed))
                modified_by_speed = modified_by_speed.set_frame_rate(self.audio_segment.frame_rate)
            except Exception as e:
                print(f"DEBUG: Błąd przy zmianie tempa pydub: {e}")
                self._update_status_label(f"Błąd zmiany tempa: {e}", "red")
                modified_by_speed = self.audio_segment

        # Zastosuj regulację wysokości tonu (pitch) bez zmiany tempa
        semitones_factor = 2 ** (current_pitch / 12.0)

        try:
            if current_pitch == 0:
                self.modified_audio_segment = modified_by_speed
            else:
                # Tworzymy nowy segment audio z zmodyfikowaną częstotliwością próbkowania
                # co zmienia zarówno pitch jak i tempo.
                pitched_audio_temp = modified_by_speed._spawn(modified_by_speed.raw_data, overrides={
                    "frame_rate": int(modified_by_speed.frame_rate * semitones_factor)
                })
                # Następnie, zmieniamy frame_rate z powrotem na oryginalny,
                # co pydub zinterpretuje jako potrzebę użycia filtru do skorygowania tempa,
                # efektywnie zmieniając tylko pitch.
                self.modified_audio_segment = pitched_audio_temp.set_frame_rate(modified_by_speed.frame_rate)

        except Exception as e:
            print(f"DEBUG: Błąd przy zmianie wysokości tonu pydub: {e}")
            self._update_status_label(f"Błąd zmiany wysokości tonu: {e}", "red")
            self.modified_audio_segment = modified_by_speed

        self.play_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.NORMAL)

    def play_preview(self):
        """Odtwarza zmodyfikowany segment audio."""
        if self.modified_audio_segment is None:
            messagebox.showinfo("Informacja", "Najpierw załaduj lub zmodyfikuj plik audio.")
            return

        self.stop_playback()  # Upewnij się, że poprzednie odtwarzanie jest zatrzymane

        self.play_button.config(state=tk.DISABLED)
        self.stop_play_button.config(state=tk.NORMAL)
        self._update_status_label("Odtwarzam podgląd...", "blue")

        def _play():
            try:
                play(self.modified_audio_segment)
                self.after(0, lambda: self._update_status_label("Odtwarzanie zakończone.", "green"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Błąd odtwarzania",
                                                           f"Nie udało się odtworzyć audio: {e}\nUpewnij się, że FFplay/FFmpeg jest w PATH."))
                self.after(0, lambda: self._update_status_label("Błąd odtwarzania.", "red"))
            finally:
                self.after(0, lambda: self.play_button.config(state=tk.NORMAL))
                self.after(0, lambda: self.stop_play_button.config(state=tk.DISABLED))

        self.playback_thread = threading.Thread(target=_play, daemon=True)
        self.playback_thread.start()

    def stop_playback(self):
        """Symuluje zatrzymanie odtwarzania (pydub nie ma wbudowanej funkcji stop)."""
        if self.playback_thread and self.playback_thread.is_alive():
            messagebox.showinfo("Informacja",
                                "Zatrzymywanie odtwarzania może zająć chwilę, aż do końca bieżącego segmentu.")
            self.play_button.config(state=tk.NORMAL)
            self.stop_play_button.config(state=tk.DISABLED)
            self._update_status_label("Zatrzymywanie odtwarzania...", "orange")

    def save_audio_file(self):
        """Otwiera okno dialogowe zapisu i eksportuje zmodyfikowany plik audio."""
        if self.modified_audio_segment is None:
            messagebox.showinfo("Informacja", "Brak zmodyfikowanego pliku audio do zapisania.")
            return

        file_types = [
            ("Pliki MP3", "*.mp3"),
            ("Pliki WAV", "*.wav"),
            ("Pliki FLAC", "*.flac"),
            ("Pliki OGG", "*.ogg"),
            ("Wszystkie pliki", "*.*"),
        ]
        save_path = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=file_types,
            title="Zapisz zmodyfikowany plik audio jako..."
        )

        if save_path:
            try:
                output_format = os.path.splitext(save_path)[1][1:].lower()
                # Domyślny format, jeśli nie jest w rozpoznawanych
                if output_format not in ["mp3", "wav", "flac", "ogg"]:
                    output_format = "mp3"

                self.modified_audio_segment.export(save_path, format=output_format)
                self._update_status_label(f"Plik zapisano pomyślnie: {os.path.basename(save_path)}", "green")
                messagebox.showinfo("Sukces", "Zmodyfikowany plik audio został zapisany pomyślnie!")
            except Exception as e:
                messagebox.showerror("Błąd zapisu audio",
                                     f"Nie udało się zapisać pliku audio: {e}\nUpewnij się, że FFmpeg obsługuje ten format.")
                self._update_status_label("Błąd zapisu pliku.", "red")
        else:
            self._update_status_label("Zapis anulowany.", "gray")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Edytor Audio")
    root.geometry("600x700")

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both", padx=10, pady=10)

    audio_editor_tab = AudioEditorTab(notebook)
    notebook.add(audio_editor_tab, text="Edytor Audio")

    root.mainloop()