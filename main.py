import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    
    # Установка свойств приложения
    app.setApplicationName("py2txt_tool")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("py2txt_tool")
    
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
