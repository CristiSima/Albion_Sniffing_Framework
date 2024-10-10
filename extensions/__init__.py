import os
from functools import partial
from importlib import import_module 
from pathlib import Path

current_dir = os.path.dirname(os.path.abspath(__file__))

def import_small_extension(filename: str):
    print(f"Importing [{filename}]: ...")
    import_module(f".{filename[:-3]}", package="extensions")

def import_extension(extension_path: Path):
    print(f"Importing [{filename}]: ...")
    import_module(f".{filename}", package="extensions")

for filename in (os.listdir(current_dir)):
    filepath = os.path.join(current_dir, filename)
    if os.path.isfile(filepath) and filename.endswith(".py") and filename != "__init__.py":
        import_small_extension(filename)
    elif os.path.isdir(filepath) and filename != "__pycache__":
        import_extension(filepath)
