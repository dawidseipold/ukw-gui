import os
from typing import Any
import requests
from datetime import datetime
from time import sleep
from dotenv import load_dotenv

load_dotenv()


class GladiaFromFileSTT:
    def __init__(self, file_path: str):
        self.api_key: str = os.getenv("GLADIA_API_KEY")
        if not self.api_key:
            raise RuntimeError("Gladia API key not found in environment variables (GLADIA_API_KEY).")

        self.file_path = file_path
        self.base_header = {
            "x-gladia-key": self.api_key,
            "accept": "application/json",
        }

    # WAŻNE: Dodaj obsługę błędów requests i zwracaj None/rzucaj wyjątek
    def makeRequest(self, url, method="GET", data=None, files=None, change_content_type_to_app_json: bool = False) -> \
    dict[str, Any] | None:  # Zmieniono typ zwracany
        headers = self.base_header.copy()

        if change_content_type_to_app_json:
            headers["Content-Type"] = "application/json"

        try:
            if method == "POST":
                response = requests.post(url, headers=headers, json=data, files=files)
            else:
                response = requests.get(url, headers=headers)
            response.raise_for_status()  # Rzuci błąd dla statusów 4xx/5xx
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Błąd zapytania HTTP: {e}")
            return None  # Zamiast exit(1)

    @staticmethod
    def getAudioFileForm(file_path) -> list[Any] | None:
        try:
            file_name, file_extension = os.path.splitext(file_path)
            with open(file_path, "rb") as f:
                file_content = f.read()
            # WAŻNA POPRAWKA: Użyj os.path.basename(file_path) zamiast file_path
            audio_file_form = [("audio", (os.path.basename(file_path), file_content, "audio/" + file_extension[1:]))]
            return audio_file_form
        except FileNotFoundError as err:
            print(f"Błąd: Plik nie został znaleziony - {err}")
            return None  # Zamiast exit(1)
        except Exception as err:
            print(f"Wystąpił błąd podczas przygotowania pliku audio: {err}")
            return None  # Zamiast exit(1)

    def getResultFormRequest(self) -> str | None:  # Zmieniono typ zwracany na str | None
        audio_file_form = self.getAudioFileForm(self.file_path)
        if audio_file_form is None:  # Obsłuż, jeśli getAudioFileForm zwróci None
            return None

        upload_response = self.makeRequest("https://api.gladia.io/v2/upload", method="POST",
                                           files=audio_file_form)  # Użyj audio_file_form
        if upload_response is None or "audio_url" not in upload_response:  # Obsłuż, jeśli makeRequest zwróci None
            print(f"Error: Audio URL not found in upload response\nResponse: {upload_response}.")
            return None  # Zamiast exit(1)

        print("Upload response with File ID:", upload_response)

        audio_url = upload_response.get("audio_url")

        data = {
            "audio_url": audio_url,
            "diarization": True,
        }

        post_response = self.makeRequest("https://api.gladia.io/v2/pre-recorded/", "POST", data=data,
                                         change_content_type_to_app_json=True)
        if post_response is None:  # Obsłuż, jeśli makeRequest zwróci None
            print("Błąd: Brak odpowiedzi po wysłaniu żądania do Gladia API.")
            return None

        print("Sending request to Gladia API...")
        print("Post response with Transcription ID:", post_response)

        result_url = post_response.get("result_url")

        if not result_url:
            print(f"Error: Result URL not found in post response\nResponse: {post_response}.")
            return None  # Zamiast exit(1)
        return result_url

    # WAŻNE: Dodaj update_status_callback do przekazywania statusu do GUI
    def getTranscriptionFormResult(self, result_url, update_status_callback=None) -> list[dict[str, Any]] | None:
        while True:
            poll_response = self.makeRequest(result_url, change_content_type_to_app_json=True)
            if poll_response is None:  # Obsłuż, jeśli makeRequest zwróci None
                print("Błąd: Brak odpowiedzi podczas odpytywania statusu transkrypcji.")
                return None

            status = poll_response.get("status")
            if update_status_callback:  # Wywołaj callback, aby zaktualizować status w GUI
                update_status_callback(f"Status transkrypcji: {status}.")

            match status:
                case "done":
                    transcription_result = poll_response.get("result")
                    if not transcription_result:
                        print("Błąd: Wynik transkrypcji nie znaleziony.")
                        return None
                    transcription_data = transcription_result.get("transcription", {})

                    if not transcription_data:
                        print("Error: Transcription result not found")
                        break  # Wyjście z pętli, ale powinno zwrócić None

                    utterance = transcription_data.get("utterances", [])
                    if not utterance:
                        print(
                            f'Warning: No utterances found in transcription data.\nFull transcription: {transcription_data.get("full_transcription", "")}')
                        # Możesz zdecydować, czy puste utterances to błąd czy po prostu brak mowy
                    return utterance
                case "error":
                    print(f'Transcription failed.\n{poll_response}')
                    return None  # Zamiast break
                case _:
                    print(f'[{datetime.now().strftime("%H:%M:%S")}]Transcription status: {status}.')
            sleep(5)
        return None  # Zwróć None, jeśli pętla zakończy się bez zwrócenia utterance

    # showTranscript nie będzie używane bezpośrednio przez GUI, ale zachowamy je
    @staticmethod
    def showTranscript(utterances) -> None:
        for entry in utterances:
            if isinstance(entry, dict):
                speaker = entry.get("speaker", "Unknown")
                text = entry.get("text", "")
                start = entry.get("start", 0.0)
                end = entry.get("end", 0.0)
                print(f'[{start:06.2f}s - {end:06.2f}s] Speaker {speaker}: {text}')
            else:
                print(f'[Unknown format] {entry}')

    # WAŻNE: Dodaj callbacki do doTranscription i zwracaj wynik
    def doTranscription(self, update_status_callback=None, show_transcript_callback=None) -> list[
                                                                                                 dict[str, Any]] | None:
        try:
            if update_status_callback:
                update_status_callback("Rozpoczynanie transkrypcji...")

            result_url = self.getResultFormRequest()
            if result_url is None:
                if update_status_callback:
                    update_status_callback(
                        "Błąd: Nie udało się uzyskać URL wyniku (prawdopodobnie problem z uploadem).")
                return None

            if update_status_callback:
                update_status_callback("Oczekiwanie na transkrypcję z Gladia API...")
            utterances = self.getTranscriptionFormResult(result_url, update_status_callback)

            if utterances is None:  # Puste utterances to już obsłużone przez getTranscriptionFormResult
                if update_status_callback:
                    update_status_callback("Błąd lub brak transkrypcji.")
                return None

            if show_transcript_callback:  # Wywołaj callback, aby pokazać transkrypcję w GUI
                show_transcript_callback(utterances)

            # input("Press Enter to exit...") # Usuń to dla GUI
            return utterances  # Zwróć utterances
        except Exception as e:
            if update_status_callback:
                update_status_callback(f"Krytyczny błąd w transkrypcji: {e}")
            print(f"Krytyczny błąd w GladiaFromFileSTT.doTranscription: {e}")
            return None