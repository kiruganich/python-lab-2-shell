import re
from pathlib import Path
from ..logger import setup_logger

logger = setup_logger()

class GrepCommand:
    
    def __init__(self):
        pass
    
    def grep(self, args):
        if len(args) < 2:
            print("Использование: grep <pattern> <path> [-r] [-i]")
            return False
        
        pattern = args[0]
        path = args[1]
        recursive = "-r" in args
        ignore_case = "-i" in args
        
        try:
            flags = re.IGNORECASE if ignore_case else 0
            regex = re.compile(pattern, flags)
            
            target_path = Path(path).resolve()
            
            if target_path.is_file():
                return self._search_in_file(target_path, regex)
            
            if target_path.is_dir():
                return self._search_in_directory(target_path, regex, recursive)
            
            print(f"Ошибка: {target_path} не является файлом или директорией")
            return False
            
        except re.error as e:
            print(f"Ошибка в регулярном выражении: {e}")
            logger.error(f"grep {pattern} {path} ERROR: ошибка в регулярном выражении - {e}")
            return False
        except Exception as e:
            print(f"Ошибка: {e}")
            logger.error(f"grep {pattern} {path} {'-r' if recursive else ''} {'-i' if ignore_case else ''} ERROR: {e}")
            return False
    
    def _search_in_file(self, file_path, regex):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            found = False
            for i, line in enumerate(lines, 1):
                if regex.search(line):
                    found = True
                    print(f"{file_path}:{i}:{line.strip()}")
            
            return found
                
        except Exception as e:
            print(f"Не удалось прочитать файл {file_path}: {e}")
            return False
    
    def _search_in_directory(self, dir_path, regex, recursive):
        found_any = False
        
        try:
            for item in dir_path.iterdir():
                if item.is_file():
                    if self._search_in_file(item, regex):
                        found_any = True
                elif item.is_dir() and recursive:
                    if self._search_in_directory(item, regex, recursive):
                        found_any = True
            
            return found_any
            
        except Exception as e:
            print(f"Ошибка при поиске в директории {dir_path}: {e}")
            return False