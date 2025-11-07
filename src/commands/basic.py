import os
import shutil
import stat
import time
from pathlib import Path
from ..validator import (
    ensure_exists, ensure_is_dir, ensure_is_file, ensure_not_root
)
from ..logger import setup_logger

logger = setup_logger()

class   BasicCommands:
    
    def __init__(self, history_manager=None, undo_manager=None):
        self.history_manager = history_manager
        self.undo_manager = undo_manager
    

    def ls(self, args):
        long_format = False
        path = "."
        
        if args:
            if args[0] == "-l":
                long_format = True
                if len(args) > 1:
                    path = args[1]
            else:
                path = args[0]
        
        try:
            target_path = Path(path).resolve()
            ensure_exists(target_path)
            ensure_is_dir(target_path)
            
            items = list(target_path.iterdir())
            if not items:
                print("Директория пуста")
                return True
            
            if long_format:
                for item in sorted(items):
                    try:
                        stat_info = item.stat()

                        if item.is_dir():
                            file_type = 'd'
                        else:
                            file_type = '-'
                        
                        mode = stat_info.st_mode
                        permissions = file_type + 'rw-r--r--'
                        nlinks = 1
                        try:
                            owner = os.getlogin()
                        except OSError:
                            owner = "user"
                        group = owner
                        size = stat_info.st_size
                        mtime = time.strftime('%b %d %H:%M', time.localtime(stat_info.st_mtime))
                        
                        name = item.name
                        if item.is_dir():
                            name += '/'
                        elif item.is_symlink():
                            name += '@'
                        elif mode & stat.S_IXUSR:
                            name += '*'
                        
                        print(f"{permissions} {nlinks:2} {owner:8} {group:8} {size:8} {mtime} {name}")
                        
                    except Exception as e:
                        print(f"? ? ? ? ? ? ? {item.name}")
            else:
                for item in sorted(items):
                    name = item.name
                    if item.is_dir():
                        name += '/'
                    elif item.is_symlink():
                        name += '@'
                    elif item.stat().st_mode & stat.S_IXUSR:
                        name += '*'
                    print(name)
            
            logger.info(f"ls {' '.join(args)} OK")
            return True
            
        except Exception as e:
            print(f"Ошибка: {e}")
            logger.error(f"ls {' '.join(args)} ERROR: {e}")
            return False
    
    def cd(self, args):
        if args:
            path = args[0]
        else:
            path = os.path.expanduser("~")
        
        try:
            target_path = Path(path).resolve()
            
            if path == "~":
                target_path = Path.home()
            elif path == "..":
                target_path = Path.cwd().parent
            
            ensure_exists(target_path)
            ensure_is_dir(target_path)
            
            os.chdir(target_path)
            logger.info(f"cd {path} OK")
            return True
            
        except Exception as e:
            print(f"Ошибка: {e}")
            logger.error(f"cd {path} ERROR: {e}")
            return False
    
    def cat(self, args):
    
        if not args:
            print("Не указан файл для просмотра")
            return False
            
        filename = args[0]
        
        try:
            file_path = Path(filename).resolve()
            ensure_exists(file_path)
            ensure_is_file(file_path)
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                print(f.read())
            
            logger.info(f"cat {filename} OK")
            return True
        
        except Exception as e:
            print(f"Ошибка при работе с файлом '{filename}': {e}")
            logger.error(f"cat '{filename}' ERROR: {e}")
            return False
    
    def cp(self, args):
        if len(args) < 2:
            print("Использование: cp [-r] <источник> <назначение>")
            return False
            
        recursive = "-r" in args
        if recursive:
            clean_args = [arg for arg in args if arg != "-r"]
            if len(clean_args) < 2:
                print("Использование: cp [-r] <источник> <назначение>")
                return False
            src, dst = clean_args[0], clean_args[1]
        else:
            src, dst = args[0], args[1]
        
        try:
            src_path = Path(src).resolve()
            dst_path = Path(dst).resolve()
            
            ensure_exists(src_path)
            
            if src_path.is_dir() and not recursive:
                print("Для копирования каталога используйте опцию -r")
                return False
            
            if src_path.is_dir():
                if dst_path.exists() and dst_path.is_dir():
                    dst_path = dst_path / src_path.name
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                if dst_path.is_dir():
                    dst_path = dst_path / src_path.name
                shutil.copy2(src_path, dst_path)
            
            if self.undo_manager:
                self.undo_manager.record_operation(
                    'cp', 
                    str(src_path), 
                    str(dst_path),
                    cmd_index=len(self.history_manager.history) if self.history_manager else None
                )
            
            print(f"Скопировано: {src_path} -> {dst_path}")
            logger.info(f"cp {src} {dst} {'-r' if recursive else ''} OK")
            return True
            
        except Exception as e:
            print(f"Ошибка: {e}")
            logger.error(f"cp {src} {dst} {'-r' if recursive else ''} ERROR: {e}")
            return False
    
    def mv(self, args):
        if len(args) < 2:
            print("Использование: mv <источник> <назначение>")
            return False
            
        src, dst = args[0], args[1]
        
        try:
            src_path = Path(src).resolve()
            dst_path = Path(dst).resolve()
            
            ensure_exists(src_path)
            
            if dst_path.is_dir():
                dst_path = dst_path / src_path.name
            
            if src_path.resolve() == dst_path.resolve():
                print(f"Предупреждение: Исходный и целевой пути совпадают")
                return True
            
            ensure_not_root(src_path)
            
            shutil.move(str(src_path), str(dst_path))
            
            if self.undo_manager:
                self.undo_manager.record_operation(
                    'mv', 
                    str(src_path), 
                    str(dst_path),
                    cmd_index=len(self.history_manager.history) if self.history_manager else None
                )
            
            print(f"Перемещено: {src_path} -> {dst_path}")
            logger.info(f"mv {src} {dst} OK")
            return True
            
        except Exception as e:
            print(f"Ошибка: {e}")
            logger.error(f"mv {src} {dst} ERROR: {e}")
            return False
    
    def rm(self, args):
        if not args:
            print("Использование: rm [-r] <файл/каталог>")
            logger.error("rm ERROR: нет аргументов")
            return False
            
        recursive = "-r" in args
        
        # Удаление флага из аргументов
        clean_args = [arg for arg in args if arg != "-r"]
        if not clean_args:
            print("Использование: rm [-r] <файл/каталог>")
            logger.error("rm ERROR: нет целевого пути")
            return False
            
        target = clean_args[0]
        
        try:
            target_path = Path(target).resolve()
            
            # Проверки
            if not target_path.exists():
                print(f"Ошибка: Путь {target_path} не существует")
                logger.error(f"rm {target} ERROR: путь не существует")
                return False
                
            ensure_not_root(target_path)
            
            # Удаление файла (без подтверждения)
            if target_path.is_file():
                # Копируем в корзину для возможности отмены
                trash_dir = Path("data") / ".trash"
                trash_dir.mkdir(parents=True, exist_ok=True)
                backup_path = trash_dir / target_path.name
                
                counter = 1
                while backup_path.exists():
                    backup_path = trash_dir / f"{target_path.name}_{counter}"
                    counter += 1
                
                shutil.copy2(target_path, backup_path)
                
                # Записываем операцию
                if self.undo_manager:
                    self.undo_manager.record_operation(
                        'rm', 
                        str(backup_path), 
                        str(target_path),
                        cmd_index=len(self.history_manager.history) if self.history_manager else None
                    )
                
                target_path.unlink()
                print(f"Файл удалён: {target_path}")
                logger.info(f"rm {target} OK")
                return True
            
            # Удаление директории
            if target_path.is_dir():
                if not recursive:
                    print("Для удаления каталога используйте опцию -r")
                    logger.error(f"rm {target} ERROR: попытка удалить каталог без -r")
                    return False
                
                # Подтверждение при удалении каталога
                confirm = input(f"Удалить директорию {target_path} и всё её содержимое? (y/n): ")
                if confirm.lower() != 'y':
                    print("Удаление отменено")
                    logger.info(f"rm -r {target} CANCELLED by user")
                    return False
                
                # Перемещение в корзину для возможности отмены
                trash_dir = Path("data") / ".trash"
                trash_dir.mkdir(parents=True, exist_ok=True)
                backup_path = trash_dir / target_path.name
                
                counter = 1
                while backup_path.exists():
                    backup_path = trash_dir / f"{target_path.name}_{counter}"
                    counter += 1
                
                # 🔴 СНАЧАЛА копируем в корзину
                shutil.copytree(target_path, backup_path)
                
                # ✅ ПОТОМ записываем операцию
                if self.undo_manager:
                    self.undo_manager.record_operation(
                        'rm', 
                        str(backup_path), 
                        str(target_path),
                        cmd_index=len(self.history_manager.history) if self.history_manager else None
                    )
                
                # И только потом удаляем оригинал
                shutil.rmtree(target_path)
                
                print(f"Директория удалена: {target_path}")
                logger.info(f"rm -r {target} OK")
                return True
                
        except Exception as e:
            print(f"Ошибка: {e}")
            logger.error(f"rm {'-r' if recursive else ''} {target} ERROR: {e}")
            return False