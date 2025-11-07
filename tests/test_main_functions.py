import pytest
import os
import shutil
import tempfile
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.commands.basic import BasicCommands
from src.commands.archive import ArchiveCommands
from src.commands.grep import GrepCommand
from src.commands.history import HistoryManager, UndoManager, HistoryCommands
from src.parser import parse_command


@pytest.fixture
def temp_dir():
    test_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    os.chdir(test_dir)

    test_dir_path = Path(test_dir)

    (test_dir_path / "file1.txt").write_text("Содержимое файла 1", encoding='utf-8')
    (test_dir_path / "file2.txt").write_text("Содержимое файла 2", encoding='utf-8')
    (test_dir_path / "test with spaces.txt").write_text("Файл с пробелами", encoding='utf-8')

    subdir = test_dir_path / "subdir"
    subdir.mkdir()
    (subdir / "subfile.txt").write_text("Содержимое подфайла", encoding='utf-8')

    spaced_dir = test_dir_path / "dir with spaces"
    spaced_dir.mkdir()
    (spaced_dir / "inside.txt").write_text("Внутри директории с пробелами", encoding='utf-8')
    
    yield test_dir_path
    
    os.chdir(original_dir)
    shutil.rmtree(test_dir)


@pytest.fixture
def history_manager():
    temp_dir = tempfile.mkdtemp()
    history_file = Path(temp_dir) / ".history"
    hm = HistoryManager()
    hm.history_file = history_file
    history_file.parent.mkdir(parents=True, exist_ok=True)

    yield hm
    shutil.rmtree(temp_dir)


@pytest.fixture
def undo_manager():
    temp_dir = tempfile.mkdtemp()
    trash_dir = Path(temp_dir) / ".trash"
    um = UndoManager()
    um.trash_dir = trash_dir
    trash_dir.mkdir(parents=True, exist_ok=True)

    yield um
    shutil.rmtree(temp_dir)


def test_parse_command():
    cmd, args = parse_command("ls -l")
    assert cmd == "ls"
    assert args == ["-l"]
    
    cmd, args = parse_command('cat "file with spaces.txt"')
    assert cmd == "cat"
    assert args == ["file with spaces.txt"]
    
    cmd, args = parse_command('cp "src.txt" "dst.txt"')
    assert cmd == "cp"
    assert args == ["src.txt", "dst.txt"]


def test_cat_command(temp_dir, history_manager, undo_manager, capsys):
    commands = BasicCommands(history_manager, undo_manager)
    assert commands.cat(["file1.txt"]) is True
    captured = capsys.readouterr()
    assert "Содержимое файла 1" in captured.out


def test_rm_command(temp_dir, history_manager, undo_manager, capsys):
    commands = BasicCommands(history_manager, undo_manager)

    test_file = temp_dir / "to_delete.txt"
    test_file.write_text("Временный файл", encoding='utf-8')
    assert commands.rm(["to_delete.txt"]) is True
    assert not test_file.exists()

    spaced_file = temp_dir / "delete with spaces.txt"
    spaced_file.write_text("Файл для удаления", encoding='utf-8')
    assert commands.rm(["delete with spaces.txt"]) is True
    assert not spaced_file.exists()

    assert commands.rm(["nonexistent.txt"]) is False
    captured = capsys.readouterr()
    assert "Ошибка" in captured.out

    assert commands.rm(["subdir"]) is False
    captured = capsys.readouterr()
    assert "Для удаления каталога используйте опцию -r" in captured.out

    # Тест удаления с подтверждением
    import io
    original_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO('y\n')
        rm_dir = temp_dir / "rm_test_dir"
        rm_dir.mkdir()
        (rm_dir / "file.txt").write_text("Файл внутри", encoding='utf-8')
        assert commands.rm(["-r", "rm_test_dir"]) is True
        assert not rm_dir.exists()
    finally:
        sys.stdin = original_stdin


def test_grep_command(temp_dir, capsys):
    commands = GrepCommand()
    assert commands.grep(["Содержимое", "file1.txt"]) is True
    captured = capsys.readouterr()
    assert "file1.txt:1:Содержимое файла 1" in captured.out

    assert commands.grep(["пробелами", "test with spaces.txt"]) is True
    captured = capsys.readouterr()
    assert "test with spaces.txt:1:Файл с пробелами" in captured.out


def test_history_commands(temp_dir, history_manager, undo_manager, capsys):
    commands = HistoryCommands(history_manager, undo_manager)
    basic_cmds = BasicCommands(history_manager, undo_manager)

    history_manager.add_command("ls -l")
    history_manager.add_command("cd subdir")
    history_manager.add_command("cat file.txt")

    assert commands.history([]) is True
    captured = capsys.readouterr()
    assert "История команд:" in captured.out
    assert "1: ls -l" in captured.out
    assert "2: cd subdir" in captured.out
    assert "3: cat file.txt" in captured.out

    # Тест undo для cp
    (temp_dir / "source.txt").write_text("Исходный файл", encoding='utf-8')
    history_manager.add_command("cp source.txt dest.txt")
    assert basic_cmds.cp(["source.txt", "dest.txt"]) is True
    assert commands.undo([]) is True
    assert not (temp_dir / "dest.txt").exists()

    # Тест undo для mv
    (temp_dir / "source2.txt").write_text("Еще один файл", encoding='utf-8')
    history_manager.add_command("mv source2.txt renamed.txt")
    assert basic_cmds.mv(["source2.txt", "renamed.txt"]) is True
    assert commands.undo([]) is True
    assert (temp_dir / "source2.txt").exists()

    # Тест undo для rm
    (temp_dir / "to_delete.txt").write_text("Файл для удаления", encoding='utf-8')
    history_manager.add_command("rm to_delete.txt")
    assert basic_cmds.rm(["to_delete.txt"]) is True
    assert commands.undo([]) is True
    assert (temp_dir / "to_delete.txt").exists()