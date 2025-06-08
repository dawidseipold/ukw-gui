from datetime import datetime
from collections import Counter

def generate_text_report(processed_files):
    if not processed_files:
        return "Brak przetworzonych plików."

    report = "RAPORT Z PRZETWARZANIA DOKUMENTÓW\n"
    report += "=" * 50 + "\n\n"
    report += f"Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"Liczba przetworzonych plików: {len(processed_files)}\n\n"
    report += "PODSUMOWANIE:\n"
    report += "-" * 50 + "\n"

    file_types = Counter([file_info['file_type'] for file_info in processed_files])
    report += "Według typu pliku:\n"
    for file_type, count in file_types.items():
        report += f"  - {file_type}: {count} plików\n"

    extraction_methods = Counter([file_info['extraction_method'] for file_info in processed_files])
    report += "\nWedług metody ekstrakcji:\n"
    for method, count in extraction_methods.items():
        report += f"  - {method}: {count} plików\n"

    languages = Counter([file_info['language'] for file_info in processed_files])
    report += "\nWedług wykrytego języka:\n"
    for lang, count in languages.items():
        report += f"  - {lang}: {count} plików\n"

    report += "\nSZCZEGÓŁY PRZETWORZONYCH PLIKÓW:\n"
    report += "-" * 50 + "\n"
    for i, file_info in enumerate(processed_files, 1):
        report += f"{i}. {file_info['file_name']}\n"
        report += f"   Typ pliku: {file_info['file_type']}\n"
        report += f"   Metoda ekstrakcji: {file_info['extraction_method']}\n"
        report += f"   Liczba słów: {file_info['word_count']}\n"
        report += f"   Wykryty język: {file_info['language']}\n"
        if 'ocr_language' in file_info:
            report += f"   Język OCR: {file_info['ocr_language']}\n"
        report += f"   Czas przetworzenia: {file_info['timestamp']}\n\n"

    return report