import shutil
import tarfile
import zipfile
from pathlib import Path
from ..logger import setup_logger

logger = setup_logger()

class ArchiveCommands:
    
    def __init__(self, history_manager=None, undo_manager=None):
        self.history_manager = history_manager
        self.undo_manager = undo_manager
    
    def zip(self, args):
        """Создание ZIP-архива из папки"""
        if len(args) < 2:
            print("Использование: zip <folder> <archive.zip>")
            return False
            
        folder, archive = args
        
        try:
            folder_path = Path(folder).resolve()
            archive_path = Path(archive).resolve()
            
            if not folder_path.exists():
                print(f"Ошибка: Папка {folder_path} не существует")
                return False
            
            if not folder_path.is_dir():
                print(f"Ошибка: {folder_path} не является директорией")
                return False
            
            shutil.make_archive(str(archive_path).replace('.zip', ''), 'zip', folder_path)
            
            if self.undo_manager:
                self.undo_manager.record_operation(
                    'zip',
                    str(folder_path),
                    str(archive_path),
                    cmd_index=len(self.history_manager.history) if self.history_manager else None
                )
            
            print(f"ZIP архив создан: {archive_path}")
            logger.info(f"zip {folder} {archive} OK")
            return True
            
        except Exception as e:
            print(f"Ошибка: {e}")
            logger.error(f"zip {folder} {archive} ERROR: {e}")
            return False
    
    def unzip(self, args):
        """Распаковывка ZIP-архива"""
        if len(args) < 1:
            print("Использование: unzip <archive.zip> [extract_path]")
            return False
            
        archive = args[0]
        extract_path = args[1] if len(args) > 1 else "."
        
        try:
            archive_path = Path(archive).resolve()
            extract_path = Path(extract_path).resolve()
            
            if not archive_path.exists():
                print(f"Ошибка: Архив {archive_path} не существует")
                return False
            
            if not zipfile.is_zipfile(archive_path):
                print(f"Ошибка: {archive_path} не является ZIP-архивом")
                return False
            
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(extract_path)
            
            print(f"Архив распакован в: {extract_path}")
            logger.info(f"unzip {archive} {extract_path if len(args) > 1 else ''} OK")
            return True
            
        except Exception as e:
            print(f"Ошибка: {e}")
            logger.error(f"unzip {archive} {extract_path if len(args) > 1 else ''} ERROR: {e}")
            return False
    
    def tar(self, args):
        """Создание TAR.GZ архива из папки"""
        if len(args) < 2:
            print("Использование: tar <folder> <archive.tar.gz>")
            return False
            
        folder, archive = args
        
        try:
            folder_path = Path(folder).resolve()
            archive_path = Path(archive).resolve()
            
            if not folder_path.exists():
                print(f"Ошибка: Папка {folder_path} не существует")
                return False
            
            if not folder_path.is_dir():
                print(f"Ошибка: {folder_path} не является директорией")
                return False
            
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(folder_path, arcname=folder_path.name)
            
            if self.undo_manager:
                self.undo_manager.record_operation(
                    'tar',
                    str(folder_path),
                    str(archive_path),
                    cmd_index=len(self.history_manager.history) if self.history_manager else None
                )
            
            print(f"TAR.GZ архив создан: {archive_path}")
            logger.info(f"tar {folder} {archive} OK")
            return True
            
        except Exception as e:
            print(f"Ошибка: {e}")
            logger.error(f"tar {folder} {archive} ERROR: {e}")
            return False
    
    def untar(self, args):
        """Распаковка TAR.GZ архива"""
        if len(args) < 1:
            print("Использование: untar <archive.tar.gz> [extract_path]")
            return False
            
        archive = args[0]
        extract_path = args[1] if len(args) > 1 else "."
        
        try:
            archive_path = Path(archive).resolve()
            extract_path = Path(extract_path).resolve()
            
            if not archive_path.exists():
                print(f"Ошибка: Архив {archive_path} не существует")
                return False
            
            if not tarfile.is_tarfile(archive_path):
                print(f"Ошибка: {archive_path} не является TAR-архивом")
                return False
            
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=extract_path, filter='data')
            
            print(f"Архив распакован в: {extract_path}")
            logger.info(f"untar {archive} {extract_path if len(args) > 1 else ''} OK")
            return True
            
        except Exception as e:
            print(f"Ошибка: {e}")
            logger.error(f"untar {archive} {extract_path if len(args) > 1 else ''} ERROR: {e}")
            return False