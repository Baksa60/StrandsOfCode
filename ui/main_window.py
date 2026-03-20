import sys
import subprocess
import platform

from pathlib import Path

from datetime import datetime

from PyQt6.QtWidgets import (

    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,

    QGroupBox, QLabel, QPushButton, QComboBox, QRadioButton, QButtonGroup,

    QTextEdit, QProgressBar, QFileDialog, QMessageBox, QCheckBox,

    QSplitter, QGridLayout, QLineEdit

)

from PyQt6.QtCore import Qt, QSize, QMimeData

from PyQt6.QtGui import QIcon, QFont, QPalette, QDragEnterEvent, QDropEvent, QPainter, QColor

from controllers.convert_controller import ConvertController

from models.conversion_options import ConversionOptions

from ui.styles import apply_theme
from ui.history_dialog import HistoryDialog

from utils.cancellation import ConversionCancelled

from version import get_app_info, get_version_string

from ui.conversion_worker import ConversionWorker
from ui.settings_manager import SettingsManager
from ui.history_manager import HistoryManager





class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.controller = ConvertController()

        self.settings_manager = SettingsManager()
        self.history_manager = HistoryManager()

        self.selected_paths = []

        self.recent_files = []  # Список недавних файлов

        self.last_save_folder = None  # Последнее место сохранения

        self.is_drag_active = False  # Состояние drag & drop

        self.worker = None

        self.init_ui()

        self.load_settings()  # Загружаем сохраненные настройки
        self.load_history()   # Загружаем историю конвертаций

        

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

        main_layout.addLayout(self._build_header())

        # Создаем сплиттер для разделения 70/30
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())

        splitter.setSizes([700, 300])  # 70% левая, 30% правая
        splitter.setStretchFactor(0, 7)  # 70% левая панель
        splitter.setStretchFactor(1, 3)  # 30% правая панель

        main_layout.addWidget(splitter)


    def _build_header(self) -> QHBoxLayout:

        # Заголовок приложения с переключателем тем
        header_layout = QHBoxLayout()

        title_label = QLabel("🧬 StrandsOfCode")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Кнопка "О программе"
        about_button = QPushButton("ℹ️ О программе")
        about_button.setMinimumWidth(130)
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

        return header_layout


    def _build_left_panel(self) -> QWidget:

        # Левая панель - настройки
        left_panel = QWidget()

        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)

        # Группа выбора источника
        source_group = QGroupBox("📁 Источник файлов")
        source_layout = QVBoxLayout()
        source_layout.setSpacing(10)

        # Тип и формат в одной строке
        source_header_layout = QHBoxLayout()

        # Выбор типа источника слева
        source_header_layout.addWidget(QLabel("📋 Тип:"))

        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems([
            "📄 Один файл",
            "📁 Несколько файлов",
            "📂 Папка",
            "📂 Папка (рекурсивно)"
        ])
        self.source_type_combo.currentTextChanged.connect(self.on_source_type_changed)
        self.source_type_combo.setMaximumWidth(200)
        source_header_layout.addWidget(self.source_type_combo)

        # Растягивающееся пространство посередине
        source_header_layout.addStretch()

        # Выбор формата исходных файлов справа
        source_header_layout.addWidget(QLabel("📥 Формат ИЗ:"))

        self.source_format_combo = QComboBox()
        self.source_format_combo.addItems([
            "🧩 Все поддерживаемые",
            "🐍 Python (.py)",
            "🟨 JavaScript (.js)",
            "🔷 TypeScript (.ts)",
            "📄 Текст (.txt)",
            "📝 Markdown (.md)",
            "🌐 HTML (.html)",
            "🧾 JSON (.json)"
        ])
        self.source_format_combo.currentTextChanged.connect(self.on_source_format_changed)
        self.source_format_combo.setMaximumWidth(180)
        source_header_layout.addWidget(self.source_format_combo)

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

        source_layout.addLayout(source_header_layout)
        source_layout.addLayout(select_layout)

        source_group.setLayout(source_layout)
        left_layout.addWidget(source_group)

        # Группа информации о выбранных файлах
        info_group = QGroupBox("📊 Информация о выбранных файлах")
        info_layout = QVBoxLayout()

        self.files_count_label = QLabel("🔧 Файлов: 0")
        self.folders_count_label = QLabel("📁 Папок: 0")
        self.size_count_label = QLabel("📏 Размер: 0 KB")

        info_layout.addWidget(self.files_count_label)
        info_layout.addWidget(self.folders_count_label)
        info_layout.addWidget(self.size_count_label)

        info_group.setLayout(info_layout)
        left_layout.addWidget(info_group)

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
            "🧾 JSON (.json)",
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
        left_layout.addWidget(output_group)

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

        left_layout.addWidget(self.convert_button)
        left_layout.addWidget(self.cancel_button)
        left_layout.addStretch()

        return left_panel


    def _build_right_panel(self) -> QWidget:

        # Правая панель - лог и история
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

        # Кнопка истории конвертаций
        self.history_button = QPushButton("📜 История")
        self.history_button.clicked.connect(self.show_conversion_history)
        clear_log_layout.addWidget(self.history_button)

        clear_log_layout.addStretch()
        log_layout.addLayout(clear_log_layout)

        log_group.setLayout(log_layout)

        right_layout.addWidget(progress_group)
        right_layout.addWidget(log_group)

        return right_panel

    
    def log_action(self, action: str):
        """Добавляет сообщение о действии в лог"""
        self.log_message(f"⏰ {action}")

    def log_message(self, message: str):
        """Добавляет сообщение в лог с авто-прокруткой"""
        self.log_text.append(message)
        # Авто-прокрутка к последнему сообщению
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def load_settings(self):

        """Загружает сохраненные настройки"""

        settings = self.settings_manager.load()

        self.last_save_folder = settings.get('last_save_folder')

        if self.last_save_folder:
            self.save_path_edit.setText(self.last_save_folder)

        recent_files_data = settings.get('recent_files', [])
        self.recent_files = [Path(path) for path in recent_files_data]

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

    

    def save_settings(self):
        """Сохраняет настройки"""
        self.settings_manager.save({
            'last_save_folder': self.save_path_edit.text(),
            'last_source_type': self.source_type_combo.currentText(),
            'last_source_format': self.source_format_combo.currentText(),
            'last_output_format': self.output_format_combo.currentText(),
            'recent_files': [str(path) for path in self.recent_files]
        })

    def browse_save_location(self):
        """Открывает диалог выбора папки сохранения"""

        

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

    # Новая функция для проверки наличия сохраненной папки
    def check_save_folder(self):
        if not self.save_path_edit.text():
            QMessageBox.warning(self, "Внимание", "Сначала выберите папку для сохранения")
            return False
        return True

    def generate_filename(self):
        """Генерирует уникальное имя файла"""
        if not self.save_path_edit.text():
            QMessageBox.warning(self, "Внимание", "Сначала выберите папку для сохранения")
            return

        output_format = self._determine_output_format(self.output_format_combo.currentText())
        source_label = self.history_manager.get_current_source_format(self.source_format_combo.currentText())
        target_label = output_format.upper()
        ext = self._determine_extension(output_format)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{source_label}_to_{target_label}_{timestamp}"
        self.filename_edit.setText(self.get_unique_filename(base_name, ext))

        

        
    

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
        self.log_action("Лог очищен")

    

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

        folder_extensions = set()  # Собираем расширения файлов в папках

        

        for path in paths:

            if path.is_file():

                files.append(path)

            elif path.is_dir():

                folders.append(path)

                # Анализируем содержимое папки

                folder_extensions.update(self._get_folder_extensions(path))

        

        # Определяем основной формат файлов

        main_format = self._detect_main_format(files, folders, folder_extensions)

        

        # Автоматически выбираем тип источника

        if folders and not files:

            # Только папки - проверяем на вложенность

            if len(folders) == 1:

                if self._has_nested_folders(folders[0]):

                    self.source_type_combo.setCurrentText("📂 Папка (рекурсивно)")

                else:

                    self.source_type_combo.setCurrentText("📂 Папка")

            else:

                # Несколько папок - всегда рекурсивно

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

        

        # Устанавливаем правильный формат исходных файлов

        self._set_source_format(main_format)

        

        # Обновляем статистику

        self.update_statistics()

        

        # Обновляем последнее действие

        self.log_action(f"Перетащено {len(paths)} элементов")

        

        # Включаем кнопку конвертации

        self.convert_button.setEnabled(True)
        
        
    

    def _get_folder_extensions(self, folder_path: Path) -> set:

        """Собирает все расширения файлов в папке рекурсивно"""

        extensions = set()

        try:

            for file_path in folder_path.rglob('*'):

                if file_path.is_file():

                    ext = file_path.suffix.lower()

                    if ext:

                        extensions.add(ext)

        except Exception:

            pass

        return extensions

    

    def _detect_main_format(self, files: list[Path], folders: list[Path], folder_extensions: set) -> str:

        """Определяет основной формат файлов по доминированию"""

        all_extensions = set()

        

        # Добавляем расширения прямых файлов

        for file_path in files:

            ext = file_path.suffix.lower()

            if ext:

                all_extensions.add(ext)

        

        # Добавляем расширения из папок

        all_extensions.update(folder_extensions)

        

        # Определяем основной формат

        if not all_extensions:

            return "🧩 Все поддерживаемые"

        

        # Считаем реальное количество файлов каждого расширения

        ext_counts = {}

        total_files = 0

        

        # Считаем прямые файлы

        for file_path in files:

            ext = file_path.suffix.lower()

            if ext:

                ext_counts[ext] = ext_counts.get(ext, 0) + 1

                total_files += 1

        

        # Считаем файлы в папках (правильный подсчет)

        for folder_path in folders:

            for file_path in folder_path.rglob('*'):

                if file_path.is_file():

                    ext = file_path.suffix.lower()

                    if ext:

                        ext_counts[ext] = ext_counts.get(ext, 0) + 1

                        total_files += 1

        

        if not ext_counts:

            return "🧩 Все поддерживаемые"

        

        # Находим самый доминирующий формат

        dominant_ext = None

        max_count = 0

        

        for ext, count in ext_counts.items():

            if count > max_count:

                max_count = count

                dominant_ext = ext

        

        # Если доминирующий формат составляет >25% от всех файлов, выбираем его

        if dominant_ext and max_count > 0 and total_files > 0:

            dominance_ratio = max_count / total_files

            if dominance_ratio > 0.25:  # Более 25% файлов

                return self._extension_to_format(dominant_ext)

        

        # Если нет доминирующего формата, используем приоритеты

        priority_order = ['.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.html', '.md', '.txt']

        for ext in priority_order:

            if ext in all_extensions:

                return self._extension_to_format(ext)

        

        return "🧩 Все поддерживаемые"

    

    def _extension_to_format(self, ext: str) -> str:

        """Преобразует расширение в формат для комбобокса"""

        format_map = {

            '.py': '🐍 Python (.py)',

            '.js': '🟨 JavaScript (.js)',

            '.jsx': '🟨 JavaScript (.js)',

            '.ts': '🔷 TypeScript (.ts)',

            '.tsx': '🔷 TypeScript (.ts)',

            '.txt': '📄 Текст (.txt)',

            '.md': '📝 Markdown (.md)',

            '.html': '🌐 HTML (.html)',

            '.json': '🧾 JSON (.json)'

        }

        return format_map.get(ext.lower(), '🧩 Все поддерживаемые')

    

    def _has_nested_folders(self, folder_path: Path) -> bool:

        """Проверяет есть ли в папке вложенные папки"""

        try:

            for item in folder_path.iterdir():

                if item.is_dir():

                    return True

        except Exception:

            pass

        return False

    

    def _set_source_format(self, format_text: str):

        """Устанавливает формат исходных файлов"""

        # Ищем формат в комбобоксе

        for i in range(self.source_format_combo.count()):

            if format_text in self.source_format_combo.itemText(i):

                self.source_format_combo.setCurrentIndex(i)

                return

    

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

            ("Текст" in source_format_text or "Markdown" in source_format_text or "HTML" in source_format_text or "JSON" in source_format_text)

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

        if "JSON" in format_text:

            return [".json"]

        return []

    

    def show_about(self):

        """Показывает окно 'О программе'"""

        # Получаем информацию о приложении

        app_info = get_app_info()

        version = get_version_string()

        

        about_text = f"""

        <h2>🧬 {app_info['name']}</h2>

        <p><b>Версия:</b> {version}</p>

        <p><b>Дата сборки:</b> {app_info['build_date']}</p>

        <p><b>Автор:</b> {app_info['author']}</p>

        <p><b>Email:</b> {app_info['email']}</p>

        <p><b>Лицензия:</b> {app_info['license']}</p>

        <p><b>{app_info['description']}</b></p>

        <br>

        

        <p><b>🔄 Поддерживаемые форматы:</b></p>

        <p><i>Двунаправленная конвертация между всеми форматами:</i></p>

        <ul>

            <li>🐍 <b>Python</b> (.py)</li>

            <li>🟨 <b>JavaScript</b> (.js, .jsx)</li>

            <li>🔷 <b>TypeScript</b> (.ts, .tsx)</li>

            <li>🌐 <b>HTML</b> (.html)</li>

            <li>📝 <b>Markdown</b> (.md)</li>

            <li>📄 <b>JSON</b> (.json)</li>

            <li>📄 <b>Текст</b> (.txt)</li>

        </ul>

        <p><i>Всего 49 комбинаций конвертации (7 × 7)</i></p>

        <br>

        

        <p><b>🚀 Ключевые возможности:</b></p>

        <ul>

            <li>� <b>Drag & Drop</b> - перетаскивание файлов и папок</li>

            <li>🧠 <b>Умное определение формата</b> (90-95% точность)</li>

            <li>💾 <b>Умная система сохранения</b></li>

            <li>🎨 <b>Современный UI</b> с темами</li>

        </ul>

        <br>

        

        <p><i>{app_info['copyright']}</i></p>

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

                self.log_action("Выбран файл")
                
                
                

        elif "Несколько файлов" in source_type:

            file_paths, _ = QFileDialog.getOpenFileNames(

                self, "Выберите файлы", "", file_filter

            )

            if file_paths:

                self.selected_paths = [Path(p) for p in file_paths]

                self.selected_label.setText(f'Выбрано {len(file_paths)} файлов')

                self.convert_button.setEnabled(True)

                self.update_statistics()

                self.log_action("Выбрано несколько файлов")
                
                
                

        elif "Папка" in source_type:

            folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку")

            if folder_path:

                self.selected_paths = [Path(folder_path)]

                self.selected_label.setText(folder_path)

                self.convert_button.setEnabled(True)

                self.update_statistics()

                self.log_action("Выбрана папка")
                
                
        

        # Обновляем последнее действие

        self.log_action("Выбраны файлы/папки")

    

    def _get_file_filter(self, format_text):

        """Возвращает фильтр файлов в зависимости от формата"""

        if "Все поддерживаемые" in format_text:

            return "Supported files (*.py *.js *.jsx *.ts *.tsx *.txt *.md *.html *.json);;All files (*)"

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

        elif "JSON" in format_text:

            return "JSON files (*.json);;All files (*)"

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

                    if file_path.is_file() and file_path.suffix in [".py", ".js", ".ts", ".tsx", ".jsx", ".json"]:

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

    

    
        

    def start_conversion(self):

        if not self._validate_before_conversion():
            return

        options = self._build_conversion_options()
        if not options:
            return

        self.save_settings()
        self._start_worker(options)


    def _validate_before_conversion(self) -> bool:

        if not self.selected_paths:
            QMessageBox.warning(self, "Внимание", "Сначала выберите источник файлов")
            return False

        if not self.save_path_edit.text():
            QMessageBox.warning(self, "Внимание", "Сначала выберите папку для сохранения")
            return False

        return True


    def _determine_source_type(self, source_type_text: str) -> str:

        if "Один файл" in source_type_text:
            return "file"
        if "Несколько файлов" in source_type_text:
            return "files"
        if "Папка (рекурсивно)" in source_type_text:
            return "folder_recursive"
        return "folder"


    def _determine_output_format(self, output_format_text: str) -> str:

        if "Текст" in output_format_text:
            return "txt"
        if "Markdown" in output_format_text:
            return "markdown"
        if "HTML" in output_format_text:
            return "html"
        if "JSON" in output_format_text:
            return "json"
        if "Python" in output_format_text:
            return "python"
        if "JavaScript" in output_format_text:
            return "javascript"
        if "TypeScript" in output_format_text:
            return "typescript"
        return "txt"


    def _determine_output_mode(self, output_mode_text: str) -> str:

        return "separate" if "Отдельные" in output_mode_text else "combined"


    def _determine_extension(self, output_format: str) -> str:

        if output_format == "txt":
            return ".txt"
        if output_format == "markdown":
            return ".md"
        if output_format == "html":
            return ".html"
        if output_format == "json":
            return ".json"
        if output_format == "python":
            return ".py"
        if output_format == "javascript":
            return ".js"
        if output_format == "typescript":
            return ".ts"
        return ".txt"


    def _build_conversion_options(self):

        source_format = self.source_format_combo.currentText()
        output_format_text = self.output_format_combo.currentText()

        source_type = self._determine_source_type(self.source_type_combo.currentText())
        output_format = self._determine_output_format(output_format_text)
        output_mode = self._determine_output_mode(self.output_mode_combo.currentText())

        base_folder = Path(self.save_path_edit.text())
        filename_base = self.filename_edit.text().strip()
        ext = self._determine_extension(output_format)

        source_stem = None
        if source_type == "file" and self.selected_paths:
            try:
                source_stem = Path(self.selected_paths[0]).stem
            except Exception:
                source_stem = None

        if output_mode == "combined" and source_type != "file" and not filename_base:
            QMessageBox.warning(self, "Внимание", "Для режима 'В один файл' при нескольких файлах/папке нужно ввести имя файла")
            return None

        options_filename = None

        if output_mode == "combined":
            final_filename_base = filename_base or (source_stem or "combined")
            final_filename_base = self.get_unique_filename(final_filename_base, ext)
            options_filename = final_filename_base + ext
        else:
            if source_type == "file":
                final_filename_base = filename_base or (source_stem or "output")
                final_filename_base = self.get_unique_filename(final_filename_base, ext)
                options_filename = final_filename_base + ext
            else:
                options_filename = None

        output_folder = base_folder

        self.log_message(f"📂 Папка сохранения: {base_folder}")
        if options_filename:
            self.log_message(f"📝 Имя файла: {options_filename}")
            self.log_message(f"📂 Полный путь: {base_folder / options_filename}")
        self.log_message("🔄 Начинаю конвертацию...")

        try:
            base_folder.mkdir(parents=True, exist_ok=True)
            self.log_message(f"✅ Папка доступна: {base_folder}")
        except Exception as e:
            self.log_message(f"❌ Ошибка доступа к папке: {e}")
            return None

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

        self.log_message(f"🔍 Тип источника: {source_type}")
        self.log_message(f"📁 Пути: {self.selected_paths}")
        self.log_message(f"📤 Формат вывода: {output_format}")
        self.log_message(f"📂 Папка вывода: {output_folder}")

        return options


    def _start_worker(self, options: ConversionOptions):

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

            self.log_message("⛔ Запрошена отмена...")

            self.worker.requestInterruption()

            self.cancel_button.setEnabled(False)

        

    def on_conversion_finished(self, result):
        """Обрабатывает завершение конвертации"""
        self.progress_bar.setVisible(False)
        self.convert_button.setEnabled(True)
        self.cancel_button.setVisible(False)
        self.cancel_button.setEnabled(False)
        
        # Добавляем запись в историю
        self._save_conversion_to_history(result)

        if result.get('success', True):

            # Успешная конвертация

            if 'combined_file' in result:

                output_file = result['combined_file']['output_path']

                self.log_message(f"✅ Готово! Файл сохранен: {output_file}")

            elif 'output_files' in result and result['output_files']:

                files = result['output_files']

                self.log_message(f"✅ Готово! Сохранено файлов: {len(files)}")

                for file_path in files[:5]:  # Показываем первые 5 файлов

                    self.log_message(f"📄 {file_path}")

                if len(files) > 5:

                    self.log_message(f"... и еще {len(files) - 5} файлов")

            

            # Статистика

            if 'duration' in result:

                duration = result['duration']

                self.log_message(f"⏱️ Время выполнения: {duration.total_seconds():.2f} сек")

            

            if 'total_size' in result:

                size_mb = result['total_size'] / (1024 * 1024)

                self.log_message(f"📊 Общий размер: {size_mb:.2f} МБ")

            

            # Открываем папку с результатами

            if 'output_folder' in result:

                folder = result['output_folder']

                try:

                    if platform.system() == "Windows":

                        subprocess.run(f'explorer "{folder}"', shell=True)

                    elif platform.system() == "Darwin":  # macOS

                        subprocess.run(["open", str(folder)])

                    else:  # Linux

                        subprocess.run(["xdg-open", str(folder)])

                    self.log_message(f"📂 Папка с результатами открыта")

                except:

                    self.log_message(f"📂 Папка с результатами: {folder}")

            

            self.log_action("Конвертация завершена успешно!")

            

        else:

            if result.get('cancelled'):

                self.log_message("⛔ Конвертация отменена пользователем")
                self.log_action("Конвертация отменена")

                return



            # Ошибка

            error_msg = result.get('error', 'Неизвестная ошибка')

            self.log_message(f"❌ Ошибка: {error_msg}")
            self.log_action("Конвертация завершилась с ошибкой")

            QMessageBox.critical(self, "Ошибка", f"Конвертация завершилась с ошибкой:\n{error_msg}")

    def show_conversion_history(self):
        """Показывает историю конвертаций"""
        dialog = HistoryDialog(self)
        dialog.history_data = self.history_manager.history
        dialog.update_table()
        dialog.update_statistics()
        dialog.exec()

    def load_history(self):
        """Загружает историю конвертаций из файла"""
        self.history_manager.load()

    def add_conversion_to_history(self, conversion_data):
        """Добавляет запись о конвертации в историю"""
        self.history_manager.add_entry(conversion_data)

    def save_history(self):
        """Сохраняет историю конвертаций в файл"""
        self.history_manager.save()

    def _save_conversion_to_history(self, result):
        """Сохраняет результат конвертации в историю"""
        self.history_manager.save_conversion_result(
            result=result,
            selected_paths=self.selected_paths,
            source_format_text=self.source_format_combo.currentText(),
            output_format_text=self.output_format_combo.currentText(),
        )

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainWindow()

    window.show()

    sys.exit(app.exec())

