"""
Диалоговое окно истории конвертаций
"""

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QComboBox, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QWidget, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont


class HistoryDialog(QDialog):
    """Диалоговое окно для отображения истории конвертаций"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📜 История конвертаций")
        self.setGeometry(200, 200, 900, 700)
        self.setMinimumSize(800, 600)
        
        # Данные истории (временно - потом будут загружаться из файла)
        self.history_data = []
        
        self.init_ui()
        self.load_history_data()
        
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок и фильтры
        header_group = QGroupBox("🔍 Фильтры истории")
        header_layout = QHBoxLayout()
        
        # Фильтр по статусу
        header_layout.addWidget(QLabel("Статус:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "📋 Все",
            "✅ Успешные", 
            "❌ Неудачные",
            "⛔ Отмененные"
        ])
        self.status_filter.currentTextChanged.connect(self.filter_history)
        header_layout.addWidget(self.status_filter)
        
        header_layout.addStretch()
        
        # Кнопка очистки истории
        self.clear_button = QPushButton("🗑️ Очистить историю")
        self.clear_button.clicked.connect(self.clear_history)
        header_layout.addWidget(self.clear_button)
        
        # Кнопка закрытия
        self.close_button = QPushButton("❌ Закрыть")
        self.close_button.clicked.connect(self.accept)
        header_layout.addWidget(self.close_button)
        
        header_group.setLayout(header_layout)
        layout.addWidget(header_group)
        
        # Таблица истории
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "📅 Дата и время",
            "📁 Источник", 
            "📤 Формат",
            "📊 Статус",
            "⏱️ Время",
            "📏 Размер"
        ])
        
        # Настройка таблицы
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.history_table)
        
        # Информационная панель
        info_group = QGroupBox("📊 Статистика")
        info_layout = QHBoxLayout()
        
        self.total_label = QLabel("Всего записей: 0")
        self.success_label = QLabel("✅ Успешных: 0")
        self.failed_label = QLabel("❌ Неудачных: 0")
        self.cancelled_label = QLabel("⛔ Отмененных: 0")
        
        info_layout.addWidget(self.total_label)
        info_layout.addWidget(self.success_label)
        info_layout.addWidget(self.failed_label)
        info_layout.addWidget(self.cancelled_label)
        info_layout.addStretch()
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
    def load_history_data(self):
        """Загрузка данных истории (временно - демо-данные)"""
        # Временные демо-данные
        self.history_data = [
            {
                "timestamp": datetime.now(),
                "source": "C:\\Projects\\my_project\\src",
                "source_format": "Python",
                "output_format": "Markdown", 
                "status": "success",
                "duration": 2.5,
                "size": 1024 * 512,  # 512 KB
                "files_count": 15
            },
            {
                "timestamp": datetime.now(),
                "source": "C:\\Projects\\app.js",
                "source_format": "JavaScript",
                "output_format": "HTML",
                "status": "success", 
                "duration": 0.8,
                "size": 1024 * 128,  # 128 KB
                "files_count": 1
            },
            {
                "timestamp": datetime.now(),
                "source": "C:\\Projects\\broken_project",
                "source_format": "TypeScript",
                "output_format": "TXT",
                "status": "failed",
                "duration": 1.2,
                "size": 0,
                "files_count": 0,
                "error": "Ошибка доступа к файлам"
            },
            {
                "timestamp": datetime.now(),
                "source": "C:\\Projects\\large_project",
                "source_format": "Python",
                "output_format": "JSON",
                "status": "cancelled",
                "duration": 0.5,
                "size": 0,
                "files_count": 0
            }
        ]
        
        self.update_table()
        self.update_statistics()
        
    def filter_history(self):
        """Фильтрация истории по статусу"""
        status_filter = self.status_filter.currentText()
        
        if status_filter == "📋 Все":
            filtered_data = self.history_data
        elif status_filter == "✅ Успешные":
            filtered_data = [item for item in self.history_data if item["status"] == "success"]
        elif status_filter == "❌ Неудачные":
            filtered_data = [item for item in self.history_data if item["status"] == "failed"]
        elif status_filter == "⛔ Отмененные":
            filtered_data = [item for item in self.history_data if item["status"] == "cancelled"]
        else:
            filtered_data = self.history_data
            
        self.update_table(filtered_data)
        
    def update_table(self, data=None):
        """Обновление таблицы истории"""
        if data is None:
            data = self.history_data
            
        self.history_table.setRowCount(len(data))
        
        for row, item in enumerate(data):
            # Дата и время
            date_time = item["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            self.history_table.setItem(row, 0, QTableWidgetItem(date_time))
            
            # Источник
            source_name = Path(item["source"]).name
            if item.get("files_count", 0) > 1:
                source_name += f" ({item['files_count']} файлов)"
            self.history_table.setItem(row, 1, QTableWidgetItem(source_name))
            
            # Формат конвертации
            format_text = f"{item.get('source_format', '?')} → {item.get('output_format', '?')}"
            self.history_table.setItem(row, 2, QTableWidgetItem(format_text))
            
            # Статус
            status_icons = {
                "success": "✅ Успешно",
                "failed": "❌ Ошибка", 
                "cancelled": "⛔ Отменено"
            }
            status_text = status_icons.get(item["status"], "❓ Неизвестно")
            self.history_table.setItem(row, 3, QTableWidgetItem(status_text))
            
            # Время выполнения
            duration = item.get("duration", 0)
            if hasattr(duration, 'total_seconds'):
                duration_text = f"{duration.total_seconds():.1f} сек"
            elif isinstance(duration, (int, float)) and duration > 0:
                duration_text = f"{duration:.1f} сек"
            else:
                duration_text = "-"
            self.history_table.setItem(row, 4, QTableWidgetItem(duration_text))
            
            # Размер
            size = item.get("size", 0)
            if size > 1024 * 1024:
                size_text = f"{size / (1024 * 1024):.1f} МБ"
            elif size > 1024:
                size_text = f"{size / 1024:.1f} КБ"
            elif size > 0:
                size_text = f"{size} Б"
            else:
                size_text = "-"
            self.history_table.setItem(row, 5, QTableWidgetItem(size_text))
            
    def update_statistics(self):
        """Обновление статистики"""
        total = len(self.history_data)
        success = len([item for item in self.history_data if item["status"] == "success"])
        failed = len([item for item in self.history_data if item["status"] == "failed"])
        cancelled = len([item for item in self.history_data if item["status"] == "cancelled"])
        
        self.total_label.setText(f"Всего записей: {total}")
        self.success_label.setText(f"✅ Успешных: {success}")
        self.failed_label.setText(f"❌ Неудачных: {failed}")
        self.cancelled_label.setText(f"⛔ Отмененных: {cancelled}")
        
    def clear_history(self):
        """Очистка истории"""
        # Временное подтверждение
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            "Вы уверены, что хотите очистить всю историю конвертаций?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_data.clear()
            self.update_table()
            self.update_statistics()
