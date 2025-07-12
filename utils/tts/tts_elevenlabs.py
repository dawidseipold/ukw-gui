import requests
import os
from dotenv import load_dotenv

load_dotenv()


class ElevenLabsTTS:
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

        if not (0.7 <= speed <= 1.2):
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
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": self.stability,
                "similarity_boost": self.similarity,
            },
        }

    def make_request(self):
        """
        Wykonuje żądanie POST do API Eleven Labs, aby uzyskać strumień audio.
        Zwraca obiekt odpowiedzi requests.
        """
        try:
            response = requests.post(self.url, json=self.data, headers=self.headers, stream=True)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Błąd zapytania Eleven Labs TTS: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"DEBUG: Odpowiedź serwera: {e.response.text}")
            raise