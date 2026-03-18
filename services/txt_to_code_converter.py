"""
Конвертер из TXT формата обратно в код
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from services.base_reverse_converter import BaseReverseConverter
import re


class TxtToCodeConverter(BaseReverseConverter):
    """
    Конвертирует TXT файлы обратно в исходные файлы кода
    """
    
    def convert_to_code(self, text_content: str, output_folder: Path, 
                          language: Optional[str] = None, 
                          file_structure: Optional[Dict[str, Any]] = None) -> dict:
        """
        Конвертирует текст обратно в код
        """
        from datetime import datetime
        
        start_time = datetime.now()
        output_files = []
        
        # Создаем выходную папку
        output_folder.mkdir(parents=True, exist_ok=True)
        
        if file_structure:
            # Режим восстановления структуры
            output_files = self._restore_file_structure(
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
    
    def _restore_file_structure(self, file_structure: Dict[str, str], 
                              output_folder: Path, default_language: str) -> List[Path]:
        """
        Восстанавливает структуру файлов и папок
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
    
    def parse_txt_structure(self, content: str) -> Dict[str, str]:
        """
        Парсит TXT файл для извлечения структуры
        """
        structure = {}
        
        lines = content.split('\n')
        current_file = None
        current_content = []
        
        for line in lines:
            # Ищем заголовки файлов
            if line.startswith('## 📄 ') or line.startswith('### 📄 '):
                # Сохраняем предыдущий файл
                if current_file and current_content:
                    structure[current_file] = '\n'.join(current_content)
                
                # Начинаем новый файл
                try:
                    current_file = line.split('📄 ')[1].strip()
                except IndexError:
                    continue
                current_content = []
            
            # Собираем контент файла
            elif current_file and (line.strip() or line.startswith('│') or '```' in line):
                current_content.append(line)
        
        # Сохраняем последний файл
        if current_file and current_content:
            structure[current_file] = '\n'.join(current_content)
        
        return structure
