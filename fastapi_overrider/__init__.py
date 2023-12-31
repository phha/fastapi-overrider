import asyncio
import inspect
from collections import UserDict
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, Self, TypeVar, overload
from unittest.mock import MagicMock, create_autospec, seal

from fastapi import FastAPI
from fastapi.dependencies.utils import is_coroutine_callable

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
    def __call__(self, key: _DepType) -> MagicMock:
        """Override a dependnecy with a mock value.
        Returns the mock value"""
        ...

    def __call__(self, *args, **kwargs) -> _DepType | MagicMock | object:
        """Override a dependency either with a function, a value or a mock."""
        match args:
            case [key] if isinstance(key, Callable) and (
                list(kwargs.keys()) == ["strict"] or len(kwargs) == 0
            ):
                return self.mock(key)
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

    def mock(self, key: _DepType) -> MagicMock:
        """Override a dependnecy with a mock value.
        Returns a mock function that returns a mock value"""
        value_name = f"mock value for {key.__name__}"
        function_name = f"mock function for {key.__name__}"
        return_type = inspect.get_annotations(key)["return"]
        return_value = create_autospec(
            return_type,
            instance=True,
            unsafe=False,
            name=value_name,
        )

        mock_func = MagicMock(unsafe=False, name=function_name)
        mock_func.__signature__ = inspect.signature(key)
        mock_func.return_value = return_value
        seal(mock_func)
        self[key] = mock_func
        return mock_func

    def spy(self, key: _DepType) -> MagicMock:
        """Replace a dependency with a spy wrapper.
        Returns the spy"""
        spy_name = f"Spy for {key.__name__}"

        def wrapper(*args, **kwargs) -> Any:  # noqa: ANN002,ANN003,ANN401
            if is_coroutine_callable(key):
                return asyncio.run(key(*args, **kwargs))
            return key(*args, **kwargs)

        spy = MagicMock(wraps=key, unsafe=False, name=spy_name)
        spy.__signature__ = inspect.signature(key)
        spy.side_effect = wrapper
        seal(spy)
        self[key] = spy
        return spy

    def __enter__(self: Self) -> Self:
        self._restore_overrides = self._app.dependency_overrides
        self._app.dependency_overrides = self._restore_overrides.copy()
        self.data = self._app.dependency_overrides
        return self

    def __exit__(self, *_: object) -> None:
        self._app.dependency_overrides = self._restore_overrides
