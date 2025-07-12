import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
from pydub import AudioSegment
from pydub.playback import play
from dotenv import load_dotenv
from utils.tts.tts_elevenlabs import ElevenLabsTTS

load_dotenv()


class TTSTab(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.eleven_labs_api_key = os.getenv("ELEVEN_LABS_API_KEY")
        if not self.eleven_labs_api_key:
            messagebox.showerror("Błąd konfiguracji",
                                 "Klucz API Eleven Labs (ELEVEN_LABS_API_KEY) nie znaleziono w pliku .env.")
            self.api_key_available = False
        else:
            self.api_key_available = True

        self.output_audio_segment = None
        self.playback_thread = None
        self.output_file_path = "tts_output.mp3"

        self.voice_options = {
            "Bill": "pqHfZKP75CvOlQylNhV4",
            "Alice": "Xb7hH8MSUJpSbSDYk0k2",
            "Brian": "nPczCjzI2devNBz1zQrb",
            "Callum": "N2lVS1w4EtoT3dr4eOWO",
            "Aria": "9BWtsMINqrJLrRacOk9x"
        }
        self.selected_voice_name = tk.StringVar(value="Brian")

        self.create_widgets()
        self.setup_styles()

        self._set_controls_state(tk.DISABLED if not self.api_key_available else tk.NORMAL)

    def setup_styles(self):
        style = ttk.Style()

        style.configure("TButton", font=("Arial", 10, "bold"))
        style.map("TButton", background=[("disabled", "#e0e0e0")], foreground=[("disabled", "#808080")])

        style.configure("GenerateButton.TButton", background="#4CAF50", foreground="white")
        style.map("GenerateButton.TButton", background=[("!disabled", "#4CAF50")])

        style.configure("PlayTTSButton.TButton", background="#2196F3", foreground="white")
        style.map("PlayTTSButton.TButton", background=[("!disabled", "#2196F3")])

        style.configure("SaveTTSButton.TButton", background="#FFC107", foreground="black")
        style.map("SaveTTSButton.TButton", background=[("!disabled", "#FFC107")])

        style.configure("TLabel", font=("Arial", 10))
        style.configure("Status.TLabel", font=("Arial", 10, "italic"))
        style.configure("Status.Blue.TLabel", foreground="blue")
        style.configure("Status.Green.TLabel", foreground="green")
        style.configure("Status.Red.TLabel", foreground="red")
        style.configure("Status.Orange.TLabel", foreground="orange")

    def create_widgets(self):
        self.label = ttk.Label(self, text="Synteza Mowy (Text-to-Speech) - Eleven Labs", font=("Arial", 16, "bold"))
        self.label.pack(pady=15)

        text_frame = ttk.LabelFrame(self, text="Wprowadź Tekst", padding=15)
        text_frame.pack(pady=10, padx=20, fill="x", expand=False)
        self.text_input = tk.Text(text_frame, wrap="word", height=5, width=60, font=("Arial", 10))
        self.text_input.pack(fill="both", expand=True)
        self.text_input.insert(tk.END, "Wpisz tutaj tekst do syntezy mowy...")

        controls_frame = ttk.LabelFrame(self, text="Ustawienia Głosu i Mowy", padding=15)
        controls_frame.pack(pady=10, padx=20, fill="x", expand=False)
        controls_frame.columnconfigure(1, weight=1)

        ttk.Label(controls_frame, text="Wybierz Głos:", style="TLabel").grid(row=0, column=0, padx=5, pady=5,
                                                                             sticky="w")
        self.voice_menu = ttk.OptionMenu(controls_frame, self.selected_voice_name, self.selected_voice_name.get(),
                                         *self.voice_options.keys())
        self.voice_menu.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        ttk.Label(controls_frame, text="Prędkość (0.7-1.2):", style="TLabel").grid(row=1, column=0, padx=5, pady=5,
                                                                                   sticky="w")
        self.speed_label = ttk.Label(controls_frame, text="1.0", style="TLabel")  # <--- WIDŻET TWORZONY WCZEŚNIEJ
        self.speed_label.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.speed_scale = ttk.Scale(controls_frame, from_=0.7, to_=1.2, orient="horizontal", length=200,
                                     command=self._update_speed_label)
        self.speed_scale.set(1.0)
        self.speed_scale.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(controls_frame, text="Stabilność (0.0-1.0):", style="TLabel").grid(row=2, column=0, padx=5, pady=5,
                                                                                     sticky="w")
        self.stability_label = ttk.Label(controls_frame, text="0.5", style="TLabel")  # <--- WIDŻET TWORZONY WCZEŚNIEJ
        self.stability_label.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.stability_scale = ttk.Scale(controls_frame, from_=0.0, to_=1.0, orient="horizontal", length=200,
                                         command=self._update_stability_label)
        self.stability_scale.set(0.5)
        self.stability_scale.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(controls_frame, text="Podobieństwo (0.0-1.0):", style="TLabel").grid(row=3, column=0, padx=5, pady=5,
                                                                                       sticky="w")
        self.similarity_label = ttk.Label(controls_frame, text="0.5", style="TLabel")  # <--- WIDŻET TWORZONY WCZEŚNIEJ
        self.similarity_label.grid(row=3, column=2, padx=5, pady=5, sticky="w")
        self.similarity_scale = ttk.Scale(controls_frame, from_=0.0, to_=1.0, orient="horizontal", length=200,
                                          command=self._update_similarity_label)
        self.similarity_scale.set(0.5)
        self.similarity_scale.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        action_frame = ttk.LabelFrame(self, text="Akcje", padding=15)
        action_frame.pack(pady=10, padx=20, fill="x", expand=False)
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)
        action_frame.columnconfigure(2, weight=1)

        self.generate_button = ttk.Button(action_frame, text="Generuj Mowę", command=self.generate_speech,
                                          style="GenerateButton.TButton")
        self.generate_button.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        self.play_button = ttk.Button(action_frame, text="Odtwórz", command=self.play_generated_audio,
                                      state=tk.DISABLED, style="PlayTTSButton.TButton")
        self.play_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.stop_play_button = ttk.Button(action_frame, text="Zatrzymaj Odtwarzanie", command=self.stop_playback,
                                           state=tk.DISABLED, style="PlayTTSButton.TButton")
        self.stop_play_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.save_button = ttk.Button(action_frame, text="Zapisz Audio", command=self.save_generated_audio,
                                      state=tk.DISABLED, style="SaveTTSButton.TButton")
        self.save_button.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        self.status_label = ttk.Label(self, text="Wpisz tekst i kliknij 'Generuj Mowę'.", style="Status.Blue.TLabel")
        self.status_label.pack(pady=10)

    def _set_controls_state(self, state):
        self.text_input.config(state=state)
        self.voice_menu.config(state=state)
        self.speed_scale.config(state=state)
        self.stability_scale.config(state=state)
        self.similarity_scale.config(state=state)
        self.generate_button.config(state=state)

    def _update_speed_label(self, event=None):
        self.speed_label.config(text=f"{self.speed_scale.get():.1f}")

    def _update_stability_label(self, event=None):
        self.stability_label.config(text=f"{self.stability_scale.get():.1f}")

    def _update_similarity_label(self, event=None):
        self.similarity_label.config(text=f"{self.similarity_scale.get():.1f}")

    def _update_status_label(self, text, color_name="blue"):
        self.status_label.config(text=text, style=f"Status.{color_name.capitalize()}.TLabel")

    def generate_speech(self):
        if not self.api_key_available:
            messagebox.showerror("Błąd", "Klucz API Eleven Labs nie jest dostępny. Sprawdź plik .env.")
            return

        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Brak tekstu", "Proszę wprowadzić tekst do syntezy mowy.")
            return

        selected_voice_id = self.voice_options[self.selected_voice_name.get()]
        speed = round(self.speed_scale.get(), 1)
        stability = round(self.stability_scale.get(), 1)
        similarity = round(self.similarity_scale.get(), 1)

        self._update_status_label("Generuję mowę...", "blue")
        self.generate_button.config(state=tk.DISABLED)
        self.play_button.config(state=tk.DISABLED)
        self.stop_play_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)

        threading.Thread(target=self._run_tts_generation,
                         args=(text, selected_voice_id, speed, stability, similarity)).start()

    def _run_tts_generation(self, text, voice_id, speed, stability, similarity):
        try:
            tts_client = ElevenLabsTTS(self.eleven_labs_api_key, voice_id, text, speed, stability, similarity)
            response = tts_client.make_request()

            if response.status_code == 200:
                temp_audio_path = "temp_tts_output.mp3"
                with open(temp_audio_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)

                self.output_audio_segment = AudioSegment.from_file(temp_audio_path, format="mp3")
                self.output_file_path = temp_audio_path

                self.after(0, lambda: self._update_status_label("Mowa wygenerowana pomyślnie!", "green"))
                self.after(0, lambda: self.play_button.config(state=tk.NORMAL))
                self.after(0, lambda: self.save_button.config(state=tk.NORMAL))
            else:
                error_msg = f"Błąd generowania mowy: {response.status_code} - {response.text[:200]}..."
                self.after(0, lambda: self._update_status_label(error_msg, "red"))
                self.after(0, lambda: messagebox.showerror("Błąd generowania", error_msg))
        except Exception as e:
            error_msg = f"Wystąpił błąd: {e}"
            self.after(0, lambda: self._update_status_label(error_msg, "red"))
            self.after(0, lambda: messagebox.showerror("Błąd", error_msg))
        finally:
            self.after(0, lambda: self.generate_button.config(state=tk.NORMAL))

    def play_generated_audio(self):
        if self.output_audio_segment is None:
            messagebox.showinfo("Brak audio", "Najpierw wygeneruj mowę.")
            return

        self.stop_playback()

        self.play_button.config(state=tk.DISABLED)
        self.stop_play_button.config(state=tk.NORMAL)
        self._update_status_label("Odtwarzam wygenerowaną mowę...", "blue")

        def _play_audio():
            try:
                play(self.output_audio_segment)
                self.after(0, lambda: self._update_status_label("Odtwarzanie zakończone.", "green"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Błąd odtwarzania",
                                                           f"Nie udało się odtworzyć audio: {e}\nUpewnij się, że FFplay/FFmpeg jest w PATH."))
                self.after(0, lambda: self._update_status_label("Błąd odtwarzania.", "red"))
            finally:
                self.after(0, lambda: self.play_button.config(state=tk.NORMAL))
                self.after(0, lambda: self.stop_play_button.config(state=tk.DISABLED))

        self.playback_thread = threading.Thread(target=_play_audio, daemon=True)
        self.playback_thread.start()

    def stop_playback(self):
        if self.playback_thread and self.playback_thread.is_alive():
            messagebox.showinfo("Informacja",
                                "Zatrzymywanie odtwarzania może zająć chwilę, aż do końca bieżącego segmentu.")
            self.play_button.config(state=tk.NORMAL)
            self.stop_play_button.config(state=tk.DISABLED)
            self._update_status_label("Zatrzymywanie odtwarzania...", "orange")

    def save_generated_audio(self):
        if self.output_audio_segment is None:
            messagebox.showinfo("Brak audio", "Najpierw wygeneruj mowę, aby ją zapisać.")
            return

        file_types = [
            ("Pliki MP3", "*.mp3"),
            ("Pliki WAV", "*.wav"),
            ("Wszystkie pliki", "*.*"),
        ]
        save_path = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=file_types,
            title="Zapisz wygenerowane audio jako..."
        )

        if save_path:
            try:
                output_format = os.path.splitext(save_path)[1][1:].lower()
                if output_format not in ["mp3", "wav"]:
                    output_format = "mp3"

                self.output_audio_segment.export(save_path, format=output_format)
                self._update_status_label(f"Plik zapisano pomyślnie: {os.path.basename(save_path)}", "green")
                messagebox.showinfo("Sukces", "Wygenerowany plik audio został zapisany pomyślnie!")
            except Exception as e:
                messagebox.showerror("Błąd zapisu audio",
                                     f"Nie udało się zapisać pliku audio: {e}\nUpewnij się, że FFmpeg obsługuje ten format.")
                self._update_status_label("Błąd zapisu pliku.", "red")
        else:
            self._update_status_label("Zapis anulowany.", "gray")

        if os.path.exists(self.output_file_path) and self.output_file_path != "tts_output.mp3":
            try:
                os.remove(self.output_file_path)
            except Exception as e:
                print(f"DEBUG: Nie udało się usunąć tymczasowego pliku {self.output_file_path}: {e}")

        self.output_file_path = "tts_output.mp3"

    def _cleanup_temp_files(self):
        if os.path.exists("temp_tts_output.mp3"):
            try:
                os.remove("temp_tts_output.mp3")
                print("DEBUG: Usunięto tymczasowy plik audio.")
            except Exception as e:
                print(f"DEBUG: Nie udało się usunąć temp_tts_output.mp3: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Synteza Mowy Eleven Labs")
    root.geometry("700x750")

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both", padx=10, pady=10)

    tts_tab = TTSTab(notebook)
    notebook.add(tts_tab, text="Synteza Mowy")

    root.protocol("WM_DELETE_WINDOW", lambda: (tts_tab._cleanup_temp_files(), root.destroy()))

    root.mainloop()