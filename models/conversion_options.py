from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ConversionOptions:
    """
    Параметры конвертации.
    Эта структура передаётся из UI в контроллер и сервисы.
    """

    # тип источника: file | files | folder | folder_recursive | python_project
    source_type: str

    # выбранные пути
    paths: List[Path]

    # папка сохранения
    output_folder: Path

    # расширения файлов для обработки
    extensions: List[str]

    # режим вывода
    output_mode: str
    # separate | combined

    # формат вывода
    output_format: str = "txt"
    # txt | markdown | html

    # добавлять заголовки файлов при объединении
    add_headers: bool = True
