from pathlib import Path
from typing import List
from models.conversion_result import ConversionResult
from utils.file_utils import read_file_safe, count_lines
from utils.cancellation import check_cancelled

class ConverterService:
    """
    Отвечает за преобразование файлов.
    """

    def convert_to_separate_txt(
        self,
        files: List[Path],
        output_folder: Path,
        add_headers: bool = True,
        add_line_numbers: bool = True,
        progress_callback=None,
    ) -> ConversionResult:

        result = ConversionResult(files_found=len(files))

        output_folder.mkdir(parents=True, exist_ok=True)

        for i, file in enumerate(files, 1):

            check_cancelled()

            # Отправляем прогресс
            if progress_callback:
                progress_callback(i, len(files))

            try:
                txt_path = output_folder / (file.stem + ".txt")

                content, _ = read_file_safe(file)

                with open(txt_path, "w", encoding="utf-8") as f:
                    if add_headers:
                        # Добавляем заголовок файла
                        f.write(f"\n===== {file.name} =====\n\n")
                        
                        # Добавляем метаданные
                        metadata = self.get_file_metadata(file)
                        f.write(metadata)
                    
                    if add_line_numbers:
                        content = self.add_line_numbers(content)

                    f.write(content)
                    
                    if not content.endswith("\n"):
                        f.write("\n")

                result.files_converted += 1
                result.created_files.append(txt_path)

            except Exception as e:
                result.errors.append(f"{file}: {str(e)}")
                result.skipped_files.append(file)

        return result

    def convert_to_single_txt(
        self,
        files: List[Path],
        output_file: Path,
        add_headers: bool = True,
        add_line_numbers: bool = True,
        base_folder: Path | None = None,
        progress_callback=None
    ) -> ConversionResult:

        result = ConversionResult(files_found=len(files))

        try:
            with open(output_file, "w", encoding="utf-8") as out:

                files_sorted = sorted(
                    files,
                    key=lambda f: str(f.relative_to(base_folder)) if base_folder else str(f)
                )

                if base_folder:
                    from utils.tree_utils import build_project_tree
                    tree = build_project_tree(files_sorted, base_folder)
                    out.write(tree)

                for i, file in enumerate(files_sorted, 1):

                    check_cancelled()

                    # Отправляем прогресс
                    if progress_callback:
                        progress_callback(i, len(files_sorted))

                    try:

                        if add_headers:

                            if base_folder:
                                relative = file.relative_to(base_folder)
                                header_name = str(relative)
                            else:
                                header_name = file.name

                            out.write(f"\n===== {header_name} =====\n\n")

                            # пишем метаданные
                            metadata = self.get_file_metadata(file)
                            out.write(metadata)

                        content, _ = read_file_safe(file)

                        if add_line_numbers:
                            content = self.add_line_numbers(content)

                        out.write(content)

                        if not content.endswith("\n"):
                            out.write("\n")

                        result.files_converted += 1

                    except Exception as e:
                        result.errors.append(f"{file}: {str(e)}")
                        result.skipped_files.append(file)

            result.created_files.append(output_file)

        except Exception as e:
            result.errors.append(str(e))

        return result

    
    def add_line_numbers(self, text: str) -> str:
        """
        Добавляет нумерацию строк.
        """

        lines = text.splitlines()

        numbered = [
            f"{i+1:04d}: {line}"
            for i, line in enumerate(lines)
        ]

        return "\n".join(numbered)

    def get_file_metadata(self, file: Path) -> str:
        """
        Возвращает строку с метаданными файла.
        Пример:
            Path: services/file_collector.py
            Lines: 184
            Size: 5.2 KB
        """
        try:
            size_kb = file.stat().st_size / 1024
            lines = count_lines(file)
        except Exception:
            size_kb = 0
            lines = 0

        return f"Path: {file}\nLines: {lines}\nSize: {size_kb:.1f} KB\n" + "-"*40 + "\n"
