from pathlib import Path
from typing import List
from fnmatch import fnmatch
from config import PROJECT_MARKERS, JS_PROJECT_MARKERS, IGNORED_DIRS, IGNORE_PATTERNS


class FileCollector:
    """
    Отвечает за сбор файлов из разных источников.
    """

    def _is_in_ignored_dir(self, path: Path) -> bool:
        return any(part in IGNORED_DIRS for part in path.parts)

    def _has_allowed_extension(self, path: Path, extensions: List[str]) -> bool:
        return path.is_file() and path.suffix in extensions

    def _should_include_file(self, path: Path, extensions: List[str]) -> bool:
        if not path.exists():
            return False
        if self._is_in_ignored_dir(path):
            return False
        if not self._has_allowed_extension(path, extensions):
            return False
        if self.match_ignore_patterns(path):
            return False
        return True

    def _iter_folder(self, folder: Path, recursive: bool):
        if recursive:
            yield from folder.rglob("*")
        else:
            yield from folder.iterdir()

    def collect_from_file(self, path: Path) -> List[Path]:
        return [path]

    def collect_from_files(self, paths: List[Path]) -> List[Path]:
        return paths

    def collect_from_folder(self, folder: Path, extensions: List[str]) -> List[Path]:
        return [
            p for p in self._iter_folder(folder, recursive=False)
            if self._should_include_file(p, extensions)
        ]

    def collect_from_folder_recursive(self, folder: Path, extensions: List[str]) -> List[Path]:
        return [
            p for p in self._iter_folder(folder, recursive=True)
            if self._should_include_file(p, extensions)
        ]

    def detect_python_project(self, folder: Path) -> bool:
        """
        Проверяет является ли папка Python-проектом.
        """

        for marker in PROJECT_MARKERS:
            if (folder / marker).exists():
                return True

        return False

    def detect_js_project(self, folder: Path) -> bool:
        """
        Проверяет является ли папка JavaScript/TypeScript-проектом.
        """

        for marker in JS_PROJECT_MARKERS:
            if (folder / marker).exists():
                return True

        return False

    def collect_project_files(self, folder: Path, extensions: List[str]) -> List[Path]:
        """
        Собирает все файлы проекта с указанными расширениями,
        игнорируя служебные каталоги.
        """
        return [
            p for p in self._iter_folder(folder, recursive=True)
            if self._should_include_file(p, extensions)
        ]

    def collect_python_project(self, folder: Path, extensions: List[str]) -> List[Path]:
        """
        Устаревший метод. Используйте collect_project_files().
        """
        return self.collect_project_files(folder, extensions)

    def collect_js_project(self, folder: Path, extensions: List[str]) -> List[Path]:
        """
        Устаревший метод. Используйте collect_project_files().
        """
        return self.collect_project_files(folder, extensions)

    def match_ignore_patterns(self, path: Path) -> bool:
        """
        Проверяет соответствует ли файл игнорируемым маскам.
        """

        name = path.name

        for pattern in IGNORE_PATTERNS:
            if fnmatch(name, pattern):
                return True

        return False
