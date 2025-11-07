import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.logger import setup_logger
from src.parser import parse_command
from src.commands.basic import BasicCommands
from src.commands.archive import ArchiveCommands
from src.commands.grep import GrepCommand
from src.commands.history import HistoryManager, UndoManager, HistoryCommands

logger = setup_logger()

class ShellManager:
    def __init__(self):
        self.current_dir = os.getcwd()
        self.history_manager = HistoryManager()
        self.undo_manager = UndoManager()
        
        # Инициализация команд
        self.basic_cmds = BasicCommands(self.history_manager, self.undo_manager)
        self.archive_cmds = ArchiveCommands(self.history_manager, self.undo_manager)
        self.grep_cmd = GrepCommand()
        self.history_cmds = HistoryCommands(self.history_manager, self.undo_manager)
        
        # Регистрация команд
        self.commands = {
            'ls': self.basic_cmds.ls,
            'cd': self.basic_cmds.cd,
            'cat': self.basic_cmds.cat,
            'cp': self.basic_cmds.cp,
            'mv': self.basic_cmds.mv,
            'rm': self.basic_cmds.rm,
            'zip': self.archive_cmds.zip,
            'unzip': self.archive_cmds.unzip,
            'tar': self.archive_cmds.tar,
            'untar': self.archive_cmds.untar,
            'grep': self.grep_cmd.grep,
            'history': self.history_cmds.history,
            'clear_history': self.history_cmds.clear_history,
            'undo': self.history_cmds.undo,
        }

        logger.info("ShellManager инициализирован")
    
    def run_shell(self):
        logger.info("Запуск Mini Shell")
        print("Добро пожаловать в Mini Shell")
        print("Доступные команды: ls, cd, cat, cp, mv, rm, zip, unzip, tar, untar, grep, history, clear_history, undo, exit")
        print("Для работы с именами файлов/директорий, содержащими пробелы, необходимо использовать двойные кавычки")
        print("-" * 60)
    
        while True:
            try:
                # Отображение текущей директории перед полем ввода команд
                prompt = f"{os.path.basename(self.current_dir)}$ "
                command_line = input(prompt).strip()
            
                if not command_line:
                    continue
            
                # Парсим команду и аргументы с обработкой кавычек
                cmd, args = parse_command(command_line)
            
                # Обработка ошибок парсинга
                if cmd is None:
                    if isinstance(args, list) and args:
                        print(f"Ошибка парсинга: {args[0]}")
                        logger.error(f"Ошибка парсинга команды: {args[0]}")
                    continue
            
                # Добавляем команду в историю оболочки
                self.history_manager.add_command(command_line)
            
                # Обработка встроенных команд
                if cmd in ['exit', 'quit']:
                    logger.info("Выход из оболочки")
                    break
            
                # Выполняем команду
                if cmd in self.commands:
                    self.commands[cmd](args)
                else:
                    print(f"Неизвестная команда: {cmd}")
                    logger.warning(f"Неизвестная команда: {cmd}")
            
                # Обновляем текущую директорию
                self.current_dir = os.getcwd()
            
            except KeyboardInterrupt:
                print("\nПрервано пользователем")
                logger.info("Прервано пользователем")
                continue
            except EOFError:
                print("\nВыход из оболочки")
                logger.info("Выход из оболочки по EOF")
                break
            except Exception as e:
                print(f"Ошибка: {e}")
                logger.exception(f"Необработанное исключение: {e}")
    
    def execute_command(self, command_line):
        """Выполняет одну команду"""
        try:
            cmd, args = parse_command(command_line)
            if not cmd:
                return True
            
            if cmd in ['exit', 'quit']:
                return False
            
            if cmd in self.commands:
                self.commands[cmd](args)
            else:
                print(f"Неизвестная команда: {cmd}")
                logger.warning(f"Неизвестная команда: {cmd}")
            
            return True
            
        except Exception as e:
            print(f"Ошибка при выполнении команды: {e}")
            logger.exception(f"Ошибка при выполнении команды '{command_line}': {e}")
            return True

def main():
    """Точка входа в программу"""
    try:
        # Создаем необходимые директории
        Path("logs").mkdir(exist_ok=True)
        Path("data").mkdir(exist_ok=True)
        
        # Запускаем оболочку
        manager = ShellManager()
        manager.run_shell()
        
        logger.info("Работа оболочки завершена")
        print("\nРабота оболочки завершена. До свидания!")
        return 0
        
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        print(f"Критическая ошибка: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())