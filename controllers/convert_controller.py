from services.file_collector import FileCollector
from services.converter_service import ConverterService
from services.markdown_converter_service import MarkdownConverterService
from config import DEFAULT_COMBINED_FILENAME

class ConvertController:

    def __init__(self):
        self.collector = FileCollector()
        self.converter = ConverterService()
        self.markdown_converter = MarkdownConverterService()

    def run(self, options):

        if options.source_type == "file":
            files = self.collector.collect_from_file(options.paths[0])

        elif options.source_type == "files":
            files = self.collector.collect_from_files(options.paths)

        elif options.source_type == "folder":
            files = self.collector.collect_from_folder(
                options.paths[0],
                options.extensions
            )

        elif options.source_type == "folder_recursive":
            files = self.collector.collect_from_folder_recursive(
                options.paths[0],
                options.extensions
            )

        elif options.source_type == "python_project":

            folder = options.paths[0]

            if not self.collector.detect_python_project(folder) and not self.collector.detect_js_project(folder):
                raise ValueError("Project markers not found (Python or JavaScript/TypeScript)")

            # Определяем тип проекта и используем соответствующий метод
            if self.collector.detect_python_project(folder):
                files = self.collector.collect_python_project(
                    folder,
                    options.extensions
                )
            else:
                files = self.collector.collect_js_project(
                    folder,
                    options.extensions
                )

        else:
            raise ValueError("Unknown source type")

        if options.output_format == "markdown":
            # Конвертация в Markdown
            if options.source_type == "python_project":
                base_folder = options.paths[0]
            elif options.source_type in ["folder", "folder_recursive"]:
                base_folder = options.paths[0]
            else:
                # Для файлов используем папку первого файла
                base_folder = options.paths[0].parent if options.paths else None
            
            result = self.markdown_converter.convert_to_markdown(
                files,
                options.output_folder,
                options.add_headers,
                True,  # Всегда добавляем нумерацию строк в Markdown
                True,  # Всегда создаем дерево в Markdown
                base_folder
            )
            
        elif options.output_mode == "separate":

            result = self.converter.convert_to_separate_txt(
                files,
                options.output_folder,
                options.add_headers
            )

        elif options.output_mode == "combined":

            output_file = options.output_folder / DEFAULT_COMBINED_FILENAME

            # Определяем базовую папку для дерева
            if options.source_type == "python_project":
                base_folder = options.paths[0]
            elif options.source_type in ["folder", "folder_recursive"]:
                base_folder = options.paths[0]
            else:
                # Для файлов используем папку первого файла
                base_folder = options.paths[0].parent if options.paths else None

            result = self.converter.convert_to_single_txt(
                files,
                output_file,
                options.add_headers,
                base_folder
            )
        return result
