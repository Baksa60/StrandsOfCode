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


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Информация о программе
        info_text = """
        <h2>py2txt_tool</h2>
        <p>Версия: 1.0.0</p>
        <p>Конвертер Python файлов в текстовый формат</p>
        
        <h3>Возможности:</h3>
        <ul>
        <li>Конвертация отдельных файлов</li>
        <li>Обработка папок и проектов</li>
        <li>Создание объединенных файлов</li>
        <li>Добавление метаданных и номеров строк</li>
        </ul>
        
        <h3>Технологии:</h3>
        <p>Python 3.8+, PyQt6</p>
        
        <p><b>Разработано для удобной передачи кода в текстовом формате</b></p>
        """
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info_label)
        
        # Кнопка закрытия
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)


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