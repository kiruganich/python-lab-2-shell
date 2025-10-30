import os.path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from src.enums.file_mode import FileReadMode
from src.services.base import OSConsoleServiceBase


def test_cat_for_nonexisted_file(service: OSConsoleServiceBase, fs: FakeFilesystem):
    # Arrange
    fs.create_dir("data")
    fs.create_file(os.path.join("data", "existing.txt"), contents="test")

    # Act
    with pytest.raises(FileNotFoundError):
        service.cat(
            filename=os.path.join("data", "nonexisting.txt"), mode=FileReadMode.string
        )


def test_cat_for_folder(service: OSConsoleServiceBase, fs: FakeFilesystem):
    fs.create_dir("data")
    fs.create_file(os.path.join("data", "existing.txt"), contents="test")

    with pytest.raises(IsADirectoryError):
        service.cat("data", mode=FileReadMode.string)


def test_cat_file_with_text(service: OSConsoleServiceBase, fs: FakeFilesystem):
    fs.create_dir("data")
    content = "test"
    path = os.path.join("data", "existing.txt")
    fs.create_file(path, contents=content)

    result = service.cat(path, mode=FileReadMode.string)

    assert result == content


def test_cat_file_with_bytes(service: OSConsoleServiceBase, fs: FakeFilesystem):
    fs.create_dir("data")
    content = b"test"
    path = os.path.join("data", "existing.txt")
    fs.create_file(path, contents=content)

    result = service.cat(path, mode=FileReadMode.bytes)
    assert result == content
