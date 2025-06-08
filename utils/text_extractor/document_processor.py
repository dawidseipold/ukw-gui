import os
import glob
from datetime import datetime
from utils.text_extractor.extractors.pdf_extractor import extract_text_from_pdf
from utils.text_extractor.extractors.docx_extractor import extract_text_from_docx
from utils.text_extractor.extractors.image_extractor import extract_text_from_image
from utils.text_extractor.language_detector import detect_language
from utils.text_extractor.report_generator import generate_text_report
import csv

class DocumentProcessor:
    def __init__(self, output_dir="output", generate_report=True):
        self.output_dir = output_dir
        self.generate_report = generate_report
        self.processed_files = []

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def process_pdf(self, file_path):
        try:
            text = extract_text_from_pdf(file_path)
            word_count = len(text.split())
            self.processed_files.append({
                "file_name": os.path.basename(file_path),
                "file_type": "PDF",
                "extraction_method": "pdfplumber",
                "word_count": word_count,
                "language": detect_language(text),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return text
        except Exception as e:
            print(f"Błąd podczas przetwarzania pliku PDF {file_path}: {e}")
            return ""

    def process_docx(self, file_path):
        try:
            text = extract_text_from_docx(file_path)
            word_count = len(text.split())
            self.processed_files.append({
                "file_name": os.path.basename(file_path),
                "file_type": "DOCX",
                "extraction_method": "python-docx",
                "word_count": word_count,
                "language": detect_language(text),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return text
        except Exception as e:
            print(f"Błąd podczas przetwarzania pliku DOCX {file_path}: {e}")
            return ""

    def process_image(self, file_path):
        try:
            text, detected_lang = extract_text_from_image(file_path)
            word_count = len(text.split())
            self.processed_files.append({
                "file_name": os.path.basename(file_path),
                "file_type": os.path.splitext(file_path)[1].upper()[1:],
                "extraction_method": "OCR (Tesseract)",
                "word_count": word_count,
                "language": detect_language(text),
                "ocr_language": detected_lang,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return text
        except Exception as e:
            print(f"Błąd podczas przetwarzania obrazu {file_path}: {e}")
            return ""

    def process_file(self, file_path):
        """
        Przetwarza pojedynczy plik i zapisuje jego zawartość do pliku wyjściowego.
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.pdf':
            text = self.process_pdf(file_path)
        elif file_ext == '.docx':
            text = self.process_docx(file_path)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp']:
            text = self.process_image(file_path)
        else:
            print(f"Nieobsługiwany format pliku: {file_path}")
            return ""

        # Zapisanie tekstu do pliku wyjściowego
        if text:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(self.output_dir, f"{base_name}.txt")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Zapisano tekst do pliku: {output_path}")

    def process_batch(self, file_pattern):
        """
        Przetwarza wiele plików jednocześnie.
        """
        files = glob.glob(file_pattern)
        if not files:
            print(f"Nie znaleziono plików pasujących do wzorca: {file_pattern}")
            return

        for file_path in files:
            print(f"Przetwarzanie pliku: {file_path}")
            self.process_file(file_path)

    def generate_report_file(self):
        """
        Generowanie raportu z przetwarzania dokumentów w formatach TXT i CSV.
        """
        if not self.processed_files:
            print("Brak przetworzonych plików do wygenerowania raportu.")
            return

        # Generowanie raportu TXT
        report_txt_path = os.path.join(self.output_dir, "processing_report.txt")
        with open(report_txt_path, 'w', encoding='utf-8') as f:
            f.write(generate_text_report(self.processed_files))
        print(f"Wygenerowano raport tekstowy: {report_txt_path}")

        # Generowanie raportu CSV
        report_csv_path = os.path.join(self.output_dir, "processing_report.csv")
        with open(report_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = self.processed_files[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for file_info in self.processed_files:
                writer.writerow(file_info)
        print(f"Wygenerowano raport CSV: {report_csv_path}")