from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt


class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выполнение конвертации")
        self.setModal(True)
        self.setFixedSize(400, 150)
        
        layout = QVBoxLayout(self)
        
        # Статус
        self.status_label = QLabel("Подготовка...")
        layout.addWidget(self.status_label)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)
        
        # Кнопка отмены (можно добавить позже)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_button = QPushButton("Отмена")
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
    def update_status(self, message):
        self.status_label.setText(message)
        
    def close_dialog(self):
        self.accept()


class ErrorDialog(QDialog):
    def __init__(self, error_message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ошибка")
        self.setModal(True)
        self.setFixedSize(500, 200)
        
        layout = QVBoxLayout(self)
        
        # Иконка и сообщение
        message_layout = QHBoxLayout()
        
        # Можно добавить иконку ошибки
        
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setPlainText(error_message)
        message_layout.addWidget(self.error_text)
        
        layout.addLayout(message_layout)
        
        # Кнопка закрытия
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)