"""
Утилиты для построения дерева проекта
"""

from pathlib import Path
from typing import List
from collections import defaultdict


def build_project_tree(files: List[Path], base_folder: Path) -> str:
    """
    Строит текстовое дерево проекта с правильной структурой папок.
    
    Args:
        files: Список файлов для включения в дерево
        base_folder: Базовая папка проекта
        
    Returns:
        Строка с текстовым представлением дерева проекта
    """
    # Группируем файлы по папкам
    folder_structure = defaultdict(list)
    
    for file in files:
        try:
            relative = file.relative_to(base_folder)
        except ValueError:
            relative = file
        
        if len(relative.parts) == 1:
            # Файл в корневой папке
            folder_structure[""].append(relative)
        else:
            # Файл в подпапке
            folder_path = str(relative.parent)
            folder_structure[folder_path].append(relative)
    
    tree = []
    root_name = base_folder.name
    
    tree.append("PROJECT STRUCTURE\n")
    tree.append(f"{root_name}/")
    
    # Сортируем папки и файлы
    sorted_folders = sorted(folder_structure.keys())
    
    for folder in sorted_folders:
        if folder == "":
            # Файлы в корневой папке
            for file in sorted(folder_structure[folder], key=lambda x: x.name):
                tree.append(f" └ {file.name}")
        else:
            # Показываем структуру папок
            parts = folder.split('/')
            depth = 0
            current_path = ""
            
            for part in parts:
                if depth == 0:
                    tree.append(f" ├─ {part}/")
                else:
                    indent = " │   " * depth
                    tree.append(f"{indent} ├─ {part}/")
                depth += 1
            
            # Файлы в этой папке
            for file in sorted(folder_structure[folder], key=lambda x: x.name):
                indent = " │   " * depth
                tree.append(f"{indent} └ {file.name}")
    
    tree.append("\n" + "=" * 40 + "\n")
    tree.append("SOURCE CODE\n")
    tree.append("=" * 40 + "\n")
    
    return "\n".join(tree)
