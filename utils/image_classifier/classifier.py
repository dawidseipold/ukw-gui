import os
from PIL import Image, UnidentifiedImageError
from utils.image_classifier.model_loader import load_model

def classify_image(image_path, model, feature_extractor):
    """
    Klasyfikuje pojedynczy obraz za pomocą modelu ViT.

    Args:
        image_path (str): Ścieżka do obrazu.
        model: Załadowany model ViT.
        feature_extractor: Feature extractor dla modelu ViT.

    Returns:
        str: Nazwa klasy przewidzianej przez model.
    """
    try:
        image = Image.open(image_path).convert("RGB")
        inputs = feature_extractor(images=image, return_tensors="pt")
        outputs = model(**inputs)
        predicted_class = outputs.logits.argmax(-1).item()
        return model.config.id2label[predicted_class]
    except UnidentifiedImageError:
        return "Błąd: nie można zidentyfikować pliku jako obrazu"
    except Exception as e:
        return f"Błąd: {str(e)}"

def process_images(input_path, output_path):
    """
    Przetwarza obrazy z listy plików lub folderu i zapisuje wyniki klasyfikacji do pliku tekstowego.

    Args:
        input_path (str or list): Ścieżka do folderu z obrazami lub lista plików.
        output_path (str): Ścieżka do pliku wynikowego.
    """
    try:
        model, feature_extractor = load_model()
        results = {}

        if isinstance(input_path, list):
            files = input_path
        elif isinstance(input_path, str) and os.path.isdir(input_path):
            files = [os.path.join(input_path, file_name) for file_name in os.listdir(input_path)]
        else:
            raise ValueError("Nieprawidłowa ścieżka wejściowa. Oczekiwano folderu lub listy plików.")

        for file_path in files:
            if not file_path.lower().endswith((".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp")):
                continue

            predicted_class = classify_image(file_path, model, feature_extractor)
            results[os.path.basename(file_path)] = predicted_class

        with open(output_path, "w", encoding="utf-8") as f:
            for file_name, predicted_class in results.items():
                f.write(f"{file_name}: {predicted_class}\n")

        return results
    except Exception as e:
        raise Exception(f"Błąd podczas przetwarzania obrazów: {str(e)}")