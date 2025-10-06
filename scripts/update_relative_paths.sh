#!/usr/bin/env python3
import os
import re

# Root folder containing 'app'
ROOT_DIR = "."
APP_FOLDER_NAME = "app"

# Regex to match imports from app or its submodules
IMPORT_REGEX = re.compile(r'^(from\s+)app(\..*)\s+(import\s+.*)$')

def get_relative_prefix(file_path):
    """
    Calculate the relative import prefix based on how deep the file is from the app folder.
    """
    abs_file_path = os.path.abspath(file_path)
    parts = abs_file_path.split(os.sep)
    try:
        app_index = parts.index(APP_FOLDER_NAME)
    except ValueError:
        # File is not inside the app folder
        return None

    # Number of directories to go up from current file to reach app
    depth = len(parts) - (app_index + 2)  # +1 for filename, +1 because we want parent of app
    if depth <= 0:
        return "."
    return "." * (depth + 1)  # +1 because single dot counts as same folder

def convert_imports(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    changed = False
    new_lines = []

    for line in lines:
        match = IMPORT_REGEX.match(line)
        if match:
            from_part, module_path, import_part = match.groups()
            prefix = get_relative_prefix(file_path)
            if prefix is None:
                new_lines.append(line)
                continue
            # Remove leading dot from module_path since prefix already handles depth
            module_path_clean = module_path[1:] if module_path.startswith(".") else module_path
            new_line = f"{from_part}{prefix}{module_path_clean} {import_part}\n"
            new_lines.append(new_line)
            changed = True
        else:
            new_lines.append(line)

    if changed:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"Updated imports in {file_path}")

def main():
    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                convert_imports(file_path)

if __name__ == "__main__":
    main()
