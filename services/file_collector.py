from pathlib import Path
from typing import List
from fnmatch import fnmatch
from config import PROJECT_MARKERS, JS_PROJECT_MARKERS, IGNORED_DIRS, IGNORE_PATTERNS


class FileCollector:
    """
    Отвечает за сбор файлов из разных источников.
    """

    def collect_from_file(self, path: Path) -> List[Path]:
        return [path]

    def collect_from_files(self, paths: List[Path]) -> List[Path]:
        return paths

    def collect_from_folder(self, folder: Path, extensions: List[str]) -> List[Path]:
        return [
            f for f in folder.iterdir()
            if f.is_file() and f.suffix in extensions
        ]

    def collect_from_folder_recursive(self, folder: Path, extensions: List[str]) -> List[Path]:
        return [
            f for f in folder.rglob("*")
            if f.is_file() and f.suffix in extensions
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

    def collect_python_project(self, folder: Path, extensions: List[str]) -> List[Path]:
        """
        Собирает все Python файлы проекта,
        игнорируя служебные каталоги.
        """

        files = []

        for path in folder.rglob("*"):
            if not path.exists():
                continue

            # проверяем что путь не находится внутри игнорируемых папок
            if any(part in IGNORED_DIRS for part in path.parts):
                continue

            if path.is_file() and path.suffix in extensions:

                if self.match_ignore_patterns(path):
                    continue

                files.append(path)

        return files

    def collect_js_project(self, folder: Path, extensions: List[str]) -> List[Path]:
        """
        Собирает все JavaScript/TypeScript файлы проекта,
        игнорируя служебные каталоги.
        """

        files = []

        for path in folder.rglob("*"):
            if not path.exists():
                continue

            # проверяем что путь не находится внутри игнорируемых папок
            if any(part in IGNORED_DIRS for part in path.parts):
                continue

            if path.is_file() and path.suffix in extensions:

                if self.match_ignore_patterns(path):
                    continue

                files.append(path)

        return files

    def match_ignore_patterns(self, path: Path) -> bool:
        """
        Проверяет соответствует ли файл игнорируемым маскам.
        """

        name = path.name

        for pattern in IGNORE_PATTERNS:
            if fnmatch(name, pattern):
                return True

        return False
