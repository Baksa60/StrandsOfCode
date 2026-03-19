"""
Сервис для конвертации между текстовыми форматами
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
from html.parser import HTMLParser
from html import unescape
from utils.file_utils import read_file_safe
from utils.cancellation import check_cancelled


class TextToTextConverter:
    """
    Конвертирует между текстовыми форматами (TXT, Markdown, HTML)
    """
    
    def __init__(self):
        self.supported_conversions = {
            'txt': ['markdown', 'html'],
            'markdown': ['txt', 'html'],
            'html': ['txt', 'markdown']
        }
    
    def convert_text(self, files: List[Path], output_folder: Path, 
                    source_format: str, target_format: str,
                    output_mode: str = "separate", filename: str = None) -> dict:
        """
        Конвертирует файлы между текстовыми форматами
        
        Args:
            files: Список файлов для конвертации
            output_folder: Папка для сохранения результатов
            source_format: Исходный формат
            target_format: Целевой формат
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
                files, output_folder, source_format, target_format, filename
            )
            results['combined_file'] = combined_result
        else:
            # Конвертируем каждый файл отдельно
            for file_path in files:
                check_cancelled()
                try:
                    result = self._convert_single_file(
                        file_path, output_folder, source_format, target_format
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
                           source_format: str, target_format: str) -> dict:
        """
        Конвертирует один файл
        """
        
        # Читаем исходный файл
        source_content, _ = read_file_safe(file_path)
        
        # Конвертируем контент
        converted_content = self._convert_text_content(source_content, source_format, target_format)
        
        # Определяем имя выходного файла
        output_path = output_folder / f"{file_path.stem}.{self._get_extension(target_format)}"
        
        # Записываем конвертированный файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(converted_content)
        
        return {
            'output_path': output_path,
            'size': output_path.stat().st_size,
            'lines': len(converted_content.splitlines())
        }
    
    def _convert_text_content(self, content: str, source_format: str, target_format: str) -> str:
        """
        Конвертирует содержимое между форматами
        """
        
        if source_format == target_format:
            return content
        
        converters = {
            ('txt', 'markdown'): self._txt_to_markdown,
            ('txt', 'html'): self._txt_to_html,
            ('markdown', 'txt'): self._markdown_to_txt,
            ('markdown', 'html'): self._markdown_to_html,
            ('html', 'txt'): self._html_to_txt,
            ('html', 'markdown'): self._html_to_markdown
        }
        
        converter = converters.get((source_format, target_format))
        if converter:
            return converter(content)
        else:
            raise ValueError(f"Конвертация {source_format} → {target_format} не поддерживается")
    
    def _txt_to_markdown(self, content: str) -> str:
        """Конвертирует TXT в Markdown"""
        lines = content.split('\n')
        markdown_lines = []
        
        for line in lines:
            # Добавляем форматирование Markdown
            if line.strip():
                # Если строка выглядит как заголовок (короткая и не содержит обычных слов)
                if len(line.strip()) < 50 and line.strip().istitle():
                    markdown_lines.append(f"## {line.strip()}")
                else:
                    markdown_lines.append(line)
            else:
                markdown_lines.append("")  # Пустая строка
        
        return '\n'.join(markdown_lines)
    
    def _txt_to_html(self, content: str) -> str:
        """Конвертирует TXT в HTML"""
        lines = content.split('\n')
        html_lines = ['<!DOCTYPE html>', '<html lang="ru">', '<head>', 
                     '<meta charset="UTF-8">', '<title>Конвертированный текст</title>',
                     '<style>body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }</style>',
                     '</head>', '<body>']
        
        for line in lines:
            if line.strip():
                # Экранируем HTML сущности
                escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_lines.append(f'<p>{escaped_line}</p>')
            else:
                html_lines.append('<br>')
        
        html_lines.extend(['</body>', '</html>'])
        
        return '\n'.join(html_lines)
    
    def _markdown_to_txt(self, content: str) -> str:
        """Конвертирует Markdown в TXT"""
        lines = content.split('\n')
        txt_lines = []
        
        for line in lines:
            # Удаляем Markdown разметку
            clean_line = line
            
            # Удаляем заголовки
            clean_line = re.sub(r'^#+\s*', '', clean_line)
            
            # Удаляем жирный и курсив
            clean_line = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_line)  # **bold**
            clean_line = re.sub(r'\*(.*?)\*', r'\1', clean_line)        # *italic*
            clean_line = re.sub(r'__(.*?)__', r'\1', clean_line)        # __bold__
            clean_line = re.sub(r'_(.*?)_', r'\1', clean_line)          # _italic_
            
            # Удаляем код
            clean_line = re.sub(r'`(.*?)`', r'\1', clean_line)
            
            # Удаляем ссылки
            clean_line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_line)
            
            # Удаляем списки
            clean_line = re.sub(r'^\s*[-*+]\s*', '', clean_line)
            clean_line = re.sub(r'^\s*\d+\.\s*', '', clean_line)
            
            txt_lines.append(clean_line)
        
        return '\n'.join(txt_lines)
    
    def _markdown_to_html(self, content: str) -> str:
        """Конвертирует Markdown в HTML"""
        lines = content.split('\n')
        html_lines = ['<!DOCTYPE html>', '<html lang="ru">', '<head>', 
                     '<meta charset="UTF-8">', '<title>Конвертированный Markdown</title>',
                     '<style>body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; } h1, h2, h3 { color: #333; } code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }</style>',
                     '</head>', '<body>']
        
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    html_lines.append('</code></pre>')
                    in_code_block = False
                else:
                    html_lines.append('<pre><code>')
                    in_code_block = True
                continue
            
            if in_code_block:
                # Экранируем HTML и добавляем как есть
                escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_lines.append(escaped_line)
            else:
                # Обрабатываем Markdown разметку
                if line.strip().startswith('# '):
                    title = line.strip()[2:]
                    html_lines.append(f'<h1>{title}</h1>')
                elif line.strip().startswith('## '):
                    title = line.strip()[3:]
                    html_lines.append(f'<h2>{title}</h2>')
                elif line.strip().startswith('### '):
                    title = line.strip()[4:]
                    html_lines.append(f'<h3>{title}</h3>')
                elif line.strip():
                    # Обрабатываем обычный текст с базовой Markdown разметкой
                    processed_line = self._process_markdown_line(line)
                    html_lines.append(f'<p>{processed_line}</p>')
                else:
                    html_lines.append('<br>')
        
        html_lines.extend(['</body>', '</html>'])
        
        return '\n'.join(html_lines)
    
    def _process_markdown_line(self, line: str) -> str:
        """Обрабатывает Markdown разметку в строке"""
        processed = line
        
        # Экранируем HTML сущности
        processed = processed.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Жирный текст
        processed = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', processed)
        processed = re.sub(r'__(.*?)__', r'<strong>\1</strong>', processed)
        
        # Курсив
        processed = re.sub(r'\*(.*?)\*', r'<em>\1</em>', processed)
        processed = re.sub(r'_(.*?)_', r'<em>\1</em>', processed)
        
        # Код
        processed = re.sub(r'`(.*?)`', r'<code>\1</code>', processed)
        
        # Ссылки
        processed = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', processed)
        
        return processed
    
    def _html_to_txt(self, content: str) -> str:
        """Конвертирует HTML в TXT"""
        try:
            parser = HTMLToTextParser()
            parser.feed(content)
            return parser.get_text()
        except:
            # Если парсинг не удался, используем простую замену тегов
            cleaned = re.sub(r'<[^>]+>', '', content)
            cleaned = unescape(cleaned)
            return cleaned.strip()
    
    def _html_to_markdown(self, content: str) -> str:
        """Конвертирует HTML в Markdown"""
        try:
            parser = HTMLToMarkdownParser()
            parser.feed(content)
            return parser.get_markdown()
        except:
            # Если парсинг не удался, используем простую конвертацию
            txt = self._html_to_txt(content)
            return self._txt_to_markdown(txt)
    
    def _get_extension(self, format_name: str) -> str:
        """Возвращает расширение для формата"""
        extensions = {
            'txt': 'txt',
            'markdown': 'md',
            'html': 'html'
        }
        return extensions.get(format_name, 'txt')
    
    def _create_combined_file(self, files: List[Path], output_folder: Path,
                            source_format: str, target_format: str, filename: str = None) -> dict:
        """
        Создает объединенный файл с конвертированным текстом
        """
        # Используем указанное имя файла или имя по умолчанию
        if filename:
            output_path = output_folder / filename
        else:
            output_path = output_folder / f"combined_converted.{self._get_extension(target_format)}"
        
        if target_format == 'html':
            content_lines = ['<!DOCTYPE html>', '<html lang="ru">', '<head>', 
                           '<meta charset="UTF-8">', '<title>Конвертированные файлы</title>',
                           '<style>body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; } h1, h2, h3 { color: #333; } .file-section { margin: 40px 0; border-bottom: 1px solid #eee; padding-bottom: 20px; }</style>',
                           '</head>', '<body>',
                           f'<h1>🔄 Конвертированные файлы: {source_format} → {target_format}</h1>',
                           f'<p>Сгенерировано: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>',
                           f'<p>Всего файлов: {len(files)}</p>']
        else:
            content_lines = [
                f"# 🔄 Конвертированные файлы: {source_format} → {target_format}",
                f"Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Всего файлов: {len(files)}",
                "",
                "## 📁 Дерево проекта",
                ""
            ]
        
        # Добавляем конвертированные файлы
        for file_path in sorted(files):
            check_cancelled()
            source_content, _ = read_file_safe(file_path)
            
            converted_content = self._convert_text_content(source_content, source_format, target_format)
            
            if target_format == 'html':
                content_lines.extend([
                    '<div class="file-section">',
                    f'<h2>📄 {file_path.name}</h2>',
                    '<pre>',
                    converted_content,
                    '</pre>',
                    '</div>'
                ])
            else:
                content_lines.extend([
                    f"### 📄 {file_path.name}",
                    "",
                    "```",
                    converted_content,
                    "```",
                    ""
                ])
        
        if target_format == 'html':
            content_lines.extend(['</body>', '</html>'])
        
        # Записываем объединенный файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_lines))
        
        return {
            'output_path': output_path,
            'size': output_path.stat().st_size,
            'total_files': len(files)
        }


class HTMLToTextParser(HTMLParser):
    """HTML парсер для извлечения текста"""
    
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.current_tag = None
    
    def handle_data(self, data):
        if data.strip():
            self.text_parts.append(data)
    
    def handle_starttag(self, tag, attrs):
        if tag in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.text_parts.append('\n')
        elif tag in ['br', 'hr']:
            self.text_parts.append('\n')
        elif tag in ['ul', 'ol']:
            self.text_parts.append('\n')
        elif tag == 'li':
            self.text_parts.append('• ')
    
    def get_text(self) -> str:
        """Возвращает извлеченный текст"""
        text = ''.join(self.text_parts)
        # Очищаем лишние пробелы и пустые строки
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        return '\n'.join(cleaned_lines)


class HTMLToMarkdownParser(HTMLParser):
    """HTML парсер для конвертации в Markdown"""
    
    def __init__(self):
        super().__init__()
        self.markdown_parts = []
        self.in_list = False
        self.list_type = None
    
    def handle_data(self, data):
        if data.strip():
            self.markdown_parts.append(data)
    
    def handle_starttag(self, tag, attrs):
        if tag == 'h1':
            self.markdown_parts.append('\n# ')
        elif tag == 'h2':
            self.markdown_parts.append('\n## ')
        elif tag == 'h3':
            self.markdown_parts.append('\n### ')
        elif tag == 'h4':
            self.markdown_parts.append('\n#### ')
        elif tag == 'h5':
            self.markdown_parts.append('\n##### ')
        elif tag == 'h6':
            self.markdown_parts.append('\n###### ')
        elif tag == 'p':
            self.markdown_parts.append('\n')
        elif tag == 'br':
            self.markdown_parts.append('\n')
        elif tag == 'strong' or tag == 'b':
            self.markdown_parts.append('**')
        elif tag == 'em' or tag == 'i':
            self.markdown_parts.append('*')
        elif tag == 'code':
            self.markdown_parts.append('`')
        elif tag == 'pre':
            self.markdown_parts.append('\n```\n')
        elif tag == 'ul':
            self.in_list = True
            self.list_type = 'ul'
            self.markdown_parts.append('\n')
        elif tag == 'ol':
            self.in_list = True
            self.list_type = 'ol'
            self.markdown_parts.append('\n')
        elif tag == 'li' and self.in_list:
            if self.list_type == 'ul':
                self.markdown_parts.append('• ')
            else:
                self.markdown_parts.append('1. ')
    
    def handle_endtag(self, tag):
        if tag in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.markdown_parts.append('\n')
        elif tag == 'strong' or tag == 'b':
            self.markdown_parts.append('**')
        elif tag == 'em' or tag == 'i':
            self.markdown_parts.append('*')
        elif tag == 'code':
            self.markdown_parts.append('`')
        elif tag == 'pre':
            self.markdown_parts.append('\n```\n')
        elif tag in ['ul', 'ol']:
            self.in_list = False
            self.list_type = None
        elif tag == 'li':
            self.markdown_parts.append('\n')
    
    def get_markdown(self) -> str:
        """Возвращает Markdown"""
        markdown = ''.join(self.markdown_parts)
        # Очищаем лишние пустые строки
        lines = markdown.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            if line.strip():
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append('')
                prev_empty = True
        
        return '\n'.join(cleaned_lines)
