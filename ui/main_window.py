import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QCheckBox, QGroupBox,
    QRadioButton, QButtonGroup, QProgressBar, QTextEdit,
    QFileDialog, QMessageBox, QSplitter, QFrame, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QPalette
from controllers.convert_controller import ConvertController
from models.conversion_options import ConversionOptions
from ui.styles import apply_theme


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
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(e)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = ConvertController()
        self.selected_paths = []
        self.recent_files = []  # Список недавних файлов
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("🔧 py2txt_tool - Конвертер кода в TXT")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(800, 600)
        
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
        title_label = QLabel("🔧 py2txt_tool")
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
        
        # Радио кнопки в сетке для лучшей организации
        radio_grid = QGridLayout()
        
        self.source_button_group = QButtonGroup()
        self.radio_file = QRadioButton("📄 Один файл")
        self.radio_files = QRadioButton("📁 Несколько файлов")
        self.radio_folder = QRadioButton("📂 Папка (без вложенных)")
        self.radio_folder_recursive = QRadioButton("📂 Папка (рекурсивно)")
        self.radio_python_project = QRadioButton("🚀 Программный проект")
        
        self.source_button_group.addButton(self.radio_file, 0)
        self.source_button_group.addButton(self.radio_files, 1)
        self.source_button_group.addButton(self.radio_folder, 2)
        self.source_button_group.addButton(self.radio_folder_recursive, 3)
        self.source_button_group.addButton(self.radio_python_project, 4)
        
        self.radio_file.setChecked(True)
        
        radio_grid.addWidget(self.radio_file, 0, 0)
        radio_grid.addWidget(self.radio_files, 0, 1)
        radio_grid.addWidget(self.radio_folder, 1, 0)
        radio_grid.addWidget(self.radio_folder_recursive, 1, 1)
        radio_grid.addWidget(self.radio_python_project, 2, 0)
        
        source_layout.addLayout(radio_grid)
        
        # Кнопка выбора файлов/папок
        select_layout = QHBoxLayout()
        self.select_button = QPushButton("📂 Выбрать файл")
        self.select_button.clicked.connect(self.select_source)
        self.selected_label = QLabel("Ничего не выбрано")
        self.selected_label.setObjectName("selectedLabel")
        self.selected_label.setWordWrap(True)
        
        select_layout.addWidget(self.select_button)
        select_layout.addWidget(self.selected_label, 1)
        
        source_layout.addLayout(select_layout)
        source_group.setLayout(source_layout)
        
        # Группа настроек вывода
        output_group = QGroupBox("⚙️ Настройки вывода")
        output_layout = QVBoxLayout()
        output_layout.setSpacing(12)
        
        # Режим вывода
        output_mode_layout = QHBoxLayout()
        output_mode_layout.addWidget(QLabel("📋 Режим:"))
        self.output_mode_combo = QComboBox()
        self.output_mode_combo.addItems(["📄 Отдельные файлы", "📄 Объединенный файл"])
        output_mode_layout.addWidget(self.output_mode_combo)
        output_mode_layout.addStretch()
        
        output_layout.addLayout(output_mode_layout)
        
        # Настройки
        self.add_headers_checkbox = QCheckBox("📝 Добавлять заголовки и метаданные")
        self.add_headers_checkbox.setChecked(True)
        output_layout.addWidget(self.add_headers_checkbox)
        
        output_group.setLayout(output_layout)
        
        # Кнопка запуска
        self.convert_button = QPushButton("🚀 Конвертировать")
        self.convert_button.setObjectName("convertButton")
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setEnabled(False)
        self.convert_button.setMinimumHeight(50)
        
        left_layout.addWidget(source_group)
        left_layout.addWidget(output_group)
        left_layout.addWidget(self.convert_button)
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
        log_group.setLayout(log_layout)
        
        right_layout.addWidget(progress_group)
        right_layout.addWidget(log_group)
        
        # Добавляем панели в сплиттер
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)
        
        # Обновление текста кнопки выбора
        self.source_button_group.buttonClicked.connect(self.update_select_button_text)
        
    def update_select_button_text(self):
        button_id = self.source_button_group.checkedId()
        texts = {
            0: "📂 Выбрать файл",
            1: "📂 Выбрать файлы",
            2: "📂 Выбрать папку",
            3: "📂 Выбрать папку",
            4: "📂 Выбрать папку проекта"
        }
        self.select_button.setText(texts.get(button_id, "Выбрать"))
        
    def change_theme(self, theme_text):
        """Изменяет тему приложения"""
        if "Темная" in theme_text:
            apply_theme(QApplication.instance(), "dark")
        else:
            apply_theme(QApplication.instance(), "light")
    
    def show_about(self):
        """Показывает окно 'О программе'"""
        about_text = """
        <h2>🔧 py2txt_tool</h2>
        <p><b>Версия:</b> 1.1.0</p>
        <p><b>Конвертер файлов кода в текстовый формат</b></p>
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
        <p><i>Разработано с ❤️ для удобной работы с кодом</i></p>
        """
        
        QMessageBox.about(self, "О программе", about_text)
        
    def select_source(self):
        button_id = self.source_button_group.checkedId()
        
        if button_id == 0:  # Один файл
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Выберите файл кода", "", 
                "Code files (*.py *.js *.ts *.tsx *.jsx);;Python files (*.py);;JavaScript files (*.js *.jsx);;TypeScript files (*.ts *.tsx);;All files (*)"
            )
            if file_path:
                self.selected_paths = [Path(file_path)]
                self.selected_label.setText(file_path)
                
        elif button_id == 1:  # Несколько файлов
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "Выберите файлы кода", "", 
                "Code files (*.py *.js *.ts *.tsx *.jsx);;Python files (*.py);;JavaScript files (*.js *.jsx);;TypeScript files (*.ts *.tsx);;All files (*)"
            )
            if file_paths:
                self.selected_paths = [Path(p) for p in file_paths]
                self.selected_label.setText(f"Выбрано {len(file_paths)} файлов")
                
        elif button_id in [2, 3, 4]:  # Папки
            folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку")
            if folder_path:
                self.selected_paths = [Path(folder_path)]
                self.selected_label.setText(folder_path)
        
        self.convert_button.setEnabled(bool(self.selected_paths))
        
        # Обновляем статистику
        self.update_statistics()
        
        # Добавляем в недавние файлы
        for path in self.selected_paths:
            self.add_recent_file(path)
        
        # Обновляем последнее действие
        self.last_action_label.setText("⏰ Последнее действие: Выбраны файлы/папки")
        
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
            
        # Получение настроек
        source_type_map = {
            0: "file",
            1: "files", 
            2: "folder",
            3: "folder_recursive",
            4: "python_project"
        }
        source_type = source_type_map[self.source_button_group.checkedId()]
        
        output_mode = "separate" if self.output_mode_combo.currentIndex() == 0 else "combined"
        
        # Выбор папки для сохранения
        output_folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if not output_folder:
            return
            
        # Создание опций
        options = ConversionOptions(
            source_type=source_type,
            paths=self.selected_paths,
            output_mode=output_mode,
            output_folder=Path(output_folder),
            extensions=[".py", ".js", ".ts", ".tsx", ".jsx"],
            add_headers=self.add_headers_checkbox.isChecked()
        )
        
        # Запуск конвертации в отдельном потоке
        self.convert_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.log_text.clear()
        self.log_text.append("Начинаю конвертацию...")
        
        self.worker = ConversionWorker(self.controller, options)
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.start()
        
    def on_conversion_finished(self, result):
        self.progress_bar.setVisible(False)
        self.convert_button.setEnabled(True)
        
        if isinstance(result, Exception):
            self.log_text.append(f"Ошибка: {str(result)}")
            self.last_action_label.setText("⏰ Последнее действие: Ошибка конвертации")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(result)}")
        else:
            if result.success():
                self.log_text.append(f"Успешно! Сконвертировано: {result.files_converted} файлов")
                if result.created_files:
                    files_text = "\n".join(str(f) for f in result.created_files)
                    self.log_text.append(f"Созданные файлы:\n{files_text}")
                self.last_action_label.setText("⏰ Последнее действие: Конвертация завершена")
                QMessageBox.information(self, "Готово", f"Конвертация завершена успешно!\nОбработано файлов: {result.files_converted}")
            else:
                self.log_text.append("Конвертация завершена с ошибками")
                if result.errors:
                    errors_text = "\n".join(result.errors)
                    self.log_text.append(f"Ошибки:\n{errors_text}")
                self.last_action_label.setText("⏰ Последнее действие: Конвертация с ошибками")
                QMessageBox.warning(self, "Предупреждение", "Конвертация завершена с ошибками. Проверьте лог.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
