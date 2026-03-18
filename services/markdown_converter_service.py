"""
Сервис для конвертации кода в Markdown формат
"""

import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime


class MarkdownConverterService:
    """
    Отвечает за конвертацию файлов кода в Markdown формат
    с подсветкой синтаксиса и метаданными
    """
    
    def __init__(self):
        self.supported_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx']
        
    def convert_to_markdown(self, files: List[Path], output_folder: Path, 
                           add_headers: bool = True, add_line_numbers: bool = True,
                           create_tree: bool = True, base_folder: Optional[Path] = None) -> dict:
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
                files, output_folder, add_headers, add_line_numbers, base_folder
            )
            results['combined_file'] = combined_result
        
        # Конвертируем каждый файл отдельно
        for file_path in files:
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
            # Читаем файл с определением кодировки
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Пробуем другие кодировки
            for encoding in ['cp1251', 'latin-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
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
                                 base_folder: Path) -> dict:
        """
        Создает объединенный Markdown файл с деревом проекта
        """
        
        output_path = output_folder / "combined_code.md"
        
        # Создаем дерево проекта
        tree_content = self._create_project_tree(files, base_folder)
        
        # Собираем контент всех файлов
        files_content = []
        for file_path in sorted(files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                for encoding in ['cp1251', 'latin-1']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                else:
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
    
    def _create_project_tree(self, files: List[Path], base_folder: Path) -> str:
        """
        Создает текстовое представление дерева проекта
        """
        
        # Создаем структуру папок и файлов
        tree_structure = {}
        
        for file_path in files:
            try:
                relative_path = file_path.relative_to(base_folder)
            except ValueError:
                relative_path = file_path
            
            parts = relative_path.parts
            current_level = tree_structure
            
            for part in parts[:-1]:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
            
            current_level[parts[-1]] = None
        
        # Рекурсивно строим дерево
        def build_tree(structure, prefix="", is_last=True):
            tree_lines = []
            items = list(structure.items())
            
            for i, (name, substructure) in enumerate(items):
                is_last_item = i == len(items) - 1
                
                # Определяем символы
                connector = "└── " if is_last_item else "├── "
                extension = "    " if is_last_item else "│   "
                
                # Добавляем файл или папку
                if substructure is None:
                    # Это файл
                    tree_lines.append(f"{prefix}{connector}{name}")
                else:
                    # Это папка
                    tree_lines.append(f"{prefix}{connector}📁 {name}/")
                    tree_lines.extend(build_tree(
                        substructure, prefix + extension, is_last_item
                    ))
            
            return tree_lines
        
        tree_lines = build_tree(tree_structure)
        return "\n".join(tree_lines) if tree_lines else "Пустой проект"
