import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QPushButton, QComboBox, QRadioButton, QButtonGroup,
    QTextEdit, QProgressBar, QFileDialog, QMessageBox, QCheckBox,
    QSplitter, QGridLayout, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QThread, QMimeData
from PyQt6.QtGui import QIcon, QFont, QPalette, QDragEnterEvent, QDropEvent, QPainter, QColor
from controllers.convert_controller import ConvertController
from models.conversion_options import ConversionOptions
from ui.styles import apply_theme
from utils.cancellation import ConversionCancelled


class ConversionWorker(QThread):
    finished = pyqtSignal(object)
    progress = pyqtSignal(str)
    
    def __init__(self, controller, options):
        super().__init__()
        self.controller = controller
        self.options = options
    
    def run(self):
        try:
            result = self.controller.run(self.options)
            # Добавляем информацию о папке в результат
            if isinstance(result, dict):
                result['output_folder'] = self.options.output_folder
                result['success'] = True
            else:
                # Если результат не словарь, оборачиваем его
                result = {
                    'data': result,
                    'output_folder': self.options.output_folder,
                    'success': True
                }
            self.finished.emit(result)
        except ConversionCancelled:
            cancelled_result = {
                'cancelled': True,
                'output_folder': self.options.output_folder,
                'success': False
            }
            self.finished.emit(cancelled_result)
        except Exception as e:
            error_result = {
                'error': str(e),
                'output_folder': self.options.output_folder,
                'success': False
            }
            self.finished.emit(error_result)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = ConvertController()
        self.selected_paths = []
        self.recent_files = []  # Список недавних файлов
        self.last_save_folder = None  # Последнее место сохранения
        self.is_drag_active = False  # Состояние drag & drop
        self.worker = None
        self.init_ui()
        self.load_settings()  # Загружаем сохраненные настройки
        
        # Включаем Drag & Drop
        self.setAcceptDrops(True)
        
    def init_ui(self):
        self.setWindowTitle("🧬 StrandsOfCode - Конвертер кода")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(850, 750)
        
        # Применяем стили
        apply_theme(QApplication.instance(), "dark")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout с отступами
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Заголовок приложения с переключателем тем
        header_layout = QHBoxLayout()
        title_label = QLabel("🧬 StrandsOfCode")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Кнопка "О программе"
        about_button = QPushButton("ℹ️ О программе")
        about_button.setMaximumWidth(120)
        about_button.clicked.connect(self.show_about)
        header_layout.addWidget(about_button)
        
        # Переключатель тем
        theme_layout = QHBoxLayout()
        theme_label = QLabel("🎨 Тема:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["☀️ Светлая", "🌙 Темная"])
        self.theme_combo.setCurrentText("🌙 Темная")
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        
        header_layout.addLayout(theme_layout)
        main_layout.addLayout(header_layout)
        
        # Комбо-панель с информацией и недавними файлами
        combo_panel = QWidget()
        combo_layout = QHBoxLayout(combo_panel)
        combo_layout.setSpacing(20)
        
        # Левая часть - статистика
        stats_group = QGroupBox("📊 Информация о проекте")
        stats_layout = QVBoxLayout()
        
        self.files_count_label = QLabel("🔧 Файлов: 0")
        self.folders_count_label = QLabel("📁 Папок: 0")
        self.size_count_label = QLabel("📏 Размер: 0 KB")
        self.last_action_label = QLabel("⏰ Последнее действие: --")
        
        stats_layout.addWidget(self.files_count_label)
        stats_layout.addWidget(self.folders_count_label)
        stats_layout.addWidget(self.size_count_label)
        stats_layout.addWidget(self.last_action_label)
        stats_group.setLayout(stats_layout)
        
        # Правая часть - недавние файлы
        recent_group = QGroupBox("⏰ Недавние файлы")
        recent_layout = QVBoxLayout()
        
        self.recent_files_widget = QWidget()
        self.recent_files_layout = QVBoxLayout(self.recent_files_widget)
        
        clear_button = QPushButton("🗑️ Очистить историю")
        clear_button.setMaximumHeight(30)
        clear_button.clicked.connect(self.clear_recent_files)
        
        recent_layout.addWidget(self.recent_files_widget)
        recent_layout.addWidget(clear_button)
        recent_group.setLayout(recent_layout)
        
        combo_layout.addWidget(stats_group)
        combo_layout.addWidget(recent_group)
        
        main_layout.addWidget(combo_panel)
        
        # Создаем сплиттер для лучшей компоновки
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель - настройки
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)
        
        # Группа выбора источника
        source_group = QGroupBox("📁 Источник файлов")
        source_layout = QVBoxLayout()
        source_layout.setSpacing(10)
        
        # Тип и формат в одной строке
        header_layout = QHBoxLayout()
        
        # Выбор типа источника слева
        header_layout.addWidget(QLabel("📋 Тип:"))
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems([
            "📄 Один файл",
            "📁 Несколько файлов", 
            "📂 Папка",
            "📂 Папка (рекурсивно)"
        ])
        self.source_type_combo.currentTextChanged.connect(self.on_source_type_changed)
        self.source_type_combo.setMaximumWidth(200)
        header_layout.addWidget(self.source_type_combo)
        
        # Растягивающееся пространство посередине
        header_layout.addStretch()
        
        # Выбор формата исходных файлов справа
        header_layout.addWidget(QLabel("📥 Формат ИЗ:"))
        self.source_format_combo = QComboBox()
        self.source_format_combo.addItems([
            "🧩 Все поддерживаемые",
            "🐍 Python (.py)", 
            "🟨 JavaScript (.js)", 
            "🔷 TypeScript (.ts)", 
            "📄 Текст (.txt)", 
            "📝 Markdown (.md)", 
            "🌐 HTML (.html)"
        ])
        self.source_format_combo.currentTextChanged.connect(self.on_source_format_changed)
        self.source_format_combo.setMaximumWidth(180)
        header_layout.addWidget(self.source_format_combo)
        
        # Кнопка выбора под заголовками
        select_layout = QHBoxLayout()
        self.select_button = QPushButton("📂 Выбрать")
        self.select_button.clicked.connect(self.select_source)
        select_layout.addWidget(self.select_button)
        
        # Метка выбранного файла
        self.selected_label = QLabel("Ничего не выбрано")
        self.selected_label.setObjectName("selectedLabel")
        self.selected_label.setWordWrap(True)
        select_layout.addWidget(self.selected_label, 1)
        
        source_layout.addLayout(header_layout)
        source_layout.addLayout(select_layout)
        source_group.setLayout(source_layout)
        
        # Группа настроек вывода
        output_group = QGroupBox("💾 Сохранение результата")
        output_layout = QVBoxLayout()
        output_layout.setSpacing(12)
        
        # Режим и формат в одной строке
        output_header_layout = QHBoxLayout()
        
        # Режим вывода слева
        output_header_layout.addWidget(QLabel("📋 Режим:"))
        self.output_mode_combo = QComboBox()
        self.output_mode_combo.addItems(["📄 Отдельные файлы", "📄 В один файл"])
        output_header_layout.addWidget(self.output_mode_combo)
        self.output_mode_combo.setMaximumWidth(150)
        
        # Растягивающееся пространство посередине
        output_header_layout.addStretch()
        
        # Формат вывода справа
        output_header_layout.addWidget(QLabel("📤 Формат В:"))
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems([
            "📄 Текст (.txt)", 
            "📝 Markdown (.md)", 
            "🌐 HTML (.html)",
            "🐍 Python (.py)",
            "🟨 JavaScript (.js)",
            "🔷 TypeScript (.ts)"
        ])
        self.output_format_combo.currentTextChanged.connect(self.on_format_changed)
        self.output_format_combo.setMaximumWidth(180)
        output_header_layout.addWidget(self.output_format_combo)
        
        output_layout.addLayout(output_header_layout)
        
        # Выбор места сохранения
        save_location_layout = QHBoxLayout()
        save_location_layout.addWidget(QLabel("📂 Место:"))
        self.save_path_edit = QLineEdit()
        self.save_path_edit.setReadOnly(True)
        self.save_path_edit.setPlaceholderText("Выберите папку для сохранения...")
        save_location_layout.addWidget(self.save_path_edit, 1)
        
        self.browse_save_button = QPushButton("📂 Обзор")
        self.browse_save_button.clicked.connect(self.browse_save_location)
        save_location_layout.addWidget(self.browse_save_button)
        
        output_layout.addLayout(save_location_layout)
        
        # Ввод имени файла
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("📝 Имя:"))
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText("Введите имя файла...")
        filename_layout.addWidget(self.filename_edit, 1)
        
        self.generate_filename_button = QPushButton("🎲 Сгенерировать")
        self.generate_filename_button.clicked.connect(self.generate_filename)
        filename_layout.addWidget(self.generate_filename_button)
        
        output_layout.addLayout(filename_layout)
        
        # Настройки
        self.add_headers_checkbox = QCheckBox("📝 Добавлять заголовки и метаданные")
        self.add_headers_checkbox.setChecked(True)
        output_layout.addWidget(self.add_headers_checkbox)

        self.add_line_numbers_checkbox = QCheckBox("🔢 Добавлять нумерацию строк")
        self.add_line_numbers_checkbox.setChecked(True)
        output_layout.addWidget(self.add_line_numbers_checkbox)
        
        output_group.setLayout(output_layout)
        
        # Кнопка запуска
        self.convert_button = QPushButton("🚀 Конвертировать")
        self.convert_button.setObjectName("convertButton")
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setEnabled(False)
        self.convert_button.setMinimumHeight(50)

        self.cancel_button = QPushButton("⛔ Отмена")
        self.cancel_button.clicked.connect(self.cancel_conversion)
        self.cancel_button.setVisible(False)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setMinimumHeight(40)
        
        left_layout.addWidget(source_group)
        left_layout.addWidget(output_group)
        left_layout.addWidget(self.convert_button)
        left_layout.addWidget(self.cancel_button)
        left_layout.addStretch()
        
        # Правая панель - лог и прогресс
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(15)
        
        # Прогресс бар
        progress_group = QGroupBox("📊 Прогресс выполнения")
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        progress_layout.addWidget(self.progress_bar)
        progress_group.setLayout(progress_layout)
        
        # Область логов
        log_group = QGroupBox("📜 Лог операций")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setMinimumHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # Кнопка очистки лога
        clear_log_layout = QHBoxLayout()
        self.clear_log_button = QPushButton("🗑️ Очистить лог")
        self.clear_log_button.clicked.connect(self.clear_log)
        clear_log_layout.addWidget(self.clear_log_button)
        clear_log_layout.addStretch()
        log_layout.addLayout(clear_log_layout)
        
        log_group.setLayout(log_layout)
        
        right_layout.addWidget(progress_group)
        right_layout.addWidget(log_group)
        
        # Добавляем панели в сплиттер
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)
    
    def load_settings(self):
        """Загружает сохраненные настройки"""
        import json
        import os
        
        settings_file = Path.home() / ".strands_of_code_settings.json"
        
        try:
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.last_save_folder = settings.get('last_save_folder')
                if self.last_save_folder:
                    self.save_path_edit.setText(self.last_save_folder)
                
                # Устанавливаем последние значения комбобоксов
                if settings.get('last_source_type'):
                    index = self.source_type_combo.findText(settings['last_source_type'])
                    if index >= 0:
                        self.source_type_combo.setCurrentIndex(index)
                
                if settings.get('last_source_format'):
                    index = self.source_format_combo.findText(settings['last_source_format'])
                    if index >= 0:
                        self.source_format_combo.setCurrentIndex(index)
                
                if settings.get('last_output_format'):
                    index = self.output_format_combo.findText(settings['last_output_format'])
                    if index >= 0:
                        self.output_format_combo.setCurrentIndex(index)
                        
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
    
    def save_settings(self):
        """Сохраняет настройки"""
        import json
        
        settings_file = Path.home() / ".strands_of_code_settings.json"
        
        try:
            settings = {
                'last_save_folder': self.save_path_edit.text(),
                'last_source_type': self.source_type_combo.currentText(),
                'last_source_format': self.source_format_combo.currentText(),
                'last_output_format': self.output_format_combo.currentText()
            }
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
    
    def browse_save_location(self):
        """Открывает диалог выбора папки сохранения"""
        from pathlib import Path
        
        # Предлагаем последнюю папку или Documents по умолчанию
        if self.last_save_folder and Path(self.last_save_folder).exists():
            default_folder = self.last_save_folder
        else:
            default_folder = Path.home() / "Documents" / "StrandsOfCode"
            default_folder.mkdir(parents=True, exist_ok=True)
        
        folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку для сохранения", str(default_folder)
        )
        
        if folder:
            self.save_path_edit.setText(folder)
            self.last_save_folder = folder
            self.save_settings()
    
    def generate_filename(self):
        """Генерирует уникальное имя файла"""
        from datetime import datetime
        from pathlib import Path
        
        if not self.save_path_edit.text():
            QMessageBox.warning(self, "Внимание", "Сначала выберите папку для сохранения")
            return
        
        # Определяем расширение
        format_text = self.output_format_combo.currentText()
        if "Текст" in format_text:
            ext = ".txt"
        elif "Markdown" in format_text:
            ext = ".md"
        elif "HTML" in format_text:
            ext = ".html"
        elif "Python" in format_text:
            ext = ".py"
        elif "JavaScript" in format_text:
            ext = ".js"
        elif "TypeScript" in format_text:
            ext = ".ts"
        else:
            ext = ".txt"
        
        # Генерируем базовое имя
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Правильно извлекаем исходный формат
        source_text = self.source_format_combo.currentText()
        if "Python" in source_text:
            source_format = "Python"
        elif "JavaScript" in source_text:
            source_format = "JavaScript"
        elif "TypeScript" in source_text:
            source_format = "TypeScript"
        elif "Текст" in source_text:
            source_format = "Text"
        elif "Markdown" in source_text:
            source_format = "Markdown"
        elif "HTML" in source_text:
            source_format = "HTML"
        else:
            source_format = "Unknown"
        
        # Правильно извлекаем целевой формат
        output_format_text = self.output_format_combo.currentText()
        if "Текст" in output_format_text:
            target_format = "TXT"
        elif "Markdown" in output_format_text:
            target_format = "MD"
        elif "HTML" in output_format_text:
            target_format = "HTML"
        elif "Python" in output_format_text:
            target_format = "Python"
        elif "JavaScript" in output_format_text:
            target_format = "JS"
        elif "TypeScript" in output_format_text:
            target_format = "TS"
        else:
            target_format = "Unknown"
        
        base_name = f"{source_format}_to_{target_format}_{timestamp}"
        
        # Проверяем уникальность имени
        save_folder = Path(self.save_path_edit.text())
        counter = 1
        final_name = base_name
        
        while (save_folder / (final_name + ext)).exists():
            final_name = f"{base_name}_{counter}"
            counter += 1
        
        self.filename_edit.setText(final_name)
    
    def get_unique_filename(self, base_name: str, extension: str) -> str:
        """Возвращает уникальное имя файла"""
        save_folder = Path(self.save_path_edit.text())
        counter = 1
        final_name = base_name
        
        while (save_folder / (final_name + extension)).exists():
            final_name = f"{base_name}_{counter}"
            counter += 1
        
        return final_name
    
    def clear_log(self):
        """Очищает лог операций"""
        self.log_text.clear()
        self.last_action_label.setText("⏰ Последнее действие: Лог очищен")
    
    # Drag & Drop методы
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Обрабатывает вход в зону Drag & Drop"""
        if event.mimeData().hasUrls():
            # Проверяем, что это файлы или папки
            urls = event.mimeData().urls()
            if urls:
                self.is_drag_active = True
                self.setStyleSheet("MainWindow { border: 3px dashed #4CAF50; }")
                event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Обрабатывает выход из зоны Drag & Drop"""
        self.is_drag_active = False
        self.setStyleSheet("")  # Убираем подсветку
        event.accept()
    
    def dropEvent(self, event: QDropEvent):
        """Обрабатывает сброс файлов/папок"""
        self.is_drag_active = False
        self.setStyleSheet("")  # Убираем подсветку
        
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            paths = []
            
            for url in urls:
                path = Path(url.toLocalFile())
                if path.exists():
                    paths.append(path)
            
            if paths:
                self.process_dropped_files(paths)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def process_dropped_files(self, paths: list[Path]):
        """Обрабатывает перетащенные файлы/папки"""
        if not paths:
            return
        
        # Определяем тип контента
        files = []
        folders = []
        
        for path in paths:
            if path.is_file():
                files.append(path)
            elif path.is_dir():
                folders.append(path)
        
        # Автоматически выбираем тип источника
        if folders and not files:
            # Только папки
            if len(folders) == 1:
                self.source_type_combo.setCurrentText("📂 Папка")
            else:
                self.source_type_combo.setCurrentText("📂 Папка (рекурсивно)")
        elif files and not folders:
            # Только файлы
            if len(files) == 1:
                self.source_type_combo.setCurrentText("📄 Один файл")
            else:
                self.source_type_combo.setCurrentText("📁 Несколько файлов")
        else:
            # Смешанное содержимое
            self.source_type_combo.setCurrentText("📂 Папка (рекурсивно)")
        
        # Устанавливаем выбранные пути
        self.selected_paths = paths
        
        # Обновляем отображение
        if len(paths) == 1:
            self.selected_label.setText(str(paths[0]))
        else:
            self.selected_label.setText(f'Выбрано {len(paths)} элементов')
        
        # Обновляем статистику
        self.update_statistics()
        
        # Обновляем последнее действие
        self.last_action_label.setText(f'⏰ Последнее действие: Перетащено {len(paths)} элементов')
        
        # Включаем кнопку конвертации
        self.convert_button.setEnabled(True)
    
    def change_theme(self, theme_text):
        """Изменяет тему приложения"""
        if "Темная" in theme_text:
            apply_theme(QApplication.instance(), "dark")
        else:
            apply_theme(QApplication.instance(), "light")
    
    def on_source_type_changed(self, type_text):
        """Обрабатывает изменение типа источника"""
        if "Один файл" in type_text:
            self.select_button.setText("📂 Выбрать файл")
        elif "Несколько файлов" in type_text:
            self.select_button.setText("📂 Выбрать файлы")
        else:
            self.select_button.setText("📂 Выбрать папку")

    def on_source_format_changed(self, format_text):
        self._update_output_mode_rules()

    def on_format_changed(self, format_text):
        self._update_output_mode_rules()

    def _update_output_mode_rules(self):
        output_format_text = self.output_format_combo.currentText()
        source_format_text = self.source_format_combo.currentText()

        if "Markdown" in output_format_text or "HTML" in output_format_text:
            self.output_mode_combo.setCurrentText("📄 В один файл")
            self.output_mode_combo.setEnabled(False)
            return

        is_reverse = (
            ("Текст" in source_format_text or "Markdown" in source_format_text or "HTML" in source_format_text)
            and ("Python" in output_format_text or "JavaScript" in output_format_text or "TypeScript" in output_format_text)
        )

        if is_reverse:
            self.output_mode_combo.setCurrentText("📄 Отдельные файлы")
            self.output_mode_combo.setEnabled(False)
        else:
            self.output_mode_combo.setEnabled(True)

    def _get_source_extensions(self, format_text: str):
        """Возвращает список расширений для сбора файлов.
        Пустой список означает мульти-режим (все поддерживаемые расширения).
        """
        if "Все поддерживаемые" in format_text:
            return []
        if "Python" in format_text:
            return [".py"]
        if "JavaScript" in format_text:
            return [".js", ".jsx"]
        if "TypeScript" in format_text:
            return [".ts", ".tsx"]
        if "Текст" in format_text:
            return [".txt"]
        if "Markdown" in format_text:
            return [".md"]
        if "HTML" in format_text:
            return [".html"]
        return []
    
    def show_about(self):
        """Показывает окно 'О программе'"""
        about_text = """
        <h2>🧬 StrandsOfCode</h2>
        <p><b>Версия:</b> 1.1.0</p>
        <p><b>Конвертер кода в текстовый формат</b></p>
        <br>
        <p><b>Поддерживаемые языки:</b></p>
        <ul>
            <li>🐍 Python (.py)</li>
            <li>🟨 JavaScript (.js, .jsx)</li>
            <li>🔷 TypeScript (.ts, .tsx)</li>
        </ul>
        <br>
        <p><b>Форматы вывода:</b></p>
        <ul>
            <li>📄 Текстовые файлы (.txt)</li>
            <li>📄 Объединенный файл</li>
        </ul>
        <br>
        <p><b>Особенности:</b></p>
        <ul>
            <li>🎁 Современный интерфейс с тёмной/светлой темой</li>
            <li>📁 Работа с файлами, папками и проектами</li>
            <li>📊 Статистика и лог операций</li>
            <li>⏰ История недавних файлов</li>
            <li>📝 Метаданные и нумерация строк</li>
        </ul>
        <br>
        <p><i>Прядём код в удобный текстовый формат с ❤️</i></p>
        """
        
        QMessageBox.about(self, "О программе", about_text)
        
    def select_source(self):
        source_type = self.source_type_combo.currentText()
        source_format = self.source_format_combo.currentText()
        
        # Определяем фильтр файлов в зависимости от формата
        file_filter = self._get_file_filter(source_format)
        
        if "Один файл" in source_type:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Выберите файл", "", file_filter
            )
            if file_path:
                self.selected_paths = [Path(file_path)]
                self.selected_label.setText(file_path)
                self.convert_button.setEnabled(True)
                self.update_statistics()
                self.last_action_label.setText("⏰ Последнее действие: Выбран файл")
                
        elif "Несколько файлов" in source_type:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "Выберите файлы", "", file_filter
            )
            if file_paths:
                self.selected_paths = [Path(p) for p in file_paths]
                self.selected_label.setText(f'Выбрано {len(file_paths)} файлов')
                self.convert_button.setEnabled(True)
                self.update_statistics()
                self.last_action_label.setText("⏰ Последнее действие: Выбрано несколько файлов")
                
        elif "Папка" in source_type:
            folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку")
            if folder_path:
                self.selected_paths = [Path(folder_path)]
                self.selected_label.setText(folder_path)
                self.convert_button.setEnabled(True)
                self.update_statistics()
                self.last_action_label.setText("⏰ Последнее действие: Выбрана папка")
        
        # Обновляем последнее действие
        self.last_action_label.setText("⏰ Последнее действие: Выбраны файлы/папки")
    
    def _get_file_filter(self, format_text):
        """Возвращает фильтр файлов в зависимости от формата"""
        if "Все поддерживаемые" in format_text:
            return "Supported files (*.py *.js *.jsx *.ts *.tsx *.txt *.md *.html);;All files (*)"
        elif "Python" in format_text:
            return "Python files (*.py);;All files (*)"
        elif "JavaScript" in format_text:
            return "JavaScript files (*.js *.jsx);;All files (*)"
        elif "TypeScript" in format_text:
            return "TypeScript files (*.ts *.tsx);;All files (*)"
        elif "Текст" in format_text:
            return "Text files (*.txt);;All files (*)"
        elif "Markdown" in format_text:
            return "Markdown files (*.md);;All files (*)"
        elif "HTML" in format_text:
            return "HTML files (*.html);;All files (*)"
        else:
            return "All files (*)"
        
    def update_statistics(self):
        """Обновляет статистику выбранных файлов"""
        if not self.selected_paths:
            self.files_count_label.setText("🔧 Файлов: 0")
            self.folders_count_label.setText("📁 Папок: 0")
            self.size_count_label.setText("📏 Размер: 0 KB")
            return
        
        # Собираем статистику
        total_files = len(self.selected_paths)
        total_size = 0
        folders = set()
        
        for path in self.selected_paths:
            if path.is_file():
                total_size += path.stat().st_size
            elif path.is_dir():
                folders.add(path.name)
                # Рекурсивно считаем файлы и размер
                for file_path in path.rglob("*"):
                    if file_path.is_file() and file_path.suffix in [".py", ".js", ".ts", ".tsx", ".jsx"]:
                        total_files += 1
                        total_size += file_path.stat().st_size
        
        self.files_count_label.setText(f"🔧 Файлов: {total_files}")
        self.folders_count_label.setText(f"📁 Папок: {len(folders)}")
        
        # Конвертируем размер в KB/MB
        if total_size < 1024:
            size_text = f"📏 Размер: {total_size} B"
        elif total_size < 1024 * 1024:
            size_text = f"📏 Размер: {total_size / 1024:.1f} KB"
        else:
            size_text = f"📏 Размер: {total_size / (1024 * 1024):.1f} MB"
        
        self.size_count_label.setText(size_text)
    
    def add_recent_file(self, path: Path):
        """Добавляет файл в недавние"""
        # Удаляем дубликаты
        self.recent_files = [p for p in self.recent_files if str(p) != str(path)]
        # Добавляем в начало
        self.recent_files.insert(0, path)
        # Ограничиваем список до 5 элементов
        self.recent_files = self.recent_files[:5]
        # Обновляем отображение
        self.refresh_recent_files_display()
    
    def refresh_recent_files_display(self):
        """Обновляет отображение недавних файлов"""
        # Очищаем текущие виджеты
        for i in reversed(range(self.recent_files_layout.count())):
            child = self.recent_files_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Добавляем новые
        for file_path in self.recent_files:
            if file_path.is_file():
                button = QPushButton(f"📄 {file_path.name}")
                button.setToolTip(str(file_path))
                button.clicked.connect(lambda checked, p=file_path: self.select_recent_file(p))
                button.setMaximumHeight(25)
                self.recent_files_layout.addWidget(button)
            else:
                button = QPushButton(f"📂 {file_path.name}")
                button.setToolTip(str(file_path))
                button.clicked.connect(lambda checked, p=file_path: self.select_recent_file(p))
                button.setMaximumHeight(25)
                self.recent_files_layout.addWidget(button)
    
    def select_recent_file(self, path: Path):
        """Выбирает недавний файл/папку"""
        self.selected_paths = [path]
        self.selected_label.setText(str(path))
        self.convert_button.setEnabled(True)
        
        # Обновляем статистику
        self.update_statistics()
        
        # Обновляем последнее действие
        self.last_action_label.setText("⏰ Последнее действие: Выбран из недавних")
    
    def clear_recent_files(self):
        """Очищает историю недавних файлов"""
        self.recent_files.clear()
        self.refresh_recent_files_display()
        self.last_action_label.setText("⏰ Последнее действие: История очищена")
        
    def start_conversion(self):
        if not self.selected_paths:
            QMessageBox.warning(self, "Внимание", "Сначала выберите источник файлов")
            return
        
        # Проверяем место сохранения
        if not self.save_path_edit.text():
            QMessageBox.warning(self, "Внимание", "Сначала выберите папку для сохранения")
            return
        
        # Получение настроек
        source_format = self.source_format_combo.currentText()
        output_format_text = self.output_format_combo.currentText()
        
        # Определяем тип источника
        source_type_text = self.source_type_combo.currentText()
        if "Один файл" in source_type_text:
            source_type = "file"
        elif "Несколько файлов" in source_type_text:
            source_type = "files"
        elif "Папка (рекурсивно)" in source_type_text:
            source_type = "folder_recursive"
        else:  # Папка
            source_type = "folder"
        
        # Определяем формат вывода
        if "Текст" in output_format_text:
            output_format = "txt"
        elif "Markdown" in output_format_text:
            output_format = "markdown"
        elif "HTML" in output_format_text:
            output_format = "html"
        elif "Python" in output_format_text:
            output_format = "python"
        elif "JavaScript" in output_format_text:
            output_format = "javascript"
        elif "TypeScript" in output_format_text:
            output_format = "typescript"
        else:
            output_format = "txt"  # по умолчанию
        
        # Определяем режим вывода
        output_mode_text = self.output_mode_combo.currentText()
        output_mode = "separate" if "Отдельные" in output_mode_text else "combined"
        
        # Используем указанную папку сохранения напрямую
        base_folder = Path(self.save_path_edit.text())
        
        # Имя файла (может быть пустым, правила ниже)
        filename_base = self.filename_edit.text().strip()
        
        # Определяем расширение
        if output_format == "txt":
            ext = ".txt"
        elif output_format == "markdown":
            ext = ".md"
        elif output_format == "html":
            ext = ".html"
        elif output_format == "python":
            ext = ".py"
        elif output_format == "javascript":
            ext = ".js"
        elif output_format == "typescript":
            ext = ".ts"
        else:
            ext = ".txt"

        source_stem = None
        if source_type == "file" and self.selected_paths:
            try:
                source_stem = Path(self.selected_paths[0]).stem
            except Exception:
                source_stem = None

        if output_mode == "combined" and source_type != "file" and not filename_base:
            QMessageBox.warning(self, "Внимание", "Для режима 'В один файл' при нескольких файлах/папке нужно ввести имя файла")
            return

        options_filename = None
        if output_mode == "combined":
            final_filename_base = filename_base or (source_stem or "combined")
            final_filename_base = self.get_unique_filename(final_filename_base, ext)
            options_filename = final_filename_base + ext
        else:
            # separate
            if source_type == "file":
                final_filename_base = filename_base or (source_stem or "output")
                final_filename_base = self.get_unique_filename(final_filename_base, ext)
                options_filename = final_filename_base + ext
            else:
                final_filename_base = None
                options_filename = None

        output_folder = base_folder
        
        # Информируем пользователя о месте сохранения
        self.log_text.append(f"📂 Папка сохранения: {base_folder}")
        if options_filename:
            self.log_text.append(f"📝 Имя файла: {options_filename}")
            self.log_text.append(f"📂 Полный путь: {base_folder / options_filename}")
        self.log_text.append("🔄 Начинаю конвертацию...")
        
        # Проверяем права доступа
        try:
            base_folder.mkdir(parents=True, exist_ok=True)
            self.log_text.append(f"✅ Папка доступна: {base_folder}")
        except Exception as e:
            self.log_text.append(f"❌ Ошибка доступа к папке: {e}")
            return
        
        # Создание опций
        options = ConversionOptions(
            source_type=source_type,
            paths=self.selected_paths,
            output_mode=output_mode,
            output_format=output_format,
            output_folder=Path(output_folder),
            extensions=self._get_source_extensions(source_format),
            add_headers=self.add_headers_checkbox.isChecked(),
            add_line_numbers=self.add_line_numbers_checkbox.isChecked(),
            filename=options_filename
        )
        
        # Отладочная информация
        self.log_text.append(f"🔍 Тип источника: {source_type}")
        self.log_text.append(f"📁 Пути: {self.selected_paths}")
        self.log_text.append(f"📤 Формат вывода: {output_format}")
        self.log_text.append(f"📂 Папка вывода: {output_folder}")
        
        # Сохраняем настройки
        self.save_settings()
        
        # Запуск конвертации в отдельном потоке
        self.convert_button.setEnabled(False)
        self.cancel_button.setVisible(True)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        self.worker = ConversionWorker(self.controller, options)
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.start()

    def cancel_conversion(self):
        if self.worker and self.worker.isRunning():
            self.log_text.append("⛔ Запрошена отмена...")
            self.worker.requestInterruption()
            self.cancel_button.setEnabled(False)
        
    def on_conversion_finished(self, result):
        """Обрабатывает завершение конвертации"""
        self.progress_bar.setVisible(False)
        self.convert_button.setEnabled(True)
        self.cancel_button.setVisible(False)
        self.cancel_button.setEnabled(False)
        
        if result.get('success', True):
            # Успешная конвертация
            if 'combined_file' in result:
                output_file = result['combined_file']['output_path']
                self.log_text.append(f"✅ Готово! Файл сохранен: {output_file}")
            elif 'output_files' in result and result['output_files']:
                files = result['output_files']
                self.log_text.append(f"✅ Готово! Сохранено файлов: {len(files)}")
                for file_path in files[:5]:  # Показываем первые 5 файлов
                    self.log_text.append(f"📄 {file_path}")
                if len(files) > 5:
                    self.log_text.append(f"... и еще {len(files) - 5} файлов")
            
            # Статистика
            if 'duration' in result:
                duration = result['duration']
                self.log_text.append(f"⏱️ Время выполнения: {duration.total_seconds():.2f} сек")
            
            if 'total_size' in result:
                size_mb = result['total_size'] / (1024 * 1024)
                self.log_text.append(f"📊 Общий размер: {size_mb:.2f} МБ")
            
            # Открываем папку с результатами
            if 'output_folder' in result:
                import subprocess
                import platform
                folder = result['output_folder']
                try:
                    if platform.system() == "Windows":
                        subprocess.run(f'explorer "{folder}"', shell=True)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", str(folder)])
                    else:  # Linux
                        subprocess.run(["xdg-open", str(folder)])
                    self.log_text.append(f"📂 Папка с результатами открыта")
                except:
                    self.log_text.append(f"📂 Папка с результатами: {folder}")
            
            self.last_action_label.setText("✅ Конвертация завершена успешно!")
            
        else:
            if result.get('cancelled'):
                self.log_text.append("⛔ Конвертация отменена пользователем")
                self.last_action_label.setText("⛔ Конвертация отменена")
                return

            # Ошибка
            error_msg = result.get('error', 'Неизвестная ошибка')
            self.log_text.append(f"❌ Ошибка: {error_msg}")
            self.last_action_label.setText("❌ Конвертация завершилась с ошибкой")
            QMessageBox.critical(self, "Ошибка", f"Конвертация завершилась с ошибкой:\n{error_msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
