import inspect
from collections import UserDict
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, Self, TypeVar, overload
from unittest.mock import MagicMock, create_autospec

from fastapi import FastAPI

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

    @overload
    def __call__(self, key: _DepType, override: _DepType) -> _DepType:
        """Override a dependency with the given function.
        Returns the function"""
        ...

    @overload
    def __call__(self, key: _DepType, override: _T) -> _T:
        """Override a dependeny with a function returning the given value.
        Returns the value"""
        ...

    @overload
    def __call__(self, key: _DepType, *, strict: bool = True) -> MagicMock:
        """Override a dependnecy with a mock value.
        Returns the mock value"""
        ...

    def __call__(self, *args, **kwargs) -> _DepType | MagicMock | object:
        """Override a dependency either with a function, a value or a mock."""
        match args:
            case [key] if isinstance(key, Callable) and (
                list(kwargs.keys()) == ["strict"] or len(kwargs) == 0
            ):
                return self.mock(key, strict=kwargs.get("strict", True))
            case [key, override] if isinstance(key, Callable) and isinstance(
                override, Callable
            ):
                return self.function(key, override)
            case [key, override] if isinstance(key, Callable):
                return self.value(key, override)
            case _:
                raise NotImplementedError

    def function(self, key: _DepType, override: _DepType) -> _DepType:
        """Override a dependency with the given function.
        Returns the function"""
        self[key] = override
        return override

    def value(self, key: _DepType, override: _T) -> _T:
        """Override a dependeny with a function returning the given value.
        Returns the value"""

        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:  # noqa: ARG001
            return override

        self[key] = wraps(key)(wrapper)
        return override

    def mock(self, key: _DepType, *, strict: bool = True) -> MagicMock:
        """Override a dependnecy with a mock value.
        Returns a mock function that returns a mock value"""
        value_name = f"mock value for {key.__name__}"
        function_name = f"mock function for {key.__name__}"
        return_type = inspect.get_annotations(key)["return"]
        return_value = (
            create_autospec(
                return_type, instance=True, spec_set=True, unsafe=False, name=value_name
            )
            if strict
            else (MagicMock(name=value_name))
        )

        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> MagicMock:  # noqa: ARG001
            return return_value

        self[key] = (
            MagicMock(wraps=wrapper, spec_set=True, unsafe=False, name=function_name)
            if strict
            else MagicMock(wraps=wrapper, name=function_name)
        )
        return self[key]

    def __enter__(self: Self) -> Self:
        self._restore_overrides = self._app.dependency_overrides
        self._app.dependency_overrides = self._restore_overrides.copy()
        self.data = self._app.dependency_overrides
        return self

    def __exit__(self, *_: object) -> None:
        self._app.dependency_overrides = self._restore_overrides
