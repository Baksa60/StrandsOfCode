DEFAULT_EXTENSIONS = [".py", ".js", ".ts", ".tsx", ".jsx"]

DEFAULT_COMBINED_FILENAME = "combined_code.txt"

# признаки Python-проекта
PROJECT_MARKERS = [
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "Pipfile"
]

# признаки JavaScript/TypeScript-проекта
JS_PROJECT_MARKERS = [
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "tsconfig.json",
    "webpack.config.js",
    "vite.config.js",
    "rollup.config.js"
]

# папки которые не нужно сканировать
IGNORED_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".idea",
    ".vscode",
    "build",
    "dist"
}

# маска игнорирования файлов
IGNORE_PATTERNS = [
    "*_test.py",
    "test_*.py",
    "__init__.py",
    "*.test.js",
    "*.test.ts",
    "*.spec.js",
    "*.spec.ts",
    "*.min.js",
    "*.d.ts"
]
