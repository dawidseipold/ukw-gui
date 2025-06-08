from langdetect import detect

def detect_language(text):
    if not text or len(text.strip()) < 10:
        return "unknown"
    try:
        return detect(text)
    except:
        return "unknown"