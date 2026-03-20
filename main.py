import sys
import logging
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication
from version import __version__


def setup_logging():
    """Настраивает базовую конфигурацию логгера"""
    # Создаем папку для логов если её нет
    log_dir = Path.home() / ".strands_of_code"
    log_dir.mkdir(exist_ok=True)
    
    # Настройка логгера
    log_file = log_dir / "strands_of_code.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    # Настраиваем логгер перед запуском приложения
    setup_logging()
    
    app = QApplication(sys.argv)
    
    # Установка свойств приложения
    app.setApplicationName("StrandsOfCode")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("StrandsOfCode")
    
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
