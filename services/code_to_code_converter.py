"""
Сервис для конвертации кода между языками программирования
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
from utils.file_utils import read_file_safe
from utils.cancellation import check_cancelled


class CodeToCodeConverter:
    """
    Конвертирует код между языками программирования
    """
    
    def __init__(self):
        self.supported_conversions = {
            'python': ['javascript', 'typescript'],
            'javascript': ['python', 'typescript'],
            'typescript': ['python', 'javascript']
        }
    
    def convert_code(self, files: List[Path], output_folder: Path, 
                     source_language: str, target_language: str,
                     output_mode: str = "separate", filename: str = None) -> dict:
        """
        Конвертирует файлы кода между языками
        
        Args:
            files: Список файлов для конвертации
            output_folder: Папка для сохранения результатов
            source_language: Исходный язык
            target_language: Целевой язык
            output_mode: Режим вывода (separate/combined)
            filename: Имя файла для объединенного вывода
            
        Returns:
            dict: Результат конвертации со статистикой
        """
        
        start_time = datetime.now()
        results = {
            'total_files': len(files),
            'converted_files': 0,
            'failed_files': [],
            'output_files': [],
            'total_size': 0,
            'start_time': start_time,
            'errors': []
        }
        
        # Создаем выходную папку
        output_folder.mkdir(parents=True, exist_ok=True)
        
        if output_mode == "combined":
            # Создаем объединенный файл с указанным именем
            combined_result = self._create_combined_file(
                files, output_folder, source_language, target_language, filename
            )
            results['combined_file'] = combined_result
        else:
            # Конвертируем каждый файл отдельно
            for file_path in files:
                check_cancelled()
                try:
                    result = self._convert_single_file(
                        file_path, output_folder, source_language, target_language
                    )
                    results['converted_files'] += 1
                    results['output_files'].append(result['output_path'])
                    results['total_size'] += result['size']
                    
                except Exception as e:
                    results['failed_files'].append(str(file_path))
                    results['errors'].append(f"Ошибка конвертации {file_path}: {str(e)}")
        
        results['end_time'] = datetime.now()
        results['duration'] = results['end_time'] - results['start_time']
        
        return results
    
    def _convert_single_file(self, file_path: Path, output_folder: Path,
                           source_language: str, target_language: str) -> dict:
        """
        Конвертирует один файл
        """
        
        # Читаем исходный файл
        source_code, _ = read_file_safe(file_path)
        
        # Конвертируем код
        converted_code = self._convert_code_content(source_code, source_language, target_language)
        
        # Определяем имя выходного файла
        output_path = output_folder / f"{file_path.stem}.{self._get_extension(target_language)}"
        
        # Записываем конвертированный файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(converted_code)
        
        return {
            'output_path': output_path,
            'size': output_path.stat().st_size,
            'lines': len(converted_code.splitlines())
        }
    
    def _convert_code_content(self, code: str, source_lang: str, target_lang: str) -> str:
        """
        Конвертирует содержимое кода между языками
        """
        
        if source_lang == target_lang:
            return code
        
        # Простые правила конвертации
        converters = {
            ('python', 'javascript'): self._python_to_js,
            ('python', 'typescript'): self._python_to_ts,
            ('javascript', 'python'): self._js_to_python,
            ('javascript', 'typescript'): self._js_to_ts,
            ('typescript', 'python'): self._ts_to_python,
            ('typescript', 'javascript'): self._ts_to_js
        }
        
        converter = converters.get((source_lang, target_lang))
        if converter:
            return converter(code)
        else:
            raise ValueError(f"Конвертация {source_lang} → {target_lang} не поддерживается")
    
    def _python_to_js(self, code: str) -> str:
        """Конвертирует Python в JavaScript"""
        converted = code
        
        # Замена print на console.log
        converted = re.sub(r'print\((.*?)\)', r'console.log(\1)', converted)
        
        # Замена def на function
        converted = re.sub(r'def (\w+)\(', r'function \1(', converted)
        
        # Замена # на //
        converted = re.sub(r'^\s*#(.*)$', r'//\1', converted, flags=re.MULTILINE)
        
        # Замена True/False на true/false
        converted = converted.replace('True', 'true').replace('False', 'false')
        
        # Замена None на null
        converted = converted.replace('None', 'null')
        
        # Замена self на this (для методов классов)
        converted = re.sub(r'\bself\.', r'this.', converted)
        
        # Замена итераций
        converted = re.sub(r'for (\w+) in (\w+):', r'for (let \1 of \2) {', converted)
        
        # Добавляем точки с запятой в конце строк
        lines = converted.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('//') and not stripped.startswith('/*') and not stripped.startswith('*') and not stripped.startswith('function') and not stripped.startswith('if') and not stripped.startswith('for') and not stripped.startswith('while') and not stripped.startswith('{') and not stripped.startswith('}') and not stripped.endswith('{') and not stripped.endswith('}') and not stripped.endswith(':'):
                lines[i] = line.rstrip() + ';'
        
        return '\n'.join(lines)
    
    def _python_to_ts(self, code: str) -> str:
        """Конвертирует Python в TypeScript"""
        # Сначала конвертируем в JS
        js_code = self._python_to_js(code)
        
        # Добавляем типы TypeScript
        lines = js_code.split('\n')
        for i, line in enumerate(lines):
            # Добавляем типы к параметрам функций
            if 'function' in line and '(' in line and ')' in line:
                line = re.sub(r'(\w+)', r'\1: any', line)
                lines[i] = line
        
        return '\n'.join(lines)
    
    def _js_to_python(self, code: str) -> str:
        """Конвертирует JavaScript в Python"""
        converted = code
        
        # Замена console.log на print
        converted = re.sub(r'console\.log\((.*?)\)', r'print(\1)', converted)
        
        # Замена function на def
        converted = re.sub(r'function (\w+)\(', r'def \1(', converted)
        
        # Замена // на #
        converted = re.sub(r'^\s*\/\/(.*)$', r'#\1', converted, flags=re.MULTILINE)
        
        # Замена true/false на True/False
        converted = converted.replace('true', 'True').replace('false', 'False')
        
        # Замена null на None
        converted = converted.replace('null', 'None')
        
        # Замена this на self
        converted = re.sub(r'\bthis\.', r'self.', converted)
        
        # Удаляем точки с запятой
        converted = re.sub(r';\s*$', '', converted, flags=re.MULTILINE)
        
        # Замена фигурных скобок на отступы
        lines = converted.split('\n')
        result_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped == '}':
                indent_level -= 1
                line = '  ' * indent_level + stripped
            elif stripped.endswith('{'):
                line = '  ' * indent_level + stripped.rstrip('{')
                result_lines.append(line.rstrip(':') + ':')
                indent_level += 1
                continue
            else:
                line = '  ' * indent_level + stripped
            
            if line.strip():
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _js_to_ts(self, code: str) -> str:
        """Конвертирует JavaScript в TypeScript"""
        # Добавляем типы к JavaScript
        lines = code.split('\n')
        for i, line in enumerate(lines):
            # Добавляем типы к параметрам функций
            if 'function' in line and '(' in line and ')' in line:
                # Простая эвристика для добавления типов
                line = re.sub(r'(\w+)', r'\1: any', line)
                lines[i] = line
        
        return '\n'.join(lines)
    
    def _ts_to_python(self, code: str) -> str:
        """Конвертирует TypeScript в Python"""
        # Сначала конвертируем в JS, затем в Python
        js_code = self._ts_to_js(code)
        return self._js_to_python(js_code)
    
    def _ts_to_js(self, code: str) -> str:
        """Конвертирует TypeScript в JavaScript"""
        # Удаляем аннотации типов
        lines = code.split('\n')
        for i, line in enumerate(lines):
            # Удаляем типы параметров
            line = re.sub(r':\s*\w+', '', line)
            line = re.sub(r':\s*any', '', line)
            lines[i] = line
        
        return '\n'.join(lines)
    
    def _get_extension(self, language: str) -> str:
        """Возвращает расширение для языка"""
        extensions = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts'
        }
        return extensions.get(language, 'txt')
    
    def _create_combined_file(self, files: List[Path], output_folder: Path,
                            source_language: str, target_language: str, filename: str = None) -> dict:
        """
        Создает объединенный файл с конвертированным кодом
        """
        # Используем указанное имя файла или имя по умолчанию
        if filename:
            output_path = output_folder / filename
        else:
            output_path = output_folder / "combined_converted_code.txt"
        
        content_lines = [
            f"# 🔄 Конвертированный код: {source_language} → {target_language}",
            f"# Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Всего файлов: {len(files)}",
            "",
            "## 📁 Дерево проекта",
            ""
        ]
        
        # Добавляем дерево проекта
        tree_lines = self._create_project_tree(files)
        content_lines.extend(tree_lines)
        content_lines.extend(["", "## 📄 Конвертированные файлы", ""])
        
        # Добавляем конвертированные файлы
        for file_path in sorted(files):
            check_cancelled()
            content_lines.append(f"### 📄 {file_path.name}")
            content_lines.append("")

            source_code, _ = read_file_safe(file_path)
            
            converted_code = self._convert_code_content(source_code, source_language, target_language)
            
            content_lines.append("```" + target_language)
            content_lines.append(converted_code)
            content_lines.append("```")
            content_lines.append("")
        
        # Записываем объединенный файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_lines))
        
        return {
            'output_path': output_path,
            'size': output_path.stat().st_size,
            'total_files': len(files)
        }
    
    def _create_project_tree(self, files: List[Path]) -> List[str]:
        """Создает текстовое представление дерева проекта"""
        tree_structure = {}
        
        for file_path in files:
            # Используем только относительные пути, исключая корневую папку
            if len(file_path.parts) > 1:
                # Пропускаем первую часть (корневую папку)
                relative_parts = file_path.parts[1:]  # Пропускаем C:\Projects\py2txt_tool
            else:
                relative_parts = file_path.parts
            
            current_level = tree_structure
            
            for part in relative_parts[:-1]:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
            
            current_level[relative_parts[-1]] = None
        
        def build_tree(structure, prefix="", is_last=True):
            tree_lines = []
            items = list(structure.items())
            
            for i, (name, substructure) in enumerate(items):
                is_last_item = i == len(items) - 1
                
                connector = "└── " if is_last_item else "├── "
                extension = "    " if is_last_item else "│   "
                
                if substructure is None:
                    tree_lines.append(f"{prefix}{connector}{name}")
                else:
                    tree_lines.append(f"{prefix}{connector}📁 {name}/")
                    tree_lines.extend(build_tree(
                        substructure, prefix + extension, is_last_item
                    ))
            
            return tree_lines
        
        return build_tree(tree_structure) or ["Пустой проект"]
