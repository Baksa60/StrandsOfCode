import os
import chardet
from pathlib import Path
from typing import Optional, Tuple


def detect_file_encoding(file_path: Path) -> str:
    """
    Определяет кодировку файла.
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        Строка с названием кодировки (utf-8, cp1251 и т.д.)
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Читаем первые 10KB для определения кодировки
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'
    except Exception:
        return 'utf-8'


def read_file_safe(file_path: Path, encoding: Optional[str] = None) -> Tuple[str, str]:
    """
    Безопасно читает файл с автоматическим определением кодировки.
    
    Args:
        file_path: Путь к файлу
        encoding: Кодировка (если None, определяется автоматически)
        
    Returns:
        Кортеж (содержимое_файла, использованная_кодировка)
    """
    detected = None
    if encoding is None:
        detected = detect_file_encoding(file_path)
    else:
        detected = encoding

    # chardet иногда ошибается (особенно на коротких файлах), поэтому сначала пробуем UTF-8
    # и только потом используем детектированную кодировку.
    candidates = ['utf-8-sig', 'utf-8']
    if detected:
        candidates.append(detected)
    candidates.extend(['cp1251', 'latin1'])

    last_error: Optional[Exception] = None
    for enc in candidates:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.read()
            return content, enc
        except UnicodeDecodeError as e:
            last_error = e
            continue

    if last_error:
        raise last_error
    raise UnicodeDecodeError('utf-8', b'', 0, 1, 'Unable to decode file')


def write_file_safe(file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
    """
    Безопасно записывает файл, создавая директории при необходимости.
    
    Args:
        file_path: Путь к файлу
        content: Содержимое для записи
        encoding: Кодировка записи
        
    Returns:
        True в случае успеха, False в случае ошибки
    """
    try:
        # Создаем директории если их нет
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False


def get_file_size_human(file_path: Path) -> str:
    """
    Возвращает размер файла в человекочитаемом формате.
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        Строка с размером (B, KB, MB, GB)
    """
    try:
        size = file_path.stat().st_size
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except Exception:
        return "0 B"


def count_lines(file_path: Path, encoding: Optional[str] = None) -> int:
    """
    Подсчитывает количество строк в файле.
    
    Args:
        file_path: Путь к файлу
        encoding: Кодировка файла
        
    Returns:
        Количество строк
    """
    try:
        if encoding is None:
            encoding = detect_file_encoding(file_path)
            
        with open(file_path, 'r', encoding=encoding) as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def is_text_file(file_path: Path, sample_size: int = 1024) -> bool:
    """
    Проверяет, является ли файл текстовым.
    
    Args:
        file_path: Путь к файлу
        sample_size: Размер выборки для анализа
        
    Returns:
        True если файл текстовый, False если бинарный
    """
    try:
        with open(file_path, 'rb') as f:
            sample = f.read(sample_size)
            
        # Проверяем наличие нулевых байтов (признак бинарного файла)
        if b'\x00' in sample:
            return False
            
        # Пытаемся декодировать как UTF-8
        try:
            sample.decode('utf-8')
            return True
        except UnicodeDecodeError:
            # Пробуем определить кодировку
            encoding = detect_file_encoding(file_path)
            try:
                sample.decode(encoding)
                return True
            except:
                return False
    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """
    Очищает имя файла от недопустимых символов.
    
    Args:
        filename: Исходное имя файла
        
    Returns:
        Очищенное имя файла
    """
    # Недопустимые символы для Windows
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Удаляем точки в начале и конце
    filename = filename.strip('.')
    
    # Ограничиваем длину
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        max_name_len = 255 - len(ext)
        filename = name[:max_name_len] + ext
    
    return filename


def ensure_unique_filename(file_path: Path) -> Path:
    """
    Гарантирует уникальность имени файла, добавляя номер при необходимости.
    
    Args:
        file_path: Исходный путь к файлу
        
    Returns:
        Уникальный путь к файлу
    """
    if not file_path.exists():
        return file_path
    
    counter = 1
    while True:
        new_path = file_path.with_name(f"{file_path.stem}_{counter}{file_path.suffix}")
        if not new_path.exists():
            return new_path
        counter += 1


def get_relative_path(file_path: Path, base_path: Path) -> Path:
    """
    Безопасно получает относительный путь.
    
    Args:
        file_path: Путь к файлу
        base_path: Базовый путь
        
    Returns:
        Относительный путь
    """
    try:
        return file_path.relative_to(base_path)
    except ValueError:
        # Если файл находится вне базовой директории
        return file_path