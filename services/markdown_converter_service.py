"""
Сервис для конвертации кода в Markdown формат
"""

import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from utils.file_utils import read_file_safe
from utils.cancellation import check_cancelled


class MarkdownConverterService:
    """
    Отвечает за конвертацию файлов кода в Markdown формат
    с подсветкой синтаксиса и метаданными
    """
    
    def __init__(self):
        self.supported_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx']
        
    def convert_to_markdown(self, files: List[Path], output_folder: Path, 
                           add_headers: bool = True, add_line_numbers: bool = True,
                           create_tree: bool = True, base_folder: Optional[Path] = None,
                           filename: Optional[str] = None) -> dict:
        """
        Конвертирует файлы в Markdown формат
        
        Args:
            files: Список файлов для конвертации
            output_folder: Папка для сохранения результатов
            add_headers: Добавлять ли заголовки файлов
            add_line_numbers: Добавлять ли нумерацию строк
            create_tree: Создавать ли дерево проекта
            base_folder: Базовая папка для дерева проекта
            
        Returns:
            dict: Результат конвертации со статистикой
        """
        
        results = {
            'total_files': len(files),
            'converted_files': 0,
            'failed_files': [],
            'output_files': [],
            'total_size': 0,
            'start_time': datetime.now(),
            'errors': []
        }
        
        # Создаем выходную папку
        output_folder.mkdir(parents=True, exist_ok=True)
        
        if create_tree and base_folder:
            # Создаем объединенный файл с деревом проекта
            combined_result = self._create_combined_markdown(
                files, output_folder, add_headers, add_line_numbers, base_folder, filename
            )
            results['combined_file'] = combined_result
            results['converted_files'] = 1
            results['output_files'].append(combined_result['output_path'])
            results['total_size'] += combined_result['size']
            results['end_time'] = datetime.now()
            results['duration'] = results['end_time'] - results['start_time']
            return results
        
        # Конвертируем каждый файл отдельно
        for file_path in files:
            check_cancelled()
            try:
                result = self._convert_single_file(
                    file_path, output_folder, add_headers, add_line_numbers
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
                           add_headers: bool, add_line_numbers: bool) -> dict:
        """
        Конвертирует один файл в Markdown
        """
        
        try:
            content, _ = read_file_safe(file_path)
        except UnicodeDecodeError:
            raise ValueError(f"Не удалось определить кодировку файла {file_path}")
        
        # Определяем язык для подсветки синтаксиса
        language = self._detect_language(file_path)
        
        # Создаем Markdown контент
        markdown_content = self._create_markdown_content(
            file_path, content, language, add_headers, add_line_numbers
        )
        
        # Определяем имя выходного файла
        output_path = output_folder / f"{file_path.stem}.md"
        
        # Записываем Markdown файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return {
            'output_path': output_path,
            'size': output_path.stat().st_size,
            'lines': len(content.splitlines())
        }
    
    def _create_combined_markdown(self, files: List[Path], output_folder: Path,
                                 add_headers: bool, add_line_numbers: bool,
                                 base_folder: Path, filename: Optional[str] = None) -> dict:
        """
        Создает объединенный Markdown файл с деревом проекта
        """
        
        if filename:
            output_path = output_folder / filename
            if output_path.suffix.lower() != '.md':
                output_path = output_path.with_suffix('.md')
        else:
            output_path = output_folder / "combined_code.md"
        
        # Создаем дерево проекта
        from utils.tree_utils import build_project_tree
        tree_content = build_project_tree(files, base_folder)
        
        # Собираем контент всех файлов
        files_content = []
        for file_path in sorted(files):
            check_cancelled()
            try:
                content, _ = read_file_safe(file_path)
            except UnicodeDecodeError:
                content = f"[ОШИБКА: Не удалось прочитать файл {file_path}]"
            
            language = self._detect_language(file_path)
            
            file_content = self._create_markdown_content(
                file_path, content, language, add_headers, add_line_numbers,
                relative_to=base_folder
            )
            
            files_content.append(file_content)
        
        # Создаем объединенный контент
        combined_content = f"""# 🧬 StrandsOfCode - Объединенный код проекта

**Сгенерировано:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Всего файлов:** {len(files)}

## 📁 Дерево проекта

```
{tree_content}
```

---

## 📄 Файлы проекта

{chr(10).join(files_content)}

---

*Сгенерировано с помощью 🧬 StrandsOfCode*
"""
        
        # Записываем объединенный файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(combined_content)
        
        return {
            'output_path': output_path,
            'size': output_path.stat().st_size,
            'total_files': len(files)
        }
    
    def _detect_language(self, file_path: Path) -> str:
        """
        Определяет язык программирования по расширению файла
        """
        extension = file_path.suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'jsx',
            '.ts': 'typescript',
            '.tsx': 'tsx'
        }
        
        return language_map.get(extension, 'text')
    
    def _create_markdown_content(self, file_path: Path, content: str, 
                               language: str, add_headers: bool, 
                               add_line_numbers: bool, relative_to: Optional[Path] = None) -> str:
        """
        Создает Markdown контент для файла
        """
        
        # Определяем относительный путь
        if relative_to:
            try:
                relative_path = file_path.relative_to(relative_to)
            except ValueError:
                relative_path = file_path
        else:
            relative_path = file_path
        
        # Заголовок файла
        header = f"## 📄 {relative_path}"
        
        if add_headers:
            file_info = f"""
**Язык:** {language}  
**Размер:** {len(content)} символов  
**Строк:** {len(content.splitlines())}  
**Путь:** `{relative_path}`
"""
        else:
            file_info = ""
        
        # Обрабатываем контент с нумерацией строк
        if add_line_numbers:
            lines = content.splitlines()
            numbered_lines = []
            for i, line in enumerate(lines, 1):
                numbered_lines.append(f"{i:3d}│{line}")
            processed_content = "\n".join(numbered_lines)
        else:
            processed_content = content
        
        # Создаем блок кода с подсветкой синтаксиса
        code_block = f"```{language}\n{processed_content}\n```"
        
        # Собираем полный контент
        markdown_content = f"""{header}

{file_info}

{code_block}

"""
        
        return markdown_content
    
    
