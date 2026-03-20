import json
import logging
from datetime import datetime
from pathlib import Path


class HistoryManager:
    HISTORY_FILE = Path.home() / ".strands_of_code_history.json"

    def __init__(self):
        self.history: list = []

    def load(self) -> list:
        try:
            if self.HISTORY_FILE.exists():
                with open(self.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and isinstance(item.get("timestamp"), str):
                            try:
                                item["timestamp"] = datetime.fromisoformat(item["timestamp"])
                            except Exception:
                                item["timestamp"] = datetime.now()
                    self.history = data
        except json.JSONDecodeError as e:
            logging.warning(f"Ошибка парсинга истории: {e}")
            self.history = []
        except Exception as e:
            logging.warning(f"Ошибка загрузки истории: {e}")
            self.history = []

        return self.history

    def save(self) -> None:
        try:
            serializable_history = []
            for item in self.history:
                if not isinstance(item, dict):
                    continue

                serializable_item = item.copy()
                if isinstance(serializable_item.get("timestamp"), datetime):
                    serializable_item["timestamp"] = serializable_item["timestamp"].isoformat()

                if hasattr(serializable_item.get("duration"), 'total_seconds'):
                    serializable_item["duration"] = serializable_item["duration"].total_seconds()

                serializable_history.append(serializable_item)

            with open(self.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(serializable_history, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logging.warning(f"Ошибка сохранения истории: {e}")

    def add_entry(self, conversion_data: dict) -> None:
        history_item = {
            "timestamp": datetime.now(),
            "source": str(conversion_data.get("source_paths", [""])[0]),
            "source_format": conversion_data.get("source_format", "Unknown"),
            "output_format": conversion_data.get("output_format", "Unknown"),
            "status": conversion_data.get("status", "unknown"),
            "duration": conversion_data.get("duration", 0),
            "size": conversion_data.get("total_size", 0),
            "files_count": conversion_data.get("files_count", 0),
            "error": conversion_data.get("error", "")
        }

        self.history.append(history_item)

        if len(self.history) > 100:
            self.history = self.history[-100:]

        self.save()

    def get_current_source_format(self, format_text: str) -> str:
        if "Python" in format_text:
            return "Python"
        elif "JavaScript" in format_text:
            return "JavaScript"
        elif "TypeScript" in format_text:
            return "TypeScript"
        elif "Текст" in format_text:
            return "TXT"
        elif "Markdown" in format_text:
            return "Markdown"
        elif "HTML" in format_text:
            return "HTML"
        elif "JSON" in format_text:
            return "JSON"
        else:
            return "Unknown"

    def save_conversion_result(self, result: dict, selected_paths: list, source_format_text: str, output_format_text: str) -> None:
        if result.get('cancelled'):
            status = 'cancelled'
        elif result.get('success', True):
            status = 'success'
        else:
            status = 'failed'

        total_size = result.get('total_size', 0)
        duration = result.get('duration')

        if total_size == 0:
            if 'output_files' in result:
                try:
                    total_size = sum(Path(f).stat().st_size for f in result['output_files'] if Path(f).exists())
                except Exception:
                    total_size = 0
            elif 'combined_file' in result and 'output_path' in result['combined_file']:
                try:
                    total_size = Path(result['combined_file']['output_path']).stat().st_size
                except Exception:
                    total_size = 0

        conversion_data = {
            "source_paths": selected_paths,
            "source_format": self.get_current_source_format(source_format_text),
            "output_format": output_format_text,
            "status": status,
            "duration": duration,
            "total_size": total_size,
            "files_count": result.get('total_files', 0),
            "error": result.get('error', '')
        }

        self.add_entry(conversion_data)
