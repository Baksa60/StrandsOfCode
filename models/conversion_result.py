from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class ConversionResult:
    """
    Результат операции конвертации.
    Возвращается контроллером в UI.
    """

    files_found: int = 0
    files_converted: int = 0

    created_files: List[Path] = field(default_factory=list)
    skipped_files: List[Path] = field(default_factory=list)

    errors: List[str] = field(default_factory=list)

    def success(self) -> bool:
        return len(self.errors) == 0
