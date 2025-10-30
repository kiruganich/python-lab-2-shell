"""
conftest.py — это файл, где хранятся общие фикстуры.

Он автоматически подхватывается pytest (его не нужно импортировать).

Если conftest.py положить в корне tests/, то все тесты в этой папке смогут использовать объявленные там фикстуры.
"""

from logging import Logger
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from src.services.macos_console import MacOSConsoleService


"""
Fixture — это функция, которая подготавливает контекст для теста:
создаёт объект, настраивает окружение, делает моки, создает временные файлы и т.п.

Фикстура вызывается автоматически, достаточно просто указать её имя в параметрах теста.
"""


@pytest.fixture
def logger(mocker: MockerFixture) -> Logger:
    return mocker.Mock()


@pytest.fixture
def service(logger: Logger):
    return MacOSConsoleService(logger)


@pytest.fixture
def fake_pathlib_path_class(mocker: MockerFixture) -> Mock:
    mock_path_cls = mocker.patch("src.services.macos_console.Path")
    return mock_path_cls
