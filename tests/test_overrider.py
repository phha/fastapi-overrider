from collections.abc import Callable, Generator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI

from fastapi_overrider import Overrider

DepType = Callable[[], str]


def test_context_manager(app: FastAPI, get_foo: DepType, get_bar: DepType) -> None:
    # given
    app.dependency_overrides[get_foo] = get_foo

    # when
    with Overrider(app) as override:
        override[get_foo] = get_bar

    # then
    assert app.dependency_overrides[get_foo] == get_foo


def test_setitem(app: FastAPI, overrider: Overrider, get_foo: DepType) -> None:
    # when
    overrider[get_foo] = get_foo

    # then
    app.dependency_overrides[get_foo] = get_foo


def test_value(app: FastAPI, overrider: Overrider, get_foo: DepType) -> None:
    # given
    bar = "Bar"

    # when
    overrider.value(get_foo, bar)

    # then
    assert app.dependency_overrides[get_foo]() == bar


def test_function(
    app: FastAPI, overrider: Overrider, get_foo: DepType, get_bar: DepType
) -> None:
    # given
    bar = "Bar"

    # when
    overrider.function(get_foo, get_bar)

    # then
    assert app.dependency_overrides[get_foo]() == bar


def test_mock(app: FastAPI, overrider: Overrider, get_foo: DepType) -> None:
    # when
    mock = overrider.mock(get_foo)

    # then
    assert app.dependency_overrides[get_foo](0) == mock(0)
    assert app.dependency_overrides[get_foo] == mock
    mock.assert_called_with(0)


def test_mock_strict_by_default(overrider: Overrider, get_foo: DepType) -> None:
    # when
    with pytest.raises(AttributeError):
        overrider.mock(get_foo).bar = 0

    # then raise AttributeError


def test_mock_strict(overrider: Overrider, get_foo: DepType) -> None:
    # when
    with pytest.raises(AttributeError):
        overrider.mock(get_foo, strict=True).bar = 0

    # then raise AttributeError


def test_mock_not_strict(overrider: Overrider, get_foo: DepType) -> None:
    # when
    mock = overrider.mock(get_foo, strict=False)
    mock.bar = 0

    # then
    assert mock.bar == 0


def test_mock_call_strict_by_default(overrider: Overrider, get_foo: DepType) -> None:
    # when
    with pytest.raises(AttributeError):
        overrider.mock(get_foo).bar = 0

    # then raise AttributeError


def test_mock_call_strict(overrider: Overrider, get_foo: DepType) -> None:
    # when
    with pytest.raises(AttributeError):
        overrider(get_foo, strict=True).bar = 0

    # then raise AttributeError


def test_mock_call_not_strict(overrider: Overrider, get_foo: DepType) -> None:
    # when
    mock = overrider(get_foo, strict=False)
    mock.return_value.bar = 0

    # then
    assert isinstance(mock, MagicMock)
    assert mock().bar == 0


def test_value_call(app: FastAPI, overrider: Overrider, get_foo: DepType) -> None:
    # given
    bar = "Bar"

    # when
    mock = overrider(get_foo, bar)

    # then
    assert app.dependency_overrides[get_foo]() == bar
    assert mock == bar


def test_function_call(
    app: FastAPI, overrider: Overrider, get_foo: DepType, get_bar: DepType
) -> None:
    # given
    bar = "Bar"

    # when
    mock = overrider(get_foo, get_bar)

    # then
    assert app.dependency_overrides[get_foo]() == bar
    assert mock == get_bar


def test_spy(app: FastAPI, overrider: Overrider, get_foo: DepType) -> None:
    # when
    spy = overrider.spy(get_foo)

    # then
    assert app.dependency_overrides[get_foo]() == "Foo"
    spy.assert_called_once()


@pytest.fixture()
def app() -> FastAPI:
    return FastAPI()


@pytest.fixture()
def overrider(app: FastAPI) -> Generator[Overrider, None, None]:
    with Overrider(app) as overrider:
        yield overrider


@pytest.fixture()
def get_foo() -> DepType:
    def inner_get_foo() -> str:
        return "Foo"

    return inner_get_foo


@pytest.fixture()
def get_bar() -> DepType:
    def inner_get_bar() -> str:
        return "Bar"

    return inner_get_bar
