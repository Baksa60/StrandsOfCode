"""
Конвертер из HTML формата обратно в код
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from services.base_reverse_converter import BaseReverseConverter
import re
from html.parser import HTMLParser


class HtmlToCodeConverter(BaseReverseConverter):
    """
    Конвертирует HTML файлы обратно в исходные файлы кода
    """
    
    def convert_to_code(self, text_content: str, output_folder: Path, 
                          language: Optional[str] = None, 
                          file_structure: Optional[Dict[str, Any]] = None) -> dict:
        """
        Конвертирует HTML обратно в код
        """
        from datetime import datetime
        
        start_time = datetime.now()
        output_files = []
        
        # Создаем выходную папку
        output_folder.mkdir(parents=True, exist_ok=True)
        
        if file_structure:
            # Режим восстановления структуры
            output_files = self._restore_html_structure(
                file_structure, output_folder, language
            )
        else:
            # Режим одного файла
            language = language or self.detect_language(text_content)
            clean_content = self.clean_code_content(text_content)
            
            # Определяем расширение файла
            extension = self._get_extension_for_language(language)
            output_path = output_folder / f"restored_code{extension}"
            
            # Записываем файл
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(clean_content)
            
            output_files.append(output_path)
        
        return self.create_result(output_files, start_time)
    
    def _restore_html_structure(self, file_structure: Dict[str, str], 
                              output_folder: Path, default_language: str) -> List[Path]:
        """
        Восстанавливает структуру файлов из HTML
        """
        output_files = []
        
        for file_name, content in file_structure.items():
            # Очищаем контент
            clean_content = self.clean_code_content(content)
            
            # Определяем язык и расширение
            language = self.detect_language(clean_content) or default_language
            extension = self._get_extension_for_language(language)
            
            # Восстанавливаем путь файла
            if '/' in file_name:
                # Создаем подпапки если нужно
                file_path = output_folder / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                file_path = output_folder / file_name
            
            # Убеждаем что расширение правильное
            if not file_path.suffix:
                file_path = file_path.with_suffix(extension)
            
            # Записываем файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(clean_content)
            
            output_files.append(file_path)
        
        return output_files
    
    def _get_extension_for_language(self, language: str) -> str:
        """
        Возвращает расширение файла для языка программирования
        """
        extension_map = {
            'python': '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'jsx': '.jsx',
            'tsx': '.tsx',
            'text': '.txt'
        }
        
        return extension_map.get(language.lower(), '.txt')
    
    def parse_html_structure(self, content: str) -> Dict[str, str]:
        """
        Парсит HTML файл для извлечения структуры
        """
        parser = CodeHTMLParser()
        parser.feed(content)
        return parser.get_file_structure()
    
    def clean_code_content(self, content: str) -> str:
        """
        Очищает HTML контент от тегов и артефактов
        """
        # Удаляем HTML теги кода
        content = re.sub(r'<div[^>]*class="code-block"[^>]*>', '', content)
        content = re.sub(r'<pre[^>]*class="code[^>]*>', '', content)
        content = re.sub(r'</pre>', '', content)
        content = re.sub(r'</div>', '', content)
        
        # Очищаем от span тегов
        content = re.sub(r'<span[^>]*class="line-number"[^>]*>[^<]*</span>', '', content)
        content = re.sub(r'<span[^>]*class="line-content"[^>]*>', '', content)
        content = re.sub(r'</span>', '', content)
        
        # Декодируем HTML сущности
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'"
        }
        
        for entity, char in html_entities.items():
            content = content.replace(entity, char)
        
        return content.strip()


class CodeHTMLParser(HTMLParser):
    """
    HTML парсер для извлечения структуры файлов
    """
    
    def __init__(self):
        super().__init__()
        self.in_file_header = False
        self.current_file = None
        self.current_content = []
        self.file_structure = {}
        self.in_code_block = False
    
    def handle_starttag(self, tag, attrs):
        if tag == 'h3' and any('file-header' in attr.get('class', '') for attr in attrs if isinstance(attr, dict)):
            self.in_file_header = True
        elif tag == 'pre' and any('code' in attr.get('class', '') for attr in attrs if isinstance(attr, dict)):
            self.in_code_block = True
    
    def handle_endtag(self, tag):
        if tag == 'h3':
            self.in_file_header = False
        elif tag == 'pre':
            self.in_code_block = False
    
    def handle_data(self, data):
        if self.in_file_header:
            # Извлекаем имя файла
            clean_name = data.strip()
            if '📄' in clean_name:
                self.current_file = clean_name.split('📄')[1].strip()
        
        elif self.current_file and (self.in_code_block or data.strip()):
            # Собираем контент файла
            self.current_content.append(data)
    
    def get_file_structure(self) -> Dict[str, str]:
        """
        Возвращает извлеченную структуру файлов
        """
        if self.current_file and self.current_content:
            self.file_structure[self.current_file] = '\n'.join(self.current_content)
        
        return self.file_structure
