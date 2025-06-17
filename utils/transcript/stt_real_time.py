import os
import json
import pyaudio
import websocket
import sys
import requests
from threading import Thread, Event
from time import sleep, time
from dotenv import load_dotenv

load_dotenv()


class GladiaRealTimeSTT:
    def __init__(self, on_transcription: callable = None,
                 on_status_update: callable = None,
                 input_device_index: int = None):

        self.api_key: str = os.getenv("GLADIA_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "Gladia API key not found in environment variables (GLADIA_API_KEY). Please set it in your .env file.")

        self.SAMPLE_RATE = 16000
        self.CHANNELS = 1
        self.FORMAT = pyaudio.paInt16
        self.CHUNK = 1024

        self.on_transcription = on_transcription or (lambda text: None)
        self.on_status_update = on_status_update or (lambda msg, color: None)
        self.input_device_index = input_device_index
        self.web_socket = None
        self.audio_stream = None
        self.pyaudio_instance = None
        self.is_running = False
        self.stop_event = Event()
        self.sample_count = 0
        self.session_url = None
        self.session_id = None

        self.headers = {
            "Content-Type": "application/json",
            "X-Gladia-Key": self.api_key
        }
        self.body = {
            "encoding": "wav/pcm",
            "sample_rate": self.SAMPLE_RATE,
            "bit_depth": 16,
            "channels": self.CHANNELS
        }

    def initializeSession(self):
        self.on_status_update("Inicjalizowanie sesji Gladia...", "blue")
        try:
            response = requests.post("https://api.gladia.io/v2/live", headers=self.headers, json=self.body)
            if response.status_code == 429:
                error_data = response.json()
                message = error_data.get("message", "Nieznany błąd limitu sesji.")
                full_error = f"Błąd 429: {message}. Twój darmowy plan pozwala na 1 sesję jednocześnie. Odczekaj i spróbuj ponownie."
                print(f"DEBUG: {full_error}. Pełna odpowiedź: {response.text}")
                self.on_status_update(full_error, "red")
                raise ValueError(full_error)

            response.raise_for_status()
            data = response.json()
            self.session_id = data.get("id")
            self.session_url = data.get("url")
            self.on_status_update(f"Sesja zainicjalizowana. ID: {self.session_id}", "blue")
            return self.session_url
        except requests.exceptions.RequestException as e:
            error_message = f"Błąd sieciowy/HTTP podczas inicjalizacji sesji: {e}"
            if hasattr(e, 'response') and e.response is not None:
                error_message += f"\nSzczegóły serwera: {e.response.text}"
            print(f"DEBUG: {error_message}")
            self.on_status_update(f"Błąd inicjalizacji sesji Gladia: {error_message.splitlines()[0]}", "red")
            raise
        except ValueError as e:
            raise e
        except Exception as e:
            print(f"DEBUG: Nieoczekiwany błąd podczas inicjalizacji sesji Gladia: {e}")
            self.on_status_update(f"Błąd inicjalizacji sesji: {e}", "red")
            raise

    def onConnectionOpen(self, ws):
        self.on_status_update("Połączenie WebSocket otwarte.", "green")
        sleep(0.5)
        self.startAudioStream()

    def onMessage(self, ws, message):
        try:
            data = json.loads(message)
            if data.get("type") == "transcript" and "data" in data and "utterance" in data["data"]:
                utterance = data["data"]["utterance"]
                transcription = utterance.get("text", "")
                speaker = data["data"].get("speaker", "Unknown")
                start = utterance.get("start", 0.0)
                end = utterance.get("end", 0.0)
                formatted_text = f'[{start:06.2f}s - {end:06.2f}s] Mówca {speaker}  : {transcription}'
                self.on_transcription(formatted_text)
            elif data.get("type") == "audio_chunk":
                pass
            else:
                pass
        except json.JSONDecodeError:
            print(f"DEBUG: Błąd dekodowania JSON wiadomości WebSocket: {message}")
            self.on_status_update("Błąd dekodowania wiadomości WebSocket.", "red")
        except Exception as e:
            print(f"DEBUG: Nieoczekiwany błąd w onMessage: {e}")
            self.on_status_update(f"Nieoczekiwany błąd w onMessage: {e}", "red")

    def onError(self, ws, error):
        if "Connection is already closed" in str(error) or "connection was closed" in str(error):
            print(f"DEBUG: WebSocket error (połączenie zamknięte): {error}")
            self.on_status_update("WebSocket: Połączenie zostało zamknięte.", "gray")
        else:
            print(f"DEBUG: Krytyczny błąd WebSocket: {error}")
            self.on_status_update(f"Krytyczny błąd WebSocket: {error}", "red")
        self.stopConnection()

    def onClose(self, ws, close_status_code, close_msg):
        print(f"DEBUG: WebSocket connection closed. Status: {close_status_code}, Message: {close_msg}")
        self.on_status_update(f"Połączenie WebSocket zamknięte. Status: {close_status_code}, Wiadomość: {close_msg}",
                              "orange")
        self.stopConnection()

    def startAudioStream(self):
        try:
            self.pyaudio_instance = pyaudio.PyAudio()

            open_params = {
                "format": self.FORMAT,
                "channels": self.CHANNELS,
                "rate": self.SAMPLE_RATE,
                "input": True,
                "frames_per_buffer": self.CHUNK
            }
            if self.input_device_index is not None:
                open_params["input_device_index"] = self.input_device_index
                self.on_status_update(f"Używam urządzenia wejściowego indeks: {self.input_device_index}", "blue")

            self.audio_stream = self.pyaudio_instance.open(**open_params)
            self.on_status_update("Strumień audio otwarty.", "green")
            self.is_running = True
            self.stop_event.clear()
            Thread(target=self.streamAudioToWS, daemon=True).start()
        except Exception as e:  # Może tu być OSError, ale Exception też złapie
            print(f"DEBUG: Błąd uruchamiania strumienia audio (PyAudio): {e}")
            self.on_status_update(f"Błąd uruchamiania strumienia audio: {e}", "red")
            self.stopConnection()

    def streamAudioToWS(self):
        self.on_status_update("Rozpoczynam przesyłanie audio...", "blue")
        self.sample_count = 0
        last_log_time = time()
        while self.is_running and not self.stop_event.is_set():
            try:
                # *** ZMIENIONO: Usunięto 'timeout=0' ***
                # To było powodem błędu TypeError: PyAudio.Stream.read() got an unexpected keyword argument 'timeout'
                data = self.audio_stream.read(self.CHUNK, exception_on_overflow=False)
                self.sample_count += len(data) // 2

                if time() - last_log_time > 5:
                    self.on_status_update(f"Wysłano {self.sample_count // self.SAMPLE_RATE} sekund danych audio.",
                                          "gray")
                    last_log_time = time()

                if self.is_running and self.web_socket and not self.stop_event.is_set():
                    self.web_socket.send(data, opcode=websocket.ABNF.OPCODE_BINARY)

            # *** ZMIENIONO: Złapano ogólniejszy Exception zamiast pyaudio.PyAudioException ***
            # Bo to było powodem AttributeError: module 'pyaudio' has no attribute 'PyAudioException'
            except Exception as e:
                print(f'DEBUG: Błąd podczas przesyłania audio: {e}')
                self.on_status_update(f'Błąd przesyłania audio: {e}', "red")
                self.stopConnection()
                break

    def startConnection(self) -> bool:
        self.on_status_update("Inicjalizuję STT w czasie rzeczywistym...", "blue")
        try:
            self.session_url = self.initializeSession()
            if not self.session_url:
                self.on_status_update("Nie udało się zainicjalizować sesji.", "red")
                print("DEBUG: startConnection: initializeSession zwróciło None. Nie można kontynuować.")
                return False

            self.is_running = True
            self.web_socket = websocket.WebSocketApp(
                self.session_url,
                header=self.headers,
                on_open=self.onConnectionOpen,
                on_message=self.onMessage,
                on_error=self.onError,
                on_close=self.onClose
            )
            Thread(target=self.web_socket.run_forever, daemon=True).start()  # Użycie bez Dispatcher

            self.on_status_update("Wątek WebSocket uruchomiony. Czekam na połączenie...", "blue")
            sleep(1)

            if not self.is_running:
                self.on_status_update(
                    "Inicjalizacja WebSocket nie powiodła się (sprawdź klucz API/połączenie). Zatrzymuję...", "red")
                print(
                    "DEBUG: startConnection: is_running jest False po uruchomieniu WebSocketApp. Coś poszło nie tak (np. onError został wywołany).")
                self.stopConnection()
                return False
            return True

        except ValueError as e:
            print(f"DEBUG: Błąd połączenia (limit sesji Gladia): {e}")
            self.on_status_update(f"Błąd połączenia: {e}", "red")
            self.stopConnection()
            return False
        except Exception as e:
            print(f"DEBUG: Krytyczny błąd w startConnection (np. problem z PyAudio lub Gladia API): {e}")
            self.on_status_update(f"Błąd uruchamiania połączenia: {e}", "red")
            self.stopConnection()
            return False

    def stopConnection(self):
        print("DEBUG: stopConnection: Uruchomiono zatrzymanie. Sprawdzam zasoby...")
        self.on_status_update("Zatrzymuję wszystkie procesy...", "orange")
        self.is_running = False
        self.stop_event.set()

        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
                self.on_status_update("Strumień audio zamknięty.", "orange")
            except Exception as e:
                print(f"DEBUG: Błąd zamykania strumienia audio: {e}")
                self.on_status_update(f"Błąd zamykania strumienia audio: {e}", "red")

        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
                self.pyaudio_instance = None
                self.on_status_update("PyAudio zakończone.", "orange")
            except Exception as e:
                print(f"DEBUG: Błąd zamykania PyAudio: {e}")
                self.on_status_update(f"Błąd zamykania PyAudio: {e}", "red")

        if self.web_socket:
            try:
                print("DEBUG: Zamykam WebSocket (z GladiaRealTimeSTT.stopConnection).")
                self.web_socket.close()
                self.web_socket = None
                self.on_status_update("WebSocket zamknięty.", "orange")
            except Exception as e:
                print(f"DEBUG: Błąd zamykania WebSocket: {e}")
                self.on_status_update(f"Błąd zamykania WebSocket: {e}", "red")

        self.on_status_update("Wszystkie zasoby zamknięte.", "green")

    def run(self):
        try:
            success = self.startConnection()
            if not success:
                self.on_status_update("Nie udało się uruchomić połączenia Gladia.", "red")
                print("DEBUG: run(): startConnection zwróciło False. Sprawdź powyższe logi.")
                return
        except RuntimeError as e:
            self.on_status_update(f"Błąd konfiguracji: {e}", "red")
            print(f"DEBUG: run(): Wyjątek RuntimeError (prawdopodobnie brak klucza API): {e}")
        except Exception as e:
            self.on_status_update(f"Wystąpił nieoczekiwany błąd w run(): {e}", "red")
            print(f"DEBUG: run(): Nieoczekiwany wyjątek w run(): {e}")
            self.stopConnection()
        finally:
            pass