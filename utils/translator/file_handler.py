class FileHandler:
    @staticmethod
    def process_files_in_batches(process_batch_function, input_path: str, output_path: str, batch_size: int = 10):
        """
        Przetwarza plik wejściowy w partiach i zapisuje wynik do pliku wyjściowego.
        """
        lines = []
        batch = []

        # Przetwarzanie pliku wejściowego
        with open(input_path, 'r', encoding='utf-8') as f_in:
            for line in f_in:
                batch.append(line.rstrip('\n'))
                if len(batch) == batch_size:
                    processed_batch = process_batch_function(batch)
                    lines.extend(processed_batch)
                    batch = []

            # Przetwarzanie pozostałych linii
            if batch:
                processed_batch = process_batch_function(batch)
                lines.extend(processed_batch)

        # Zapis do pliku wyjściowego
        with open(output_path, 'w', encoding='utf-8') as f_out:
            for line in lines:
                f_out.write(f"{line}\n")