from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from utils.cancellation import check_cancelled
from utils.file_utils import read_file_safe


class JsonConverterService:
    def convert_to_json(
        self,
        files: List[Path],
        output_folder: Path,
        add_headers: bool = True,
        add_line_numbers: bool = True,
        create_tree: bool = False,
        base_folder: Optional[Path] = None,
        filename: Optional[str] = None,
        progress_callback=None,
    ) -> dict:
        output_folder.mkdir(parents=True, exist_ok=True)

        start_time = datetime.now()
        results = {
            'total_files': len(files),
            'converted_files': 0,
            'failed_files': [],
            'output_files': [],
            'total_size': 0,
            'start_time': start_time,
            'errors': [],
        }

        if create_tree:
            combined = self._create_combined_json(files, output_folder, base_folder, filename)
            results['combined_file'] = combined
            results['output_files'].append(combined['output_path'])
            results['converted_files'] = len(files)
            results['total_size'] = combined['size']
            results['end_time'] = datetime.now()
            results['duration'] = results['end_time'] - results['start_time']
            return results

        for i, file_path in enumerate(files, 1):
            check_cancelled()
            
            # Отправляем прогресс
            if progress_callback:
                progress_callback(i, len(files))
            
            try:
                content, _ = read_file_safe(file_path)
                payload = {
                    'format': 'strands_of_code.file.json.v1',
                    'name': file_path.name,
                    'path': str(file_path),
                    'extension': file_path.suffix,
                    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'content': content,
                }

                out_path = output_folder / f"{file_path.stem}.json"
                with open(out_path, 'w', encoding='utf-8') as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)

                results['converted_files'] += 1
                results['output_files'].append(out_path)
                results['total_size'] += out_path.stat().st_size
            except Exception as e:
                results['failed_files'].append(str(file_path))
                results['errors'].append(f"Ошибка конвертации {file_path}: {e}")

        results['end_time'] = datetime.now()
        results['duration'] = results['end_time'] - results['start_time']
        return results

    def _create_combined_json(
        self,
        files: List[Path],
        output_folder: Path,
        base_folder: Optional[Path],
        filename: Optional[str],
    ) -> dict:
        check_cancelled()

        if filename:
            output_path = output_folder / filename
        else:
            output_path = output_folder / 'combined_code.json'

        if output_path.suffix.lower() != '.json':
            output_path = output_path.with_suffix('.json')

        files_payload = []
        for file_path in sorted(files):
            check_cancelled()
            content, _ = read_file_safe(file_path)

            rel_path = None
            if base_folder:
                try:
                    rel_path = str(file_path.relative_to(base_folder))
                except Exception:
                    rel_path = str(file_path.name)
            else:
                rel_path = str(file_path.name)

            files_payload.append(
                {
                    'path': rel_path,
                    'name': file_path.name,
                    'extension': file_path.suffix,
                    'content': content,
                }
            )

        payload = {
            'format': 'strands_of_code.json.v1',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_files': len(files_payload),
            'files': files_payload,
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return {
            'output_path': output_path,
            'size': output_path.stat().st_size,
            'total_files': len(files_payload),
        }
