"""
Версия и метаданные продукта StrandsOfCode
"""

__version__ = "1.4.0"
__version_name__ = "Clean Code Edition"
__build_date__ = "2026-03-21"
__author__ = "Baksa60"
__email__ = "Baksa60@yandex.ru"
__description__ = "Профессиональный конвертер кода с улучшенной архитектурой"
__copyright__ = f"© 2026 {__author__}"
__license__ = "MIT"

# Метаданные приложения
APP_INFO = {
    "name": "StrandsOfCode",
    "version": __version__,
    "version_name": __version_name__,
    "build_date": __build_date__,
    "author": __author__,
    "email": __email__,
    "description": __description__,
    "copyright": __copyright__,
    "license": __license__,
    "website": "https://github.com/StrandsOfCode/StrandsOfCode",
    "repository": "https://github.com/StrandsOfCode/StrandsOfCode.git",
    "docs": "https://github.com/StrandsOfCode/StrandsOfCode/wiki",
    "issues": "https://github.com/StrandsOfCode/StrandsOfCode/issues"
}

# История версий
VERSION_HISTORY = [
    {
        "version": "1.3.0",
        "name": "Drag & Drop Edition",
        "date": "2026-03-19",
        "features": [
            "Drag & Drop функциональность",
            "Визуальная индикация зоны Drop",
            "Умное определение формата файлов (90-95% точность)",
            "Автоматический выбор типа источника",
            "Поддержка множественного drag & drop",
            "Обработка разных типов контента (файлы, папки)"
        ]
    },
    {
        "version": "1.2.0", 
        "name": "HTML Export",
        "date": "2026-03-18",
        "features": [
            "Экспорт в HTML с CSS стилями",
            "Подсветка синтаксиса в HTML",
            "Адаптивный дизайн HTML",
            "Улучшенная верстка"
        ]
    },
    {
        "version": "1.1.0",
        "name": "Smart Conversion",
        "date": "2026-03-17", 
        "features": [
            "Умная система сохранения",
            "Выбор папки до конвертации",
            "Генерация уникальных имен",
            "Запоминание настроек"
        ]
    },
    {
        "version": "1.0.0",
        "name": "Initial Release",
        "date": "2026-03-16",
        "features": [
            "Базовая конвертация кода в текст",
            "Поддержка Python, JavaScript, TypeScript",
            "Конвертация текста в код",
            "Современный UI с темами"
        ]
    }
]

def get_version_string():
    """Возвращает полную строку версии"""
    return f"{__version__} ({__version_name__})"

def get_app_info():
    """Возвращает полную информацию о приложении"""
    return APP_INFO.copy()

def get_version_history():
    """Возвращает историю версий"""
    return VERSION_HISTORY.copy()

def is_beta():
    """Проверяет является ли версия бета"""
    return "beta" in __version__.lower() or "alpha" in __version__.lower()

def get_build_info():
    """Возвращает информацию о сборке"""
    return {
        "version": __version__,
        "build_date": __build_date__,
        "is_beta": is_beta(),
        "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}"
    }
