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
    ) -> ConversionResult:

        result = ConversionResult(files_found=len(files))

        output_folder.mkdir(parents=True, exist_ok=True)

        for file in files:

            check_cancelled()

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
        base_folder: Path | None = None
    ) -> ConversionResult:

        result = ConversionResult(files_found=len(files))

        try:
            with open(output_file, "w", encoding="utf-8") as out:

                files_sorted = sorted(
                    files,
                    key=lambda f: str(f.relative_to(base_folder)) if base_folder else str(f)
                )

                if base_folder:
                    tree = self.build_project_tree(files_sorted, base_folder)
                    out.write(tree)

                for file in files_sorted:

                    check_cancelled()

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

    def build_project_tree(self, files: List[Path], base_folder: Path) -> str:
        """
        Строит текстовое дерево проекта с правильной структурой папок.
        """
        from collections import defaultdict
        
        # Группируем файлы по папкам
        folder_structure = defaultdict(list)
        
        for file in files:
            try:
                relative = file.relative_to(base_folder)
            except ValueError:
                relative = file
            
            if len(relative.parts) == 1:
                # Файл в корневой папке
                folder_structure[""].append(relative)
            else:
                # Файл в подпапке
                folder_path = str(relative.parent)
                folder_structure[folder_path].append(relative)
        
        tree = []
        root_name = base_folder.name
        
        tree.append("PROJECT STRUCTURE\n")
        tree.append(f"{root_name}/")
        
        # Сортируем папки и файлы
        sorted_folders = sorted(folder_structure.keys())
        
        for folder in sorted_folders:
            if folder == "":
                # Файлы в корневой папке
                for file in sorted(folder_structure[folder], key=lambda x: x.name):
                    tree.append(f" └ {file.name}")
            else:
                # Показываем структуру папок
                parts = folder.split('/')
                depth = 0
                current_path = ""
                
                for part in parts:
                    if depth == 0:
                        tree.append(f" ├─ {part}/")
                    else:
                        indent = " │   " * depth
                        tree.append(f"{indent} ├─ {part}/")
                    depth += 1
                
                # Файлы в этой папке
                for file in sorted(folder_structure[folder], key=lambda x: x.name):
                    indent = " │   " * depth
                    tree.append(f"{indent} └ {file.name}")
        
        tree.append("\n" + "=" * 40 + "\n")
        tree.append("SOURCE CODE\n")
        tree.append("=" * 40 + "\n")
        
        return "\n".join(tree)

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
