import re
from utils.translator.config import HEADER_PATTERN, TAG_PATTERN, MANUAL_TRANSLATIONS

class LineProcessor:
    def __init__(self):
        self.header_re = re.compile(HEADER_PATTERN)
        self.tag_re = re.compile(TAG_PATTERN)

    def split_header(self, line: str) -> tuple:
        """
        Rozdziela nagłówek (np. [ID]) od reszty linii.
        """
        match = self.header_re.match(line)

        if match:
            return match.group(1), line[match.end():]
        return '', line

    def process_tags(self, text: str, translate_func) -> str:
        """
        Przetwarza znaczniki w tekście, tłumacząc tylko ich zawartość.
        """
        parts = []
        last_pos = 0

        for match in self.tag_re.finditer(text):
            if match.start() > last_pos:
                parts.append(translate_func(text[last_pos:match.start()]))

            opening_tag = match.group(1)
            content = match.group(2)
            closing_tag = match.group(3)

            translated_content = translate_func(content)

            if match.start() > 0 and text[match.start() - 1] == ' ':
                parts.append(' ')

            parts.append(f"{opening_tag}{translated_content}{closing_tag}")

            if match.end() < len(text) and text[match.end()] == ' ':
                parts.append(' ')

            last_pos = match.end()

        if last_pos < len(text):
            parts.append(translate_func(text[last_pos:]))

        return ''.join(parts)

    @staticmethod
    def apply_manual_translations(text: str) -> str:
        """
        Zastępuje frazy zgodnie z ręcznymi tłumaczeniami.
        """
        for phrase, translation in MANUAL_TRANSLATIONS.items():
            text = text.replace(phrase, translation)

        return text