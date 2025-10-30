from pathlib import Path
from unittest.mock import Mock

import pytest

from pytest_mock import MockerFixture

from src.services.base import OSConsoleServiceBase


def test_ls_called_for_nonexisted_folder(
    service: OSConsoleServiceBase, fake_pathlib_path_class: Mock, mocker: MockerFixture
):
    # Arrange
    fake_path_object: Mock = mocker.create_autospec(Path, instance=True, spec_set=True)
    fake_path_object.exists.return_value = False
    nonexistent_path: str = "/nonexistent"
    fake_pathlib_path_class.return_value = fake_path_object

    # Act
    with pytest.raises(FileNotFoundError):
        service.ls(nonexistent_path)

    # Assert
    fake_pathlib_path_class.assert_called_with(nonexistent_path)
    fake_path_object.exists.assert_called_once()


def test_ls_called_for_file(
    service: OSConsoleServiceBase,
    fake_pathlib_path_class: Mock,
    mocker: MockerFixture,
):
    # Arrange
    path_object: Mock = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_object.exists.return_value = True
    path_object.is_dir.return_value = False
    not_a_directory_file: str = "file.txt"
    fake_pathlib_path_class.return_value = path_object

    with pytest.raises(NotADirectoryError):
        service.ls(not_a_directory_file)

    fake_pathlib_path_class.assert_called_with(not_a_directory_file)
    path_object.exists.assert_called_once()


def test_ls_called_for_existing_directory(
    service: OSConsoleServiceBase,
    fake_pathlib_path_class: Mock,
    mocker: MockerFixture,
):

    path_obj = mocker.create_autospec(Path, instance=True, spec_set=True)
    path_obj.exists.return_value = True
    path_obj.is_dir.return_value = True

    entry = mocker.Mock()
    entry.name = "file.txt"
    path_obj.iterdir.return_value = [entry]

    fake_pathlib_path_class.return_value = path_obj

    # Act
    result = service.ls("/fake/dir")

    # Assert
    fake_pathlib_path_class.assert_called_once_with("/fake/dir")
    path_obj.exists.assert_called_once_with()
    path_obj.is_dir.assert_called_once_with()
    path_obj.iterdir.assert_called_once_with()
    assert result == ["file.txt\n"]
