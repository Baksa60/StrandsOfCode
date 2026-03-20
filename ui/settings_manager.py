import json
import logging
from pathlib import Path


class SettingsManager:
    SETTINGS_FILE = Path.home() / ".strands_of_code_settings.json"

    def load(self) -> dict:
        try:
            if self.SETTINGS_FILE.exists():
                with open(self.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            logging.warning(f"Ошибка загрузки настроек: {e}")

        return {}

    def save(self, settings: dict) -> None:
        try:
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.warning(f"Ошибка сохранения настроек: {e}")
