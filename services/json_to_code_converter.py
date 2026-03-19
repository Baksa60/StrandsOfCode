from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.base_reverse_converter import BaseReverseConverter


class JsonToCodeConverter(BaseReverseConverter):
    def parse_json_structure(self, content: str) -> Dict[str, str]:
        data = json.loads(content)

        if isinstance(data, dict) and isinstance(data.get("files"), list):
            structure: Dict[str, str] = {}
            for item in data["files"]:
                if not isinstance(item, dict):
                    continue
                path = item.get("path") or item.get("name")
                text = item.get("content")
                if isinstance(path, str) and isinstance(text, str):
                    structure[path] = text
            return structure

        if isinstance(data, dict) and isinstance(data.get("name"), str) and isinstance(data.get("content"), str):
            return {data["name"]: data["content"]}

        raise ValueError("Не удалось распознать структуру JSON")

    def convert_to_code(
        self,
        text_content: str,
        output_folder: Path,
        language: Optional[str] = None,
        file_structure: Optional[Dict[str, Any]] = None,
    ) -> dict:
        from datetime import datetime

        start_time = datetime.now()
        output_files: List[Path] = []

        output_folder.mkdir(parents=True, exist_ok=True)

        if not file_structure:
            file_structure = self.parse_json_structure(text_content)

        for file_name, content in file_structure.items():
            clean_content = self.clean_code_content(content)

            file_path = output_folder / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if not file_path.suffix and language:
                file_path = file_path.with_suffix(self._get_extension_for_language(language))

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(clean_content)

            output_files.append(file_path)

        return self.create_result(output_files, start_time)

    def _get_extension_for_language(self, language: str) -> str:
        extension_map = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
        }
        return extension_map.get((language or "").lower(), ".txt")
