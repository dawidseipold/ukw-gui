from transformers import ViTImageProcessor, ViTForImageClassification
from utils.image_classifier.config import HUGGING_FACE_API_TOKEN, MODEL_NAME

def load_model():
    """
    Ładuje model ViT z Hugging Face.
    """
    try:
        if not HUGGING_FACE_API_TOKEN:
            raise ValueError("Token Hugging Face nie został ustawiony w pliku .env.")

        model = ViTForImageClassification.from_pretrained(MODEL_NAME, token=HUGGING_FACE_API_TOKEN)
        feature_extractor = ViTImageProcessor.from_pretrained(MODEL_NAME)

        return model, feature_extractor
    except Exception as e:
        raise Exception(f"Błąd podczas ładowania modelu: {str(e)}")