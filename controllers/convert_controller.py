from services.file_collector import FileCollector

from services.converter_service import ConverterService

from services.markdown_converter_service import MarkdownConverterService

from services.html_converter_service import HtmlConverterService

from services.txt_to_code_converter import TxtToCodeConverter

from services.markdown_to_code_converter import MarkdownToCodeConverter

from services.html_to_code_converter import HtmlToCodeConverter

from services.code_to_code_converter import CodeToCodeConverter

from services.text_to_text_converter import TextToTextConverter

from services.json_converter_service import JsonConverterService

from services.json_to_code_converter import JsonToCodeConverter

from config import DEFAULT_COMBINED_FILENAME

from pathlib import Path

from typing import Optional, List

from models.conversion_result import ConversionResult

from utils.file_utils import read_file_safe

from utils.file_utils import ensure_unique_filename

import os



class ConvertController:



    def __init__(self):

        self.collector = FileCollector()

        self.converter = ConverterService()

        self.markdown_converter = MarkdownConverterService()

        self.html_converter = HtmlConverterService()

        self.json_converter = JsonConverterService()

        self.txt_reverse_converter = TxtToCodeConverter()

        self.markdown_reverse_converter = MarkdownToCodeConverter()

        self.html_reverse_converter = HtmlToCodeConverter()

        self.json_reverse_converter = JsonToCodeConverter()

        self.code_converter = CodeToCodeConverter()

        self.text_converter = TextToTextConverter()



    def run(self, options):

        # Определяем тип конвертации по форматам

        source_format = self._detect_source_format_from_options(options)

        

        # Текст → Код

        if source_format in ["txt", "markdown", "html", "json"] and options.output_format in ["python", "javascript", "typescript"]:

            result = self._run_text_to_code_conversion(options)

            normalized = self._normalize_dict_result(result, options)

            return self._postprocess_single_file_output(normalized, options)

        

        # Код → Код

        elif source_format in ["python", "javascript", "typescript"] and options.output_format in ["python", "javascript", "typescript"]:

            result = self._run_code_to_code_conversion(options)

            normalized = self._normalize_dict_result(result, options)

            return self._postprocess_single_file_output(normalized, options)

        

        # Текст → Текст

        elif source_format in ["txt", "markdown", "html", "json"] and options.output_format in ["txt", "markdown", "html", "json"]:

            result = self._run_text_to_text_conversion(options)

            normalized = self._normalize_dict_result(result, options)

            return self._postprocess_single_file_output(normalized, options)

        

        # Код → Текст (существующая логика)

        else:

            result = self._run_forward_conversion(options)

            normalized = self._normalize_dict_result(result, options)

            return self._postprocess_single_file_output(normalized, options)



    def _postprocess_single_file_output(self, result: dict, options) -> dict:

        try:

            if getattr(options, 'source_type', None) != 'file':

                return result

            if getattr(options, 'output_mode', None) != 'separate':

                return result

            if not getattr(options, 'filename', None):

                return result



            output_files = result.get('output_files')

            if not output_files or len(output_files) != 1:

                return result



            src_path = Path(output_files[0])

            if not src_path.exists():

                return result



            desired = Path(options.output_folder) / options.filename

            if desired.suffix.lower() != src_path.suffix.lower():

                desired = desired.with_suffix(src_path.suffix)

            desired = ensure_unique_filename(desired)



            if src_path.resolve() != desired.resolve():

                desired.parent.mkdir(parents=True, exist_ok=True)

                os.replace(src_path, desired)

                result['output_files'] = [desired]

                if 'combined_file' in result and isinstance(result['combined_file'], dict):

                    result['combined_file']['output_path'] = desired



        except Exception as e:

            result.setdefault('errors', [])

            result['errors'].append(f"Ошибка переименования выходного файла: {e}")



        return result

    

    def _detect_source_format(self, file_path: Optional[Path]) -> str:

        """Определяет формат исходного файла"""

        if not file_path:

            return "txt"

        

        extension = file_path.suffix.lower()

        

        if extension == '.py':

            return "python"

        elif extension in ['.js', '.jsx']:

            return "javascript"

        elif extension in ['.ts', '.tsx']:

            return "typescript"

        elif extension == '.md':

            return "markdown"

        elif extension == '.html':

            return "html"

        elif extension == '.json':

            return "json"

        else:

            return "txt"



    def _detect_source_format_from_options(self, options) -> str:

        """Определяет формат источника из options.



        Важно: для папок/проектов/нескольких файлов нельзя надёжно определять формат по suffix у пути,

        поэтому используем options.extensions (выбранный формат ИЗ в UI).

        """



        # Для одиночного файла suffix надёжен

        if getattr(options, 'source_type', None) == 'file':

            return self._detect_source_format(options.paths[0] if options.paths else None)



        # Для нескольких файлов пробуем определить по первому файлу (если он файл)

        if getattr(options, 'source_type', None) == 'files':

            if options.paths and options.paths[0].is_file():

                return self._detect_source_format(options.paths[0])



        # Для папок/проектов и мульти-режима ориентируемся на выбранные расширения

        extensions = getattr(options, 'extensions', None) or []

        exts = set(e.lower() for e in extensions)



        if exts & {'.py'}:

            return 'python'

        if exts & {'.js', '.jsx'}:

            return 'javascript'

        if exts & {'.ts', '.tsx'}:

            return 'typescript'

        if exts & {'.md'}:

            return 'markdown'

        if exts & {'.html'}:

            return 'html'

        if exts & {'.json'}:

            return 'json'

        if exts & {'.txt'}:

            return 'txt'



        # Если extensions пустые ("все поддерживаемые"), определяем по фактическим файлам

        try:

            files = self._collect_files(options)

            for p in files:

                fmt = self._detect_source_format(p)

                if fmt != 'txt':

                    return fmt

        except Exception:

            pass



        return 'txt'

    

    def _run_text_to_code_conversion(self, options):

        """Запускает конвертацию текста в код"""

        return self._run_reverse_conversion(options)

    

    def _run_code_to_code_conversion(self, options):

        """Запускает конвертацию кода в код"""

        # Собираем файлы

        files = self._collect_files(options)

        

        # Определяем исходный язык

        source_format = self._detect_source_format_from_options(options)

        

        return self.code_converter.convert_code(

            files,

            options.output_folder,

            source_format,

            options.output_format,

            options.output_mode,

            options.filename

        )

    

    def _run_text_to_text_conversion(self, options):

        """Запускает конвертацию текста в текст"""

        # Собираем файлы

        files = self._collect_files(options)

        

        # Определяем исходный формат

        source_format = self._detect_source_format_from_options(options)

        

        return self.text_converter.convert_text(

            files,

            options.output_folder,

            source_format,

            options.output_format,

            options.output_mode,

            options.filename

        )

    

    def _collect_files(self, options):

        """Собирает файлы по опциям с умной фильтрацией"""

        try:

            if options.source_type == "file":

                return self.collector.collect_from_file(options.paths[0])

            elif options.source_type == "files":

                return self.collector.collect_from_files(options.paths)

            elif options.source_type == "folder":

                return self._collect_from_folder_smart(options.paths[0], options.extensions)

            elif options.source_type == "folder_recursive":

                return self._collect_from_folder_recursive_smart(options.paths[0], options.extensions)

            elif options.source_type == "python_project":

                folder = options.paths[0]

                if not self.collector.detect_python_project(folder) and not self.collector.detect_js_project(folder):

                    raise ValueError("Project markers not found (Python or JavaScript/TypeScript)")

                return self.collector.collect_project_files(folder, options.extensions)

            else:

                raise ValueError("Unknown source type")

        except Exception as e:

            raise ValueError(f"Error collecting files: {str(e)}")

    

    def _collect_from_folder_smart(self, folder_path: Path, extensions: List[str]) -> List[Path]:

        """Умный сбор файлов из папки.

        Если extensions не заданы, используем все поддерживаемые форматы (мульти-режим).

        """

        all_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.txt', '.md', '.html', '.json']

        effective_extensions = extensions or all_extensions

        return self.collector.collect_from_folder(folder_path, effective_extensions)

    

    def _collect_from_folder_recursive_smart(self, folder_path: Path, extensions: List[str]) -> List[Path]:

        """Умный рекурсивный сбор файлов из папки.

        Если extensions не заданы, используем все поддерживаемые форматы (мульти-режим).

        """

        all_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.txt', '.md', '.html']

        effective_extensions = extensions or all_extensions

        return self.collector.collect_from_folder_recursive(folder_path, effective_extensions)

    

    def _run_forward_conversion(self, options):

        """

        Запускает прямую конвертацию (код → текст)

        """

        # Собираем файлы

        files = self._collect_files(options)

        

        # Определяем базовую папку для дерева/относительных путей

        if options.source_type == "python_project":

            base_folder = options.paths[0]

        elif options.source_type in ["folder", "folder_recursive"]:

            base_folder = options.paths[0]

        else:

            base_folder = options.paths[0].parent if options.paths else None



        # Для Markdown/HTML используем специализированные сервисы

        if options.output_format == "markdown":

            create_tree = options.output_mode == "combined"

            return self.markdown_converter.convert_to_markdown(

                files,

                options.output_folder,

                add_headers=options.add_headers,

                add_line_numbers=options.add_line_numbers,

                create_tree=create_tree,

                base_folder=base_folder if create_tree else None,

                filename=options.filename if create_tree else None,

            )



        if options.output_format == "json":

            create_tree = options.output_mode == "combined"

            return self.json_converter.convert_to_json(

                files,

                options.output_folder,

                add_headers=options.add_headers,

                add_line_numbers=options.add_line_numbers,

                create_tree=create_tree,

                base_folder=base_folder if create_tree else None,

                filename=options.filename if create_tree else None,

            )



        if options.output_format == "html":

            create_tree = options.output_mode == "combined"

            return self.html_converter.convert_to_html(

                files,

                options.output_folder,

                add_headers=options.add_headers,

                add_line_numbers=options.add_line_numbers,

                create_tree=create_tree,

                base_folder=base_folder if create_tree else None,

                filename=options.filename if create_tree else None,

            )



        # TXT (существующая логика)

        if options.output_mode == "separate":

            result = self.converter.convert_to_separate_txt(

                files, 

                options.output_folder, 

                options.add_headers,

                options.add_line_numbers,

            )

        else:

            # Используем имя файла из опций

            output_file = options.output_folder / (options.filename or DEFAULT_COMBINED_FILENAME)

            

            result = self.converter.convert_to_single_txt(

                files, 

                output_file, 

                options.add_headers,

                options.add_line_numbers,

                base_folder=base_folder,

            )

        

        if isinstance(result, ConversionResult):

            return self._normalize_conversion_result(result, options)



        return result



    def _normalize_conversion_result(self, result: ConversionResult, options) -> dict:

        normalized = {

            'total_files': result.files_found,

            'converted_files': result.files_converted,

            'failed_files': [str(p) for p in result.skipped_files],

            'output_files': result.created_files,

            'errors': result.errors,

        }



        if options.output_mode == 'combined' and result.created_files:

            normalized['combined_file'] = {'output_path': result.created_files[0]}



        return normalized



    def _normalize_dict_result(self, result, options=None) -> dict:

        if isinstance(result, ConversionResult):

            if options is None:

                raise ValueError("Internal error: options is required to normalize ConversionResult")

            return self._normalize_conversion_result(result, options)



        if not isinstance(result, dict):

            return {

                'data': result,

                'total_files': 0,

                'converted_files': 0,

                'failed_files': [],

                'output_files': [],

                'errors': [],

            }



        # Гарантируем наличие ключей, чтобы UI не падал от KeyError

        result.setdefault('total_files', result.get('files_found', 0))

        result.setdefault('converted_files', result.get('files_converted', 0))

        result.setdefault('failed_files', [])

        result.setdefault('output_files', [])

        result.setdefault('errors', [])



        return result

    

    def _run_reverse_conversion(self, options):

        """

        Запускает обратную конвертацию (текст → код)

        """

        if getattr(options, 'output_mode', None) != 'separate':

            options.output_mode = 'separate'



        # Читаем входной файл

        input_file = options.paths[0]



        if not input_file.is_file():

            raise ValueError(

                "Обратная конвертация (текст → код) поддерживает только один входной файл. "

                "Выберите 'Один файл' и укажите .txt/.md/.html/.json файл."

            )



        try:

            content, _ = read_file_safe(input_file)

        except UnicodeDecodeError:

            raise ValueError(f"Не удалось прочитать файл {input_file}")

        

        # Выбираем конвертер

        if input_file.suffix.lower() == '.txt':

            converter = self.txt_reverse_converter

            # Пробуем извлечь структуру из TXT

            file_structure = converter.parse_txt_structure(content)

        elif input_file.suffix.lower() == '.md':

            converter = self.markdown_reverse_converter

            # Пробуем извлечь структуру из Markdown

            file_structure = converter.parse_markdown_structure(content)

        elif input_file.suffix.lower() == '.html':

            converter = self.html_reverse_converter

            # Пробуем извлечь структуру из HTML

            file_structure = converter.parse_html_structure(content)

        elif input_file.suffix.lower() == '.json':

            converter = self.json_reverse_converter

            file_structure = converter.parse_json_structure(content)

        else:

            raise ValueError(f"Неподдерживаемый формат файла: {input_file.suffix}")

        

        # Запускаем конвертацию

        return converter.convert_to_code(

            content,

            options.output_folder,

            options.output_format,  # Язык для восстановления

            file_structure

        )

