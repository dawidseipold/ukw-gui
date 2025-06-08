from utils.translator.loader import translate_text_via_api
from utils.translator.config import SOURCE_LANG, TARGET_LANG
from utils.translator.line_processor import LineProcessor
from utils.translator.file_handler import FileHandler

class Translator:
    def __init__(self):
        self.processor = LineProcessor()

    def translate_segment(self, text: str) -> str:
        """
        Tłumaczy pojedynczy segment tekstu.
        """
        if not text.strip():
            return text

        text = self.processor.apply_manual_translations(text)
        return translate_text_via_api(text, SOURCE_LANG, TARGET_LANG)

    def process_line(self, line: str) -> str:
        """
        Przetwarza pojedynczą linię tekstu, zachowując znaczniki i nagłówki.
        """
        header, content = self.processor.split_header(line)
        processed_content = self.processor.process_tags(content, self.translate_segment)

        return f"{header}{processed_content}"

    def process_file(self, input_path: str, output_path: str):
        """
        Przetwarza cały plik wejściowy i zapisuje wynik do pliku wyjściowego.
        """
        FileHandler.process_files(self.process_line, input_path, output_path)

    def process_file_with_progress(self, input_path: str, output_path: str, update_progress):
        """
        Przetwarza plik wejściowy linia po linii z aktualizacją postępu.
        """
        lines = []
        processed_lines = 0

        with open(input_path, 'r', encoding='utf-8') as f_in:
            for line in f_in:
                processed_line = self.process_line(line.rstrip('\n'))
                lines.append(processed_line)
                processed_lines += 1
                update_progress(processed_lines)

        with open(output_path, 'w', encoding='utf-8') as f_out:
            for line in lines:
                f_out.write(f"{line}\n")