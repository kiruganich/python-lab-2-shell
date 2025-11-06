import pytest
import os
import shutil
import tempfile
import sys
from pathlib import Path
import logging

# Добавляем путь к src в sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.commands.basic import BasicCommands
from src.commands.archive import ArchiveCommands
from src.commands.grep import GrepCommand
from src.commands.history import HistoryManager, UndoManager, HistoryCommands
from src.parser import parse_command
from src.logger import setup_logger

# Настройка логгера для тестов
logger = setup_logger()
logger.setLevel(logging.CRITICAL)  # Отключаем логгирование во время тестов

@pytest.fixture
def temp_dir():
    """Создает временную директорию для тестов и очищает её после завершения"""
    # Создаем временную директорию
    test_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    os.chdir(test_dir)
    
    # Создаем тестовую структуру файлов
    test_dir_path = Path(test_dir)
    
    # Создаем файлы
    (test_dir_path / "file1.txt").write_text("Содержимое файла 1")
    (test_dir_path / "file2.txt").write_text("Содержимое файла 2")
    (test_dir_path / "test with spaces.txt").write_text("Файл с пробелами")
    
    # Создаем поддиректорию
    subdir = test_dir_path / "subdir"
    subdir.mkdir()
    (subdir / "subfile.txt").write_text("Содержимое подфайла")
    
    # Создаем директорию с пробелами
    spaced_dir = test_dir_path / "dir with spaces"
    spaced_dir.mkdir()
    (spaced_dir / "inside.txt").write_text("Внутри директории с пробелами")
    
    yield test_dir_path
    
    # Возвращаемся в исходную директорию
    os.chdir(original_dir)
    # Удаляем временную директорию
    shutil.rmtree(test_dir)

@pytest.fixture
def history_manager():
    """Создает экземпляр HistoryManager с временным файлом истории"""
    temp_dir = tempfile.mkdtemp()
    history_file = Path(temp_dir) / ".history"
    hm = HistoryManager(str(history_file))
    yield hm
    shutil.rmtree(temp_dir)

@pytest.fixture
def undo_manager():
    """Создает экземпляр UndoManager с временной корзиной"""
    temp_dir = tempfile.mkdtemp()
    trash_dir = Path(temp_dir) / ".trash"
    um = UndoManager()
    um.trash_dir = trash_dir
    trash_dir.mkdir(parents=True, exist_ok=True)
    yield um
    shutil.rmtree(temp_dir)

def test_parse_command():
    """Тест функции парсинга команд"""
    # Тест простых команд
    cmd, args = parse_command("ls -l")
    assert cmd == "ls"
    assert args == ["-l"]
    
    # Тест команд с кавычками
    cmd, args = parse_command('cat "file with spaces.txt"')
    assert cmd == "cat"
    assert args == ["file with spaces.txt"]
    
    # Тест команд с несколькими аргументами в кавычках
    cmd, args = parse_command('cp "source file.txt" "dest file.txt"')
    assert cmd == "cp"
    assert args == ["source file.txt", "dest file.txt"]
    
    # Тест команды с незакрытыми кавычками
    cmd, args = parse_command('ls "unclosed')
    assert cmd is None
    assert "Незакрытые кавычки" in args[0]

def test_ls_command(temp_dir, history_manager, undo_manager, capsys):
    """Тест команды ls"""
    commands = BasicCommands(history_manager, undo_manager)
    
    # Тест простого ls
    assert commands.ls([]) is True
    captured = capsys.readouterr()
    assert "file1.txt" in captured.out
    assert "file2.txt" in captured.out
    assert "subdir" in captured.out
    assert "dir with spaces" in captured.out
    
    # Тест ls для конкретной директории
    assert commands.ls(["subdir"]) is True
    captured = capsys.readouterr()
    assert "subfile.txt" in captured.out
    
    # Тест ls для директории с пробелами в имени
    assert commands.ls(["dir with spaces"]) is True
    captured = capsys.readouterr()
    assert "inside.txt" in captured.out
    
    # Тест ls для несуществующей директории
    assert commands.ls(["nonexistent"]) is False
    captured = capsys.readouterr()
    assert "Ошибка" in captured.out

def test_cd_command(temp_dir, history_manager, undo_manager, capsys):
    """Тест команды cd"""
    commands = BasicCommands(history_manager, undo_manager)
    original_dir = os.getcwd()
    
    # Тест cd в поддиректорию
    assert commands.cd(["subdir"]) is True
    assert os.path.basename(os.getcwd()) == "subdir"
    
    # Тест cd .. для возврата назад
    assert commands.cd([".."]) is True
    assert Path(os.getcwd()) == temp_dir
    
    # Тест cd в директорию с пробелами
    assert commands.cd(["dir with spaces"]) is True
    assert os.path.basename(os.getcwd()) == "dir with spaces"
    
    # Тест cd .. для возврата назад
    assert commands.cd([".."]) is True
    assert Path(os.getcwd()) == temp_dir
    
    # Тест cd в несуществующую директорию
    assert commands.cd(["nonexistent"]) is False
    captured = capsys.readouterr()
    assert "Ошибка" in captured.out
    
    # Возвращаемся в исходную директорию
    os.chdir(original_dir)

def test_cat_command(temp_dir, history_manager, undo_manager, capsys):
    """Тест команды cat"""
    commands = BasicCommands(history_manager, undo_manager)
    
    # Тест cat существующего файла
    assert commands.cat(["file1.txt"]) is True
    captured = capsys.readouterr()
    assert "Содержимое файла 1" in captured.out
    
    # Тест cat файла с пробелами в имени
    assert commands.cat(["test with spaces.txt"]) is True
    captured = capsys.readouterr()
    assert "Файл с пробелами" in captured.out
    
    # Тест cat несуществующего файла
    assert commands.cat(["nonexistent.txt"]) is False
    captured = capsys.readouterr()
    assert "Ошибка" in captured.out
    
    # Тест cat директории
    assert commands.cat(["subdir"]) is False
    captured = capsys.readouterr()
    assert "не является файлом" in captured.out

def test_cp_command(temp_dir, history_manager, undo_manager, capsys):
    """Тест команды cp"""
    commands = BasicCommands(history_manager, undo_manager)
    
    # Тест копирования файла
    assert commands.cp(["file1.txt", "file1_copy.txt"]) is True
    assert (temp_dir / "file1_copy.txt").exists()
    assert (temp_dir / "file1_copy.txt").read_text() == "Содержимое файла 1"
    
    # Тест копирования файла с пробелами
    assert commands.cp(["test with spaces.txt", "copied with spaces.txt"]) is True
    assert (temp_dir / "copied with spaces.txt").exists()
    assert (temp_dir / "copied with spaces.txt").read_text() == "Файл с пробелами"
    
    # Тест копирования в существующую директорию
    assert commands.cp(["file2.txt", "subdir"]) is True
    assert (temp_dir / "subdir" / "file2.txt").exists()
    
    # Тест рекурсивного копирования директории
    assert commands.cp(["-r", "subdir", "subdir_copy"]) is True
    assert (temp_dir / "subdir_copy").exists()
    assert (temp_dir / "subdir_copy" / "subfile.txt").exists()
    
    # Тест копирования несуществующего файла
    assert commands.cp(["nonexistent.txt", "target.txt"]) is False
    captured = capsys.readouterr()
    assert "Ошибка" in captured.out
    
    # Тест копирования директории без флага -r
    assert commands.cp(["subdir", "new_subdir"]) is False
    captured = capsys.readouterr()
    assert "Для копирования каталога используйте опцию -r" in captured.out

def test_mv_command(temp_dir, history_manager, undo_manager, capsys):
    """Тест команды mv"""
    commands = BasicCommands(history_manager, undo_manager)
    
    # Тест перемещения файла
    assert commands.mv(["file1.txt", "file1_renamed.txt"]) is True
    assert not (temp_dir / "file1.txt").exists()
    assert (temp_dir / "file1_renamed.txt").exists()
    
    # Тест перемещения файла с пробелами
    assert commands.mv(["test with spaces.txt", "moved with spaces.txt"]) is True
    assert not (temp_dir / "test with spaces.txt").exists()
    assert (temp_dir / "moved with spaces.txt").exists()
    
    # Тест перемещения файла в директорию
    assert commands.mv(["file1_renamed.txt", "subdir"]) is True
    assert (temp_dir / "subdir" / "file1_renamed.txt").exists()
    
    # Тест перемещения несуществующего файла
    assert commands.mv(["nonexistent.txt", "target.txt"]) is False
    captured = capsys.readouterr()
    assert "Ошибка" in captured.out

def test_rm_command(temp_dir, history_manager, undo_manager, capsys):
    """Тест команды rm"""
    commands = BasicCommands(history_manager, undo_manager)
    
    # Создаем файл для удаления
    test_file = temp_dir / "to_delete.txt"
    test_file.write_text("Временный файл")
    
    # Тест удаления файла с подтверждением
    assert commands.rm(["to_delete.txt"]) is True
    assert not test_file.exists()
    
    # Тест удаления файла с пробелами
    spaced_file = temp_dir / "delete with spaces.txt"
    spaced_file.write_text("Файл для удаления")
    assert commands.rm(["delete with spaces.txt"]) is True
    assert not spaced_file.exists()
    
    # Тест удаления несуществующего файла
    assert commands.rm(["nonexistent.txt"]) is False
    captured = capsys.readouterr()
    assert "Ошибка" in captured.out
    
    # Тест удаления директории без флага -r
    assert commands.rm(["subdir"]) is False
    captured = capsys.readouterr()
    assert "Для удаления каталога используйте опцию -r" in captured.out
    
    # Тест принудительного удаления директории
    rm_dir = temp_dir / "rm_test_dir"
    rm_dir.mkdir()
    (rm_dir / "file.txt").write_text("Файл внутри")
    
    # Используем флаг -f для пропуска подтверждения
    assert commands.rm(["-r", "-f", "rm_test_dir"]) is True
    assert not rm_dir.exists()

def test_zip_command(temp_dir, history_manager, undo_manager, capsys):
    """Тест команды zip"""
    commands = ArchiveCommands(history_manager, undo_manager)
    
    # Тест создания ZIP-архива из директории
    assert commands.zip(["subdir", "subdir.zip"]) is True
    assert (temp_dir / "subdir.zip").exists()
    assert (temp_dir / "subdir.zip").stat().st_size > 0
    
    # Тест создания ZIP-архива из директории с пробелами
    assert commands.zip(["dir with spaces", "spaced_dir.zip"]) is True
    assert (temp_dir / "spaced_dir.zip").exists()
    assert (temp_dir / "spaced_dir.zip").stat().st_size > 0
    
    # Тест создания архива из несуществующей директории
    assert commands.zip(["nonexistent", "archive.zip"]) is False
    captured = capsys.readouterr()
    assert "Ошибка" in captured.out

def test_unzip_command(temp_dir, history_manager, undo_manager, capsys):
    """Тест команды unzip"""
    commands = ArchiveCommands(history_manager, undo_manager)
    
    # Создаем ZIP-архив для тестирования
    import zipfile
    zip_path = temp_dir / "test.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.write(temp_dir / "file2.txt", "file2.txt")
    
    # Тест распаковки архива
    extract_dir = temp_dir / "unzipped"
    assert commands.unzip([str(zip_path), str(extract_dir)]) is True
    assert extract_dir.exists()
    assert (extract_dir / "file2.txt").exists()
    
    # Тест распаковки несуществующего архива
    assert commands.unzip(["nonexistent.zip", "extract_dir"]) is False
    captured = capsys.readouterr()
    assert "Ошибка" in captured.out

def test_tar_command(temp_dir, history_manager, undo_manager, capsys):
    """Тест команды tar"""
    commands = ArchiveCommands(history_manager, undo_manager)
    
    # Тест создания TAR.GZ архива из директории
    assert commands.tar(["subdir", "subdir.tar.gz"]) is True
    assert (temp_dir / "subdir.tar.gz").exists()
    assert (temp_dir / "subdir.tar.gz").stat().st_size > 0
    
    # Тест создания архива из несуществующей директории
    assert commands.tar(["nonexistent", "archive.tar.gz"]) is False
    captured = capsys.readouterr()
    assert "Ошибка" in captured.out

def test_untar_command(temp_dir, history_manager, undo_manager, capsys):
    """Тест команды untar"""
    commands = ArchiveCommands(history_manager, undo_manager)
    
    # Создаем TAR.GZ архив для тестирования
    import tarfile
    tar_path = temp_dir / "test.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(temp_dir / "file2.txt", "file2.txt")
    
    # Тест распаковки архива
    extract_dir = temp_dir / "untarred"
    assert commands.untar([str(tar_path), str(extract_dir)]) is True
    assert extract_dir.exists()
    assert (extract_dir / "file2.txt").exists()
    
    # Тест распаковки несуществующего архива
    assert commands.untar(["nonexistent.tar.gz", "extract_dir"]) is False
    captured = capsys.readouterr()
    assert "Ошибка" in captured.out

def test_grep_command(temp_dir, capsys):
    """Тест команды grep"""
    commands = GrepCommand()
    
    # Тест поиска в одном файле
    assert commands.grep(["Содержимое", "file1.txt"]) is True
    captured = capsys.readouterr()
    assert "file1.txt:1:Содержимое файла 1" in captured.out
    
    # Тест поиска в файле с пробелами в имени
    assert commands.grep(["пробелами", '"test with spaces.txt"']) is True
    captured = capsys.readouterr()
    assert "test with spaces.txt:1:Файл с пробелами" in captured.out
    
    # Тест поиска с игнорированием регистра
    assert commands.grep(["содержимое", "file1.txt", "-i"]) is True
    captured = capsys.readouterr()
    assert "file1.txt:1:Содержимое файла 1" in captured.out
    
    # Тест рекурсивного поиска
    assert commands.grep(["подфайла", "subdir", "-r"]) is True
    captured = capsys.readouterr()
    assert "subdir/subfile.txt:1:Содержимое подфайла" in captured.out
    
    # Тест поиска в несуществующем файле
    assert commands.grep(["pattern", "nonexistent.txt"]) is False
    captured = capsys.readouterr()
    assert "Ошибка" in captured.out

def test_history_commands(temp_dir, history_manager, undo_manager, capsys):
    """Тест команд истории и отмены"""
    commands = HistoryCommands(history_manager, undo_manager)
    basic_cmds = BasicCommands(history_manager, undo_manager)
    
    # Добавляем команды в историю
    history_manager.add_command("ls -l")
    history_manager.add_command("cd subdir")
    history_manager.add_command("cat file.txt")
    
    # Тест просмотра всей истории
    assert commands.history([]) is True
    captured = capsys.readouterr()
    assert "История команд:" in captured.out
    assert "1: ls -l" in captured.out
    assert "2: cd subdir" in captured.out
    assert "3: cat file.txt" in captured.out
    
    # Тест просмотра ограниченной истории
    assert commands.history(["2"]) is True
    captured = capsys.readouterr()
    assert "2: cd subdir" in captured.out
    assert "3: cat file.txt" in captured.out
    assert "1: ls -l" not in captured.out
    
    # Тест очистки истории
    assert commands.clear_history([]) is True
    assert len(history_manager.history) == 0
    
    # Тест отмены операции cp
    # Создаем файл для тестирования
    (temp_dir / "source.txt").write_text("Исходный файл")
    # Выполняем копирование
    assert basic_cmds.cp(["source.txt", "dest.txt"]) is True
    assert (temp_dir / "dest.txt").exists()
    # Отменяем операцию
    assert commands.undo([]) is True
    assert not (temp_dir / "dest.txt").exists()
    
    # Тест отмены операции mv
    (temp_dir / "source2.txt").write_text("Еще один файл")
    # Выполняем перемещение
    assert basic_cmds.mv(["source2.txt", "renamed.txt"]) is True
    assert not (temp_dir / "source2.txt").exists()
    assert (temp_dir / "renamed.txt").exists()
    # Отменяем операцию
    assert commands.undo([]) is True
    assert (temp_dir / "source2.txt").exists()
    assert not (temp_dir / "renamed.txt").exists()
    
    # Тест отмены операции rm
    (temp_dir / "to_delete.txt").write_text("Файл для удаления")
    # Выполняем удаление
    assert basic_cmds.rm(["-f", "to_delete.txt"]) is True
    assert not (temp_dir / "to_delete.txt").exists()
    # Отменяем операцию
    assert commands.undo([]) is True
    assert (temp_dir / "to_delete.txt").exists()