"""
Базовый класс для обратных конвертеров (текст → код)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime


class BaseReverseConverter(ABC):
    """
    Базовый класс для конвертации текста обратно в код
    """
    
    def __init__(self):
        self.supported_extensions = ['.txt', '.md', '.html', '.json']
        
    @abstractmethod
    def convert_to_code(self, text_content: str, output_folder: Path, 
                          language: Optional[str] = None, 
                          file_structure: Optional[Dict[str, Any]] = None) -> dict:
        """
        Конвертирует текст обратно в код
        
        Args:
            text_content: Текст для конвертации
            output_folder: Папка для сохранения результатов
            language: Язык программирования (если известен)
            file_structure: Структура файлов и папок для восстановления
            
        Returns:
            dict: Результат конвертации со статистикой
        """
        pass
    
    def detect_language(self, content: str) -> str:
        """
        Определяет язык программирования по содержимому
        """
        # Простая эвристика для определения языка
        content_lower = content.lower()
        
        # Python индикаторы
        python_indicators = ['def ', 'import ', 'from ', 'class ', 'if __name__', 'print(']
        
        # JavaScript индикаторы  
        js_indicators = ['function ', 'const ', 'let ', 'var ', '=>', 'console.log(']
        
        # TypeScript индикаторы
        ts_indicators = ['interface ', 'type ', 'export ', 'as ', ': string', ': number']
        
        # Подсчитываем индикаторы
        python_score = sum(1 for indicator in python_indicators if indicator in content_lower)
        js_score = sum(1 for indicator in js_indicators if indicator in content_lower)
        ts_score = sum(1 for indicator in ts_indicators if indicator in content_lower)
        
        # Определяем язык с наибольшим количеством индикаторов
        scores = {'python': python_score, 'javascript': js_score, 'typescript': ts_score}
        return max(scores, key=scores.get)
    
    def parse_file_structure(self, content: str) -> Dict[str, Any]:
        """
        Парсит структуру файлов из текста
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
                current_file = line.split('📄 ')[1].strip()
                current_content = []
            
            # Собираем контент файла
            elif current_file and (line.startswith('```') or line.strip()):
                current_content.append(line)
        
        # Сохраняем последний файл
        if current_file and current_content:
            structure[current_file] = '\n'.join(current_content)
        
        return structure
    
    def clean_code_content(self, content: str) -> str:
        """
        Очищает контент от артефактов конвертации
        """
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            if line.startswith('Path:') or line.startswith('Lines:') or line.startswith('Size:'):
                continue
            if line and line.strip('-') == '':
                continue

            # Удаляем нумерацию строк если есть
            if line.strip() and line[0].isdigit() and '│' in line:
                cleaned_lines.append(line.split('│', 1)[1] if '│' in line else line)
            elif len(line) >= 6 and line[:4].isdigit() and line[4:6] == ': ':
                cleaned_lines.append(line[6:])
            else:
                cleaned_lines.append(line)
        
        # Удаляем маркеры блоков кода
        content = '\n'.join(cleaned_lines)
        content = content.replace('```python', '').replace('```javascript', '').replace('```typescript', '')
        content = content.replace('```', '')
        
        return content.strip()
    
    def create_result(self, output_files: List[Path], start_time: datetime) -> dict:
        """
        Создает результат конвертации
        """
        return {
            'total_files': len(output_files),
            'converted_files': len(output_files),
            'failed_files': [],
            'output_files': output_files,
            'total_size': sum(f.stat().st_size for f in output_files if f.exists()),
            'start_time': start_time,
            'end_time': datetime.now(),
            'errors': []
        }
