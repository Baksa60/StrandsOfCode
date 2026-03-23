"""
Диалог предпросмотра файлов перед конвертацией
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLabel, QPushButton,
    QDialogButtonBox, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from pathlib import Path
from utils.file_utils import read_file_safe, count_lines
import os


class FilePreviewDialog(QDialog):
    """Диалог для предпросмотра списка файлов перед конвертацией"""
    
    def __init__(self, parent, files):
        super().__init__(parent)
        self.files = files
        self.setWindowTitle("🔍 Предпросмотр файлов")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        self.init_ui()
        self.populate_table()
        
    def init_ui(self):
        """Инициализирует UI"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        header_label = QLabel(f"📁 Найдено файлов: {len(self.files)}")
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(12)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Создаем сплиттер
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Таблица файлов
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["📁 Файл", "📏 Размер", "📝 Строк", "💾 Тип"])
        
        # Настраиваем таблицу
        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Файл - растягивается
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Размер - по содержимому
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Строки - по содержимому
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Тип - по содержимому
        
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.file_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Область предпросмотра содержимого файла
        self.preview_area = QTextEdit()
        self.preview_area.setReadOnly(True)
        self.preview_area.setPlaceholderText("Выберите файл для предпросмотра содержимого...")
        
        # Устанавливаем моноширинный шрифт для кода
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.preview_area.setFont(font)
        
        # Добавляем в сплиттер
        splitter.addWidget(self.file_table)
        splitter.addWidget(self.preview_area)
        splitter.setSizes([400, 300])  # 40% таблица, 60% предпросмотр
        
        layout.addWidget(splitter)
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        # Кнопка обновления
        refresh_button = QPushButton("🔄 Обновить")
        refresh_button.clicked.connect(self.refresh_file_info)
        buttons.addButton(refresh_button, QDialogButtonBox.ButtonRole.ActionRole)
        
        layout.addWidget(buttons)
        
    def populate_table(self):
        """Заполняет таблицу файлами"""
        self.file_table.setRowCount(len(self.files))
        
        for row, file_path in enumerate(self.files):
            # Имя файла
            relative_path = file_path.name
            item = QTableWidgetItem(relative_path)
            item.setToolTip(str(file_path))
            self.file_table.setItem(row, 0, item)
            
            # Размер файла
            try:
                size = file_path.stat().st_size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size // 1024} KB"
                else:
                    size_str = f"{size // (1024 * 1024)} MB"
            except:
                size_str = "N/A"
            item = QTableWidgetItem(size_str)
            self.file_table.setItem(row, 1, item)
            
            # Количество строк
            try:
                lines = count_lines(file_path)
                item = QTableWidgetItem(str(lines))
            except:
                item = QTableWidgetItem("N/A")
            self.file_table.setItem(row, 2, item)
            
            # Тип файла
            extension = file_path.suffix.lower()
            type_map = {
                '.py': '🐍 Python',
                '.js': '🟨 JavaScript', 
                '.ts': '🔷 TypeScript',
                '.jsx': '⚛️ React JSX',
                '.tsx': '⚛️ React TSX',
                '.txt': '📄 Текст',
                '.md': '📝 Markdown',
                '.html': '🌐 HTML',
                '.json': '🧾 JSON',
                '.css': '🎨 CSS',
                '.xml': '📄 XML',
                '.yaml': '📄 YAML',
                '.yml': '📄 YML'
            }
            file_type = type_map.get(extension, f'📄 {extension[1:].upper()}')
            item = QTableWidgetItem(file_type)
            self.file_table.setItem(row, 3, item)
    
    def on_selection_changed(self):
        """Обрабатывает изменение выбора файла"""
        current_row = self.file_table.currentRow()
        if current_row >= 0 and current_row < len(self.files):
            file_path = self.files[current_row]
            self.show_file_content(file_path)
        else:
            self.preview_area.clear()
            self.preview_area.setPlaceholderText("Выберите файл для предпросмотра содержимого...")
    
    def show_file_content(self, file_path):
        """Показывает содержимое выбранного файла"""
        try:
            content, _ = read_file_safe(file_path)
            if len(content) > 10000:  # Ограничиваем предпросмотр 10KB
                content = content[:10000] + "\n\n... (показано первые 10KB из " + str(len(content)) + " символов)"
            
            self.preview_area.setPlainText(content)
            # Прокрутка в начало
            cursor = self.preview_area.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.preview_area.setTextCursor(cursor)
            
        except Exception as e:
            self.preview_area.setPlainText(f"Ошибка чтения файла: {str(e)}")
    
    def refresh_file_info(self):
        """Обновляет информацию о файлах"""
        self.populate_table()
        if self.file_table.currentRow() >= 0:
            current_row = self.file_table.currentRow()
            if current_row < len(self.files):
                file_path = self.files[current_row]
                self.show_file_content(file_path)
