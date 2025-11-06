from pathlib import Path

def ensure_not_root(path):
    clean_path = str(path).strip('"').strip("'")
    resolved_path = Path(path).resolve()
    if str(resolved_path).endswith("/..") or str(resolved_path).endswith("\\.."):
        raise PermissionError("Запрещено работать с родительскими каталогами")
    if resolved_path == Path("/"):
        raise PermissionError("Запрещено работать с корневым каталогом")

def ensure_exists(path):
    if not Path(path).exists():
        raise FileNotFoundError(f"Путь {path} не существует")

def ensure_is_dir(path):
    if not Path(path).is_dir():
        raise NotADirectoryError(f"Объект {path} не является каталогом")

def ensure_is_file(path):
    if not Path(path).is_file():
        raise IsADirectoryError(f"Объект {path} не является файлом")