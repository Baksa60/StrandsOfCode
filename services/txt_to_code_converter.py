"""
Конвертер из TXT формата обратно в код
"""

import os
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
            # Нормализуем разделители путей для текущей ОС
            normalized_name = file_name.replace('/', os.sep)
            
            if os.sep in normalized_name:
                # Создаем подпапки если нужно
                file_path = output_folder / normalized_name
                file_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                file_path = output_folder / normalized_name
            
            # Убеждаем что расширение правильное
            if not file_path.suffix:
                file_path = file_path.with_suffix(extension)
            
            # Записываем файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(clean_content)
            
            output_files.append(file_path)
        
        return output_files
    
        
    def parse_txt_structure(self, content: str) -> Dict[str, str]:
        structure: Dict[str, str] = {}

        lines = content.split('\n')
        current_file: Optional[str] = None
        current_content: List[str] = []

        header_re = re.compile(r'^=====\s+(?P<name>.+?)\s+=====$')

        def flush():
            nonlocal current_file, current_content
            if current_file is not None:
                structure[current_file] = '\n'.join(current_content).strip('\n')

        for line in lines:
            m = header_re.match(line.strip())
            if m:
                flush()
                current_file = m.group('name').strip()
                current_content = []
                continue

            if current_file is None:
                continue

            if line.startswith('Path:') or line.startswith('Lines:') or line.startswith('Size:'):
                continue
            if line and line.strip('-') == '':
                continue

            current_content.append(line)

        flush()
        return {k: v for k, v in structure.items() if v.strip()}
