# eleven_labs_tts.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()


class ElevenLabsTTS:  # Zmieniono nazwę na ElevenLabsTTS, aby było bardziej precyzyjne
    def __init__(self, api_key: str, voice_id: str, text: str, speed: float = 1.0, stability: float = 0.5,
                 similarity: float = 0.5):
        """
        Inicjalizuje klienta Text-to-Speech dla Eleven Labs.
        :param api_key: Klucz API Eleven Labs.
        :param voice_id: ID wybranego głosu.
        :param text: Tekst do syntezy mowy.
        :param speed: Prędkość mowy (0.7 do 1.2).
        :param stability: Stabilność głosu (niższa dla większej emocjonalności).
        :param similarity: Stopień podobieństwa do oryginalnego głosu.
        """
        if not api_key:
            raise ValueError("Eleven Labs API key is required.")  # Zmieniono RuntimeError na ValueError

        self.api_key = api_key
        self.voice_id = voice_id
        self.text = text

        # Sprawdź zakres prędkości
        if not (0.7 <= speed <= 1.2):
            # Użyj wartości domyślnej, jeśli poza zakresem, lub rzuć błąd
            print(f"DEBUG: Prędkość ({speed}) poza zakresem [0.7, 1.2]. Używam 1.0.")
            self.speed = 1.0
        else:
            self.speed = speed

        self.stability = stability
        self.similarity = similarity

        self.url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"
        self.headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }

        self.data = {
            "text": self.text,
            "model_id": "eleven_monolingual_v1",  # Standardowy model
            "voice_settings": {
                "stability": self.stability,
                "similarity_boost": self.similarity,
                # Speed nie jest bezpośrednio w voice_settings w API Eleven Labs w ten sposób,
                # ale jako osobny parametr w requests.
                # Niestety API ElevenLabs V1 nie ma 'speed' w voice_settings
                # Zostawię to, ale API może to ignorować.
                # Bardziej zaawansowana kontrola prędkości wymaga V2 API lub innej obróbki.
            },
        }
        # Prędkość w ElevenLabs API V1 nie jest kontrolka w voice_settings,
        # lecz elementem dla "voice_tuning" w starszych wersjach API lub jako post-processing.
        # W nowszych wersjach API Eleven Labs (np. v2) kontrola tempa jest dostępna jako 'model_id' (np. 'eleven_turbo_v2' + "rate" w params)
        # Biorąc pod uwagę dostarczony kod, który używa "eleven_monolingual_v1",
        # parametr "speed" w `voice_settings` prawdopodobnie nie będzie miał wpływu.
        # Aby to działało, musiałbyś użyć API V2 i/lub innego podejścia.
        # Na razie zostawimy speed jako parametr, ale ostrzegamy o jego efektywności.

    def make_request(self):
        """
        Wykonuje żądanie POST do API Eleven Labs, aby uzyskać strumień audio.
        Zwraca obiekt odpowiedzi requests.
        """
        try:
            # W API V1 speed nie jest w voice_settings, ale może być opcją w innych modelach/wersjach API.
            # Jeśli chcemy to obsłużyć, musielibyśmy rozbudować `self.data` lub URL params.
            # Dla ElevenLabs V1 z eleven_monolingual_v1 speed jest poza voice_settings lub nie jest obsługiwany w ten sposób.
            # Prosta prędkość w TTS jest rzadko modyfikowana w API V1 w ten sposób, częściej jako część modelu.

            # W API Eleven Labs V1, kontrola 'speed' jest bardziej złożona.
            # Zwykle to 'model_id' (np. 'eleven_turbo_v2') i opcjonalny 'rate' parameter
            # dla wybranych modeli. Dla 'eleven_monolingual_v1' podanego w przykładzie,
            # 'speed' w 'voice_settings' jest ignorowany.

            response = requests.post(self.url, json=self.data, headers=self.headers, stream=True)
            response.raise_for_status()  # Rzuca błąd dla statusów 4xx/5xx
            return response
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Błąd zapytania Eleven Labs TTS: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"DEBUG: Odpowiedź serwera: {e.response.text}")
            raise