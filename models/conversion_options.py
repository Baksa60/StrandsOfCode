from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


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

    # режим вывода: combined | separate
    output_mode: str

    # формат вывода: txt | markdown | html | python | javascript | typescript
    output_format: str

    # добавлять заголовки и метаданные
    add_headers: bool = True

    add_line_numbers: bool = True

    # имя файла для сохранения
    filename: Optional[str] = None
