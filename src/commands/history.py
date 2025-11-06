import shutil
from pathlib import Path
from ..logger import setup_logger

logger = setup_logger()

class HistoryManager:
    def __init__(self, history_file=None):
        self.history_file = history_file or Path("data") / ".history"
        self.history = []
        self.load_history()
    
    def load_history(self):

        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            logger.error(f"Ошибка при загрузке истории: {e}")
            self.history = []
    
    def save_history(self):
        """Сохранение истории команд в файл"""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                for cmd in self.history:
                    f.write(f"{cmd}\n")
        except Exception as e:
            logger.error(f"Ошибка при сохранении истории: {e}")
    
    def add_command(self, command):
        """Добавление команды в историю"""
        self.history.append(command)
        self.save_history()
    
    def get_history(self, limit=None):
        """Возвращает историю команд"""
        if limit is None or limit <= 0:
            return [(i+1, cmd) for i, cmd in enumerate(self.history)]
        
        # Возвращаем последние N команд с правильной нумерацией
        start_idx = max(0, len(self.history) - limit)
        # Сохраняем правильную нумерацию (1-based индекс)
        return [(start_idx + i + 1, cmd) for i, cmd in enumerate(self.history[start_idx:])]
    
    def clear_history(self):
        """Очистка истории"""
        self.history = []
        self.save_history()
    
    def remove_command(self, cmd_index):
        """Удаление команды из истории по индексу (1-based)"""
        try:
            idx = cmd_index - 1
            if 0 <= idx < len(self.history):
                self.history.pop(idx)
                self.save_history()
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при удалении команды из истории: {e}")
            return False

class UndoManager:
    def __init__(self):
        self.trash_dir = Path("data") / ".trash"
        self.trash_dir.mkdir(parents=True, exist_ok=True)
        self.undo_history = []
    
    def record_operation(self, operation, source, destination=None, cmd_index=None):
        """Записывание операции для возможности отмены"""
        record = {
            'operation': operation,
            'source': source,
            'destination': destination,
            'cmd_index': cmd_index
        }
        self.undo_history.append(record)
    
    def undo_last_operation(self, history_manager):
        """Отмена последней операции"""
        try:
            if not self.undo_history:
                print("Нет операций для отмены")
                return False
            
            last_op = self.undo_history.pop()
            operation = last_op['operation']
            cmd_index = last_op.get('cmd_index')
            
            if operation == 'cp':
                self._undo_copy(last_op)
            elif operation == 'mv':
                self._undo_move(last_op)
            elif operation == 'rm':
                self._undo_remove(last_op)
            elif operation in ['zip', 'tar']:
                self._undo_archive(last_op)
            else:
                print(f"Неизвестная операция для отмены: {operation}")
                return False
            
            if cmd_index and history_manager:
                history_manager.remove_command(cmd_index)
            
            return True
            
        except Exception as e:
            print(f"Ошибка при отмене операции: {e}")
            return False
    
    def _undo_copy(self, operation):
        """Отмена операции копирования"""
        destination = operation['destination']
        
        if Path(destination).exists():
            if Path(destination).is_dir():
                shutil.rmtree(destination)
            else:
                Path(destination).unlink()
            print(f"Отмена копирования: удален файл/директория {destination}")
    
    def _undo_move(self, operation):
        """Отмена операции перемещения"""
        source = operation['source']
        destination = operation['destination']
        
        if Path(destination).exists():
            if Path(destination).is_dir():
                if not Path(source).exists():
                    Path(source).mkdir(parents=True)
                shutil.move(str(destination), str(source))
            else:
                if Path(source).parent.exists():
                    shutil.move(str(destination), str(source))
                else:
                    Path(source).parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(destination), str(source))
            
            print(f"Отмена перемещения: восстановлен файл/директория {source}")
    
    def _undo_remove(self, operation):
        """Отмена операции удаления"""
        trash_path = operation['source']
        original_path = operation['destination']
        
        if Path(trash_path).exists():
            original_dir = Path(original_path).parent
            if not original_dir.exists():
                original_dir.mkdir(parents=True, exist_ok=True)
            
            if Path(trash_path).is_dir():
                shutil.copytree(trash_path, original_path)
            else:
                shutil.copy2(trash_path, original_path)
            
            print(f"Отмена удаления: восстановлен файл/директория {original_path}")
    
    def _undo_archive(self, operation):
        """Отмена операции создания архива"""
        archive_path = operation['destination']
        
        if Path(archive_path).exists():
            Path(archive_path).unlink()
            print(f"Отмена создания архива: удален файл {archive_path}")

class HistoryCommands:
    
    def __init__(self, history_manager, undo_manager):
        self.history_manager = history_manager
        self.undo_manager = undo_manager
    
    def history(self, args):
        """Вывод истории команд"""
        limit = None
        if args:
            try:
                limit = int(args[0])
            except ValueError:
                print(f"Ошибка: Некорректный аргумент для history: {args[0]}")
                return False
        
        history = self.history_manager.get_history(limit)
        
        if not history:
            print("История команд пуста")
            return True
        
        print("История команд:")
        for idx, cmd in history:
            print(f"{idx}: {cmd}")
        
        return True
    
    def clear_history(self, args):
        self.history_manager.clear_history()
        print("История команд очищена")
        return True
    
    def undo(self, args):
        success = self.undo_manager.undo_last_operation(self.history_manager)
        return success