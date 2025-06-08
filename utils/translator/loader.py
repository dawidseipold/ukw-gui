import requests
from utils.translator.config import HUGGING_FACE_API_URL, HUGGING_FACE_API_TOKEN, SOURCE_LANG, TARGET_LANG

def translate_text_via_api(text: str, source_lang: str, target_lang: str) -> str:
    """
    Wysyła zapytanie do API Hugging Face w celu przetłumaczenia tekstu.
    """
    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_API_TOKEN}"
    }
    payload = {
        "inputs": text,
        "parameters": {
            "src_lang": source_lang,  # Dodano język źródłowy
            "tgt_lang": target_lang  # Dodano język docelowy
        }
    }

    response = requests.post(HUGGING_FACE_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        return result[0]["translation_text"]
    else:
        raise Exception(f"Błąd API Hugging Face: {response.status_code} - {response.text}")