import pytesseract
from PIL import Image

def extract_text_from_image(file_path):
    image = Image.open(file_path)
    text_eng = pytesseract.image_to_string(image, lang='eng')
    text_pol = pytesseract.image_to_string(image, lang='pol')
    if len(text_eng) > len(text_pol):
        return text_eng, "eng"
    else:
        return text_pol, "pol"