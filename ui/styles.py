"""
Современные стили для py2txt_tool
"""

# Светлая тема
LIGHT_THEME = """
/* Главное окно */
QMainWindow {
    background-color: #f5f5f5;
}

/* Центральный виджет */
QWidget {
    background-color: #ffffff;
    color: #2c3e50;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 9pt;
}

/* Группы */
QGroupBox {
    font-weight: 600;
    color: #34495e;
    border: 2px solid #e1e8ed;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px 0 8px;
    color: #3498db;
    font-weight: 700;
}

/* Кнопки */
QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 9pt;
    min-height: 16px;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #21618c;
}

QPushButton:disabled {
    background-color: #bdc3c7;
    color: #7f8c8d;
}

/* Основная кнопка конвертации */
QPushButton#convertButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #27ae60, stop:1 #229954);
    font-size: 11pt;
    padding: 12px 24px;
    min-height: 20px;
}

QPushButton#convertButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #229954, stop:1 #1e8449);
}

QPushButton#convertButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #1e8449, stop:1 #196f3d);
}

/* Радио кнопки */
QRadioButton {
    color: #2c3e50;
    font-size: 9pt;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #bdc3c7;
    background-color: white;
}

QRadioButton::indicator:hover {
    border: 2px solid #3498db;
}

QRadioButton::indicator:checked {
    border: 2px solid #3498db;
    background-color: #3498db;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iNSIgY3k9IjUiIHI9IjMiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo=);
}

/* Чекбоксы */
QCheckBox {
    color: #2c3e50;
    font-size: 9pt;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #bdc3c7;
    background-color: white;
}

QCheckBox::indicator:hover {
    border: 2px solid #3498db;
}

QCheckBox::indicator:checked {
    border: 2px solid #27ae60;
    background-color: #27ae60;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
}

/* Комбобоксы */
QComboBox {
    background-color: white;
    border: 2px solid #e1e8ed;
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 16px;
    color: #2c3e50;
}

QComboBox:hover {
    border: 2px solid #3498db;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNiA2TDExIDEiIHN0cm9rZT0iIzJjM2U1MCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+Cg==);
}

QComboBox QAbstractItemView {
    background-color: white;
    border: 2px solid #e1e8ed;
    border-radius: 6px;
    selection-background-color: #3498db;
    selection-color: white;
    padding: 4px;
}

/* Прогресс бар */
QProgressBar {
    border: none;
    border-radius: 8px;
    text-align: center;
    color: white;
    font-weight: 600;
    background-color: #ecf0f1;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #3498db, stop:1 #2980b9);
    border-radius: 8px;
}

/* Текстовые поля */
QTextEdit {
    background-color: #f8f9fa;
    border: 2px solid #e1e8ed;
    border-radius: 6px;
    padding: 8px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 8pt;
    color: #2c3e50;
}

QTextEdit:focus {
    border: 2px solid #3498db;
}

/* Метки */
QLabel {
    color: #2c3e50;
    font-size: 9pt;
}

QLabel#selectedLabel {
    background-color: #f8f9fa;
    border: 1px solid #e1e8ed;
    border-radius: 4px;
    padding: 6px 8px;
    color: #7f8c8d;
    font-style: italic;
}

QLabel#titleLabel {
    color: #2c3e50;
    font-size: 12pt;
    font-weight: 700;
    margin-bottom: 8px;
}

QLabel#sectionLabel {
    color: #7f8c8d;
    font-size: 8pt;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

/* Скроллбары */
QScrollBar:vertical {
    border: none;
    background: #f8f9fa;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background: #bdc3c7;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #95a5a6;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

# Темная тема
DARK_THEME = """
/* Главное окно */
QMainWindow {
    background-color: #1a1a1a;
}

/* Центральный виджет */
QWidget {
    background-color: #2d2d2d;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 9pt;
}

/* Группы */
QGroupBox {
    font-weight: 600;
    color: #e0e0e0;
    border: 2px solid #404040;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    background-color: #2d2d2d;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px 0 8px;
    color: #4fc3f7;
    font-weight: 700;
}

/* Кнопки */
QPushButton {
    background-color: #4fc3f7;
    color: #1a1a1a;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 9pt;
    min-height: 16px;
}

QPushButton:hover {
    background-color: #29b6f6;
}

QPushButton:pressed {
    background-color: #03a9f4;
}

QPushButton:disabled {
    background-color: #555555;
    color: #888888;
}

/* Основная кнопка конвертации */
QPushButton#convertButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #66bb6a, stop:1 #4caf50);
    font-size: 11pt;
    padding: 12px 24px;
    min-height: 20px;
    color: white;
}

QPushButton#convertButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #4caf50, stop:1 #43a047);
}

QPushButton#convertButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                               stop:0 #43a047, stop:1 #388e3c);
}

/* Радио кнопки */
QRadioButton {
    color: #e0e0e0;
    font-size: 9pt;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #555555;
    background-color: #2d2d2d;
}

QRadioButton::indicator:hover {
    border: 2px solid #4fc3f7;
}

QRadioButton::indicator:checked {
    border: 2px solid #4fc3f7;
    background-color: #4fc3f7;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iNSIgY3k9IjUiIHI9IjMiIGZpbGw9IiMxYTFhMWEiLz4KPC9zdmc+Cg==);
}

/* Чекбоксы */
QCheckBox {
    color: #e0e0e0;
    font-size: 9pt;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #555555;
    background-color: #2d2d2d;
}

QCheckBox::indicator:hover {
    border: 2px solid #4fc3f7;
}

QCheckBox::indicator:checked {
    border: 2px solid #66bb6a;
    background-color: #66bb6a;
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0iIzFkMWQxZCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+Cg==);
}

/* Комбобоксы */
QComboBox {
    background-color: #404040;
    border: 2px solid #555555;
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 16px;
    color: #e0e0e0;
}

QComboBox:hover {
    border: 2px solid #4fc3f7;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNiA2TDExIDEiIHN0cm9rZT0iI2UwZTBlMCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+Cg==);
}

QComboBox QAbstractItemView {
    background-color: #404040;
    border: 2px solid #555555;
    border-radius: 6px;
    selection-background-color: #4fc3f7;
    selection-color: #1a1a1a;
    padding: 4px;
}

/* Прогресс бар */
QProgressBar {
    border: none;
    border-radius: 8px;
    text-align: center;
    color: white;
    font-weight: 600;
    background-color: #404040;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #4fc3f7, stop:1 #29b6f6);
    border-radius: 8px;
}

/* Текстовые поля */
QTextEdit {
    background-color: #1a1a1a;
    border: 2px solid #555555;
    border-radius: 6px;
    padding: 8px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 8pt;
    color: #e0e0e0;
}

QTextEdit:focus {
    border: 2px solid #4fc3f7;
}

/* Метки */
QLabel {
    color: #e0e0e0;
    font-size: 9pt;
}

QLabel#selectedLabel {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 8px;
    color: #888888;
    font-style: italic;
}

QLabel#titleLabel {
    color: #e0e0e0;
    font-size: 12pt;
    font-weight: 700;
    margin-bottom: 8px;
}

QLabel#sectionLabel {
    color: #888888;
    font-size: 8pt;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

/* Скроллбары */
QScrollBar:vertical {
    border: none;
    background: #404040;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background: #555555;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #666666;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


def apply_theme(app, theme="light"):
    """Применяет тему к приложению"""
    if theme == "dark":
        app.setStyleSheet(DARK_THEME)
    else:
        app.setStyleSheet(LIGHT_THEME)
