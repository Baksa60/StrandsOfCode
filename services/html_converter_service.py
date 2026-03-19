"""
Сервис для конвертации кода в HTML формат
"""

import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from utils.file_utils import read_file_safe
from utils.cancellation import check_cancelled


class HtmlConverterService:
    """
    Отвечает за конвертацию файлов кода в HTML формат
    с подсветкой синтаксиса и современным дизайном
    """
    
    def __init__(self):
        self.supported_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx']
        
    def convert_to_html(self, files: List[Path], output_folder: Path, 
                      add_headers: bool = True, add_line_numbers: bool = True,
                      create_tree: bool = True, base_folder: Optional[Path] = None,
                      filename: Optional[str] = None) -> dict:
        """
        Конвертирует файлы в HTML формат
        
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
            combined_result = self._create_combined_html(
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
        Конвертирует один файл в HTML
        """
        
        try:
            content, _ = read_file_safe(file_path)
        except UnicodeDecodeError:
            raise ValueError(f"Не удалось определить кодировку файла {file_path}")
        
        # Определяем язык для подсветки синтаксиса
        language = self._detect_language(file_path)
        
        # Создаем HTML контент
        html_content = self._create_html_content(
            file_path, content, language, add_headers, add_line_numbers
        )
        
        # Определяем имя выходного файла
        output_path = output_folder / f"{file_path.stem}.html"
        
        # Записываем HTML файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return {
            'output_path': output_path,
            'size': output_path.stat().st_size,
            'lines': len(content.splitlines())
        }
    
    def _create_combined_html(self, files: List[Path], output_folder: Path,
                              add_headers: bool, add_line_numbers: bool,
                              base_folder: Path, filename: Optional[str] = None) -> dict:
        """
        Создает объединенный HTML файл с деревом проекта
        """
        
        if filename:
            output_path = output_folder / filename
            if output_path.suffix.lower() != '.html':
                output_path = output_path.with_suffix('.html')
        else:
            output_path = output_folder / "combined_code.html"
        
        # Создаем дерево проекта
        tree_content = self._create_project_tree(files, base_folder)
        
        # Собираем контент всех файлов
        files_content = []
        for file_path in sorted(files):
            check_cancelled()
            try:
                content, _ = read_file_safe(file_path)
            except UnicodeDecodeError:
                content = f"[ОШИБКА: Не удалось прочитать файл {file_path}]"
            
            language = self._detect_language(file_path)
            
            file_content = self._create_html_content(
                file_path, content, language, add_headers, add_line_numbers,
                relative_to=base_folder
            )
            
            files_content.append(file_content)
        
        # Создаем объединенный контент
        combined_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧬 StrandsOfCode - Объединенный код проекта</title>
    <style>
{self._get_combined_css()}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🧬 StrandsOfCode</h1>
            <p class="subtitle">Объединенный код проекта</p>
            <div class="meta">
                <span>Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                <span>Всего файлов: {len(files)}</span>
            </div>
        </header>
        
        <section class="tree-section">
            <h2>📁 Дерево проекта</h2>
            <pre class="tree">{tree_content}</pre>
        </section>
        
        <section class="files-section">
            <h2>📄 Файлы проекта</h2>
            {chr(10).join(files_content)}
        </section>
        
        <footer class="footer">
            <p>Сгенерировано с помощью 🧬 StrandsOfCode</p>
        </footer>
    </div>
</body>
</html>"""
        
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
    
    def _create_html_content(self, file_path: Path, content: str, 
                            language: str, add_headers: bool, 
                            add_line_numbers: bool, relative_to: Optional[Path] = None) -> str:
        """
        Создает HTML контент для файла
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
        header_html = f'<h3 class="file-header">📄 {relative_path}</h3>'
        
        if add_headers:
            file_info_html = f"""
<div class="file-info">
    <span class="info-item"><strong>Язык:</strong> {language}</span>
    <span class="info-item"><strong>Размер:</strong> {len(content)} символов</span>
    <span class="info-item"><strong>Строк:</strong> {len(content.splitlines())}</span>
    <span class="info-item"><strong>Путь:</strong> <code>{relative_path}</code></span>
</div>"""
        else:
            file_info_html = ""
        
        # Обрабатываем контент с нумерацией строк
        if add_line_numbers:
            lines = content.splitlines()
            numbered_lines = []
            for i, line in enumerate(lines, 1):
                escaped_line = self._escape_html(line)
                numbered_lines.append(f'<span class="line-number">{i:3d}</span><span class="line-content">{escaped_line}</span>')
            processed_content = "\n".join(numbered_lines)
        else:
            processed_content = self._escape_html(content)
        
        # Создаем блок кода с подсветкой синтаксиса
        code_html = f'<div class="code-block"><pre class="code language-{language}">{processed_content}</pre></div>'
        
        # Собираем полный контент
        html_content = f"""{header_html}

{file_info_html}

{code_html}

"""
        
        return html_content
    
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
    
    def _escape_html(self, text: str) -> str:
        """
        Экранирует HTML символы
        """
        return (text.replace('&', '&amp;')
                     .replace('<', '&lt;')
                     .replace('>', '&gt;')
                     .replace('"', '&quot;')
                     .replace("'", '&#39;'))
    
    def _get_combined_css(self) -> str:
        """
        Возвращает CSS стили для объединенного HTML файла
        """
        return """
/* Общие стили */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', 'Arial', sans-serif;
    line-height: 1.6;
    color: #2c3e50;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

/* Хедер */
.header {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    padding: 30px;
    margin-bottom: 30px;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.header h1 {
    font-size: 2.5em;
    color: #2c3e50;
    margin-bottom: 10px;
}

.subtitle {
    font-size: 1.2em;
    color: #7f8c8d;
    margin-bottom: 20px;
}

.meta {
    display: flex;
    justify-content: center;
    gap: 30px;
    flex-wrap: wrap;
}

.meta span {
    background: #3498db;
    color: white;
    padding: 5px 15px;
    border-radius: 20px;
    font-size: 0.9em;
}

/* Секции */
.tree-section, .files-section {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    padding: 30px;
    margin-bottom: 30px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.tree-section h2, .files-section h2 {
    color: #2c3e50;
    margin-bottom: 20px;
    font-size: 1.5em;
}

.tree {
    background: #f8f9fa;
    border: 2px solid #e9ecef;
    border-radius: 10px;
    padding: 20px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9em;
    color: #495057;
    overflow-x: auto;
}

/* Файлы */
.file-header {
    color: #2c3e50;
    margin-bottom: 15px;
    font-size: 1.3em;
    border-bottom: 2px solid #3498db;
    padding-bottom: 10px;
}

.file-info {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
}

.info-item {
    background: #e3f2fd;
    color: #1565c0;
    padding: 5px 10px;
    border-radius: 5px;
    font-size: 0.9em;
}

.code-block {
    background: #2d3748;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 30px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

.code {
    margin: 0;
    padding: 20px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9em;
    line-height: 1.4;
    overflow-x: auto;
    white-space: pre;
}

.line-number {
    color: #718096;
    margin-right: 15px;
    user-select: none;
    display: inline-block;
    width: 3em;
    text-align: right;
}

.line-content {
    color: #e2e8f0;
}

/* Подсветка синтаксиса */
.language-python .line-content {
    color: #e2e8f0;
}

.language-javascript .line-content {
    color: #e2e8f0;
}

.language-typescript .line-content {
    color: #e2e8f0;
}

/* Футер */
.footer {
    text-align: center;
    padding: 20px;
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.9em;
}

/* Адаптивность */
@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    
    .header, .tree-section, .files-section {
        padding: 20px;
    }
    
    .meta {
        flex-direction: column;
        gap: 10px;
    }
    
    .file-info {
        flex-direction: column;
        gap: 10px;
    }
}
"""
