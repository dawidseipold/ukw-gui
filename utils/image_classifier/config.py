import os
from dotenv import load_dotenv

load_dotenv()

HUGGING_FACE_API_TOKEN = os.getenv("HUGGING_FACE_API_TOKEN")
MODEL_NAME = "google/vit-base-patch16-224"