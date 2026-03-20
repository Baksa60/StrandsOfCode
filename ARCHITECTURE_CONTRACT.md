# ARCHITECTURE_CONTRACT.md

## 1. Цель

Обеспечить единый и однозначный контракт для конвертера кода StrandsOfCode, чтобы перенос, интеграция и рефакторинг:

- не ломали существующие форматы конвертации;
- позволяли добавлять новые форматы и новые типы конвертеров;
- не приводили к ложной унификации;
- не размазывали ответственность между слоями.

Создать архитектуру, в которой:

- существует один владелец конвертации (ConversionEngine);
- форматы не управляют состоянием, файлами и жизненным циклом;
- добавление нового формата или нового типа конвертера не требует переписывания ядра;
- перенос формата означает удаление старой логики, а не её оборачивание.

⚠️ **Контракт требует полной унификации интерфейса, за исключением нижеперечисленного.**
- Иконки форматов в UI
- Названия форматов в выпадающих списках
- Специфичные настройки формата в диалогах
- Текст в статусах ошибок конвертации

Этот контракт является обязательным для всех изменений в проекте.

## 2. Архитектурные слои и их власть

### 2.1. ConversionEngine — ЯДРО

ConversionEngine — единственный владелец конвертации.

Он эксклюзивно управляет:

- состоянием конвертации;
- жизненным циклом (collect, convert, save, cancel);
- очередью файлов и прогрессом;
- историей конвертаций;
- валидацией форматов;
- генерацией и исполнением эффектов;
- статистикой, метаданными, сохранением.

❌ **Запрещено:**

- дублировать управление состоянием в конвертерах;
- иметь format-specific session hooks (usePythonSession, и т.п.).

Любой код, который принимает решение вне ConversionEngine, считается архитектурным дефектом.

### 2.2. FormatDefinition — ДОМЕН, НЕ ПРОЦЕСС

**FormatDefinition** — это чистое описание правил конвертации, а не сценариев исполнения.

**Он имеет право:**

- принимать доменную модель (файлы, опции);
- принимать действие пользователя (конвертировать, сохранить);
- возвращать новую модель;
- возвращать ConversionEffect[];
- сообщать результат валидации.

**Он НЕ имеет права:**

- хранить состояние PyQt;
- управлять историей;
- знать о PyQt, файловой системе, диалогах;
- знать о типе вывода (TXT, HTML, MD, JSON);
- вызывать сохранение, открытие диалогов;
- управлять жизненным циклом.

#### Контракт FormatDefinition
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ConversionOptions:
    source_format: str
    target_format: str
    include_metadata: bool = True
    line_numbers: bool = True
    syntax_highlight: bool = False
    combine_files: bool = False

@dataclass
class ConversionEffect:
    type: str  # 'save', 'error', 'progress', 'complete'
    data: Dict[str, Any]

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class FormatDefinition(ABC):
    @abstractmethod
    def validate_source(self, file_path: str) -> ValidationResult:
        """Проверяет, поддерживается ли исходный формат"""
        pass
    
    @abstractmethod
    def validate_target(self, options: ConversionOptions) -> ValidationResult:
        """Проверяет, поддерживается ли целевой формат"""
        pass
    
    @abstractmethod
    def convert(
        self, 
        source_files: List[str], 
        options: ConversionOptions
    ) -> {
        'result': str,
        'effects': List[ConversionEffect],
        'metadata': Dict[str, Any]
    }:
        """Выполняет конвертацию"""
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Возвращает поддерживаемые расширения"""
        pass
```

### 2.3. Effects — ТОЛЬКО ДЕКЛАРАТИВНЫЕ

**Форматы никогда не выполняют side-effects.**

Они только описывают намерения.

```python
type ConversionEffect =
  | { type: 'save_file'; path: str; content: str }
  | { type: 'progress'; current: int; total: int }
  | { type: 'error'; code: str; message: str }
  | { type: 'metadata'; data: Dict[str, Any] }
  | { type: 'complete'; stats: Dict[str, Any] }
```

✔ **Исполнение эффектов** — исключительная обязанность ConversionEngine.
❌ **Любой прямой вызов** file_manager, dialog_manager, progress_bar из формата — запрещён.

### 2.4. File Collector — ЕДИНЫЙ И ЦЕНТРАЛИЗОВАННЫЙ

**Сбор файлов:**

- управляется только UnifiedFileCollector;
- имеет общую логику фильтрации;
- сериализуется централизованно;
- одинаков по UX независимо от типа формата.

**Формат:**

- не считает файлы;
- не хранит пути;
- не фильтрует по расширениям.

❌ **Любой собственный FileCollector** внутри формата — подлежит удалению.

### 2.5. Persistence — ИНФРАСТРУКТУРА

**Сохранение и загрузка:**

- реализуются вне формата;
- не содержат доменной логики;
- работают со snapshot'ом, предоставленным ConversionEngine.

```python
@dataclass
class ConversionSnapshot:
    conversion_id: str
    source_files: List[str]
    target_format: str
    options: ConversionOptions
    result: Optional[str]
    metadata: Dict[str, Any]
    status: str  # 'pending', 'running', 'completed', 'failed'
    created_at: str
    completed_at: Optional[str]
```

### 2.6. UI / Presentation — ФОРМАТ СЛЕП, UI — СПЕЦИАЛИЗИРОВАННЫЙ

**UI** — визуальный адаптер, а не универсальный бог-объект.

**Он:**

- визуализирует прогресс;
- транслирует пользовательский ввод в доменные действия;
- выбирается по типу формата, а не по конвертеру.

**Формат:**

- не знает, что используется PyQt;
- не знает, что есть диалоги;
- не знает, как именно рисуется его прогресс;
- не знает, как именно сохраняется результат.

#### Гибридная архитектура UI (ОБЯЗАТЕЛЬНО)

**Многоуровневая абстракция:**

```
FormatLogic
   ↓
FormatUIAdapter
   ↓
(UIEngine interface)
   ↓
PyQt*UI
```

**Text UI (текстовые форматы)**
- `TextUIEngine<TState, TOptions>` — базовый интерфейс
- `SimpleTextUI<TState, TOptions>` — базовый TXT
- `MarkdownUI<TState, TOptions>` — Markdown с подсветкой
- `JSONUI<TState, TOptions>` — структурированный JSON

**Code UI (языки программирования)**
- `CodeUIEngine<TState, TOptions>` — базовый интерфейс
- `PythonUI<TState, TOptions>` — Python специфичный
- `JavaScriptUI<TState, TOptions>` — JS/TS специфичный

⚠️ **CodeUIEngine НЕ наследуется от TextUIEngine**
Это принципиально разные миры.

#### Адаптерная модель (ОБЯЗАТЕЛЬНО)

Каждый формат НЕ работает напрямую с PyQt:

```
PythonUIAdapter → CodeUIEngine
TXTUIAdapter → SimpleTextUI
HTMLUIAdapter → MarkdownUI
JSONUIAdapter → JSONUI
```

#### Фабрика UI (ОБЯЗАТЕЛЬНО)

`UIEngineFactory`:
- знает PyQt;
- не знает конкретные форматы;
- выбирается по типу формата, а не по названию конвертера;
- предоставляет предустановленные конфигурации для форматов.

#### Типы форматов (обязательное разделение)

**Text-based converters**
- текстовые файлы
- простая конвертация, метаданные
- примеры: TXT, Markdown, JSON

**Code-based converters**
- языки программирования
- синтаксический анализ, подсветка
- примеры: Python, JavaScript, TypeScript

❌ **Code-converter НЕ обязан и НЕ должен подчиняться** text-контракту.

**Why full unification is intentionally impossible:**

1. **Разная семантика:** Text — строковая обработка, Code — синтаксический анализ
2. **Разная структура:** Text — плоский текст, Code — древовидная структура
3. **Разная логика подсветки:** Text — нет, Code — синтаксическая подсветка
4. **Разная валидация:** Text — кодировка, Code — синтаксис
5. **Разные метаданные:** Text — базовые, Code — функции, классы, импорты

Попытка полной унификации приведет к:
- потере семантики форматов;
- усложнению кода ради абстракции;
- невозможности добавлять новые типы форматов.

**UIInput:**
- source_files
- options
- progress

**UIOutput:**
- доменные действия (ConversionOptions)

❌ **Любое упоминание** PyQt, QWidget, QDialog, QVBoxLayout в FormatDefinition или format logic — нарушение контракта.

### 2.7. MainWindow — ЕДИНЫЙ ИНТЕРФЕЙС

**MainWindow** — унифицированный компонент для всех форматов.

**Обязательный шаблон использования:**
```python
class MainWindow(QMainWindow):
    def __init__(self):
        self.conversion_engine = ConversionEngine()
        self.ui_factory = UIEngineFactory()
        self.setup_ui()
    
    def setup_ui(self):
        # Единая структура для всех форматов
        self.source_selector = SourceSelector()
        self.format_selector = FormatSelector()
        self.options_panel = OptionsPanel()
        self.conversion_button = ConversionButton()
        self.progress_bar = ProgressBar()
```

**Правила:**
- `format_selector` — всегда использует единый список форматов
- `options_panel` — всегда адаптируется под выбранный формат
- **Запрещено:** создавать специфичные UI для каждого формата
- **Запрещено:** дублировать логику выбора формата

**Цель:** устранить двусмысленность при добавлении новых форматов и обеспечить предсказуемость.

### 2.8. Error Handling — ЕДИНЫЙ СТАНДАРТ

**Все ошибки должны использовать централизованную систему обработки.**

**Обязательное правило:**
- Любая ошибка должна проходить через `ErrorHandler`
- **Запрещено:** хардкодить сообщения об ошибках в конвертерах
- **Запрещено:** использовать `raise Exception` без обработки
- **Обязательно:** добавлять коды ошибок в `ERROR_CODES`

**Исключения (допускается прямой raise):**
- Критические системные ошибки
- Ошибки импорта модулей
- Отсутствие файлов

**Пример правильного использования:**
```python
# ❌ Плохо - нарушает контракт
raise Exception("Failed to convert file")

# ✅ Хорошо - соответствует контракту
return ConversionEffect(
    type='error',
    data={'code': 'CONVERSION_FAILED', 'message': 'Failed to convert file'}
)
```

**Цель:** обеспечить централизованную обработку ошибок и избежать хаоса в сообщениях.

## 3. Прямо запрещено

**Агент НЕ ИМЕЕТ ПРАВА:**

- создавать use<Format>Session;
- создавать orchestrator'ы поверх ConversionEngine;
- дублировать логику ConversionEngine;
- делать «универсальный конвертер для всех форматов»;
- сохранять старые API «на всякий случай»;
- оборачивать старый код без удаления оригинала;
- добавлять абстракции, не забирающие ответственность;
- хардкодить сообщения об ошибках (исключая системные).

## 4. Критерии приёмки (ОТК)

**Работа считается принятой ТОЛЬКО ЕСЛИ:**

- количество строк кода уменьшилось;
- исчезли дублирующие системы;
- у формата нет собственного состояния;
- ConversionEngine — единственный управляющий слой;
- эффекты только декларативные;
- FileCollector — один;
- UI изолирован от домена;
- тип формата выбран явно;
- старый код удалён, а не закомментирован.

**Работа отклоняется**, даже если «всё работает», но нарушен контракт.

## 5. Статус контракта

**Этот документ — единственный источник правды.**

Любое отклонение требует явного согласования.

**Архитектурная «гибкость»** без согласования считается ошибкой.

## 6. Археология

**legacy/:**

- не изменяется;
- не рефакторится;
- используется только как справочник поведения.

**Копировать поведение** — допустимо.
**Копировать код** — запрещено.

## Финальная ремарка (для агентов)

**Архитектура — не про «чтобы всем было удобно».**
Архитектура — это распределение власти, границ и ответственности.

**Унификация ради унификации** — форма технического самообмана.
