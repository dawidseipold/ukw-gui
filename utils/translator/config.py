import os
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

# Konfiguracja API Hugging Face
HUGGING_FACE_API_URL = "https://api-inference.huggingface.co/models/facebook/mbart-large-50-many-to-many-mmt"
HUGGING_FACE_API_TOKEN = os.getenv("HUGGING_FACE_API_TOKEN")  # Pobierz klucz API z .env

# Języki tłumaczenia
SOURCE_LANG = "en_XX"
TARGET_LANG = "pl_PL"

# Wzorce do przetwarzania tekstu
HEADER_PATTERN = r'^(\[[^\]]+\]\s*)'  # Wzorzec dla nagłówków (np. [ID])
TAG_PATTERN = r'(\{g\|[^}]+\})(.*?)(\{/g\})'  # Wzorzec dla znaczników (np. {g|...}...{/g})

# Ręczne tłumaczenia (idiomy i specyficzne frazy)
MANUAL_TRANSLATIONS = {
    "A rolling stone gathers no moss": "Toczący się kamień mchu nie narasta",
    "wise men": "mędrcy",
    "know when to settle": "wiedzą kiedy osiąść"
}