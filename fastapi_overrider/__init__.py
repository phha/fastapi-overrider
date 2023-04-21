import inspect

from collections import UserDict
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar
from unittest.mock import MagicMock, create_autospec

from fastapi import FastAPI
from typing_extensions import Self

_T = TypeVar("_T")
_P = ParamSpec("_P")

_DepType = Callable[_P, _T]


class Overrider(UserDict):
    """Set dependency overrides and clean the up after using.
    To be used as a pytest fixture."""

    def __init__(
        self,
        app: FastAPI,
    ) -> None:
        self._app = app

    def function(self, key: _DepType, override: _DepType) -> _DepType:
        """Override a dependency with the given function.
        Returns the function"""
        self[key] = override
        return override

    def value(self, key: _DepType, override: _T) -> _T:
        """Override a dependeny with a function returning the given value.
        Returns the value"""

        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            return override

        self[key] = wraps(key)(wrapper)
        return override

    def mock(self, key: _DepType, strict=True) -> MagicMock:
        """Override a dependnecy with a mock.
        Returns the mock"""
        name = f"mock for {key}"
        return_type = inspect.get_annotations(key)["return"]
        return_value = (
            create_autospec(
                return_type, instance=True, spec_set=True, unsafe=False, name=name
            )
            if strict
            else (MagicMock(name=name))
        )
        return self.value(key, return_value)

    def __enter__(self: Self) -> Self:
        self._restore_overrides = self._app.dependency_overrides
        self._app.dependency_overrides = self._restore_overrides.copy()
        self.data = self._app.dependency_overrides
        return self

    def __exit__(self, *_: Any) -> None:
        self._app.dependency_overrides = self._restore_overrides
