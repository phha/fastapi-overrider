from collections.abc import Iterator

import pytest
from fastapi import FastAPI

from fastapi_overrider import Overrider


@pytest.mark.anyio()
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_beanie(override: Overrider) -> None:
    # given
    from beanie import Document, init_beanie
    from mongomock_motor import AsyncMongoMockClient

    class Item(Document):
        name: str

    def get() -> Item:
        ...

    client = AsyncMongoMockClient()
    await init_beanie(database=client.get_database("db"), document_models=[Item])

    # when
    item = override.some(get)

    # then
    assert isinstance(item, Document)


def test_odmantic(override: Overrider) -> None:
    # given
    from odmantic import Model

    class Item(Model):
        name: str

    def get() -> Item:
        ...

    # when
    item = override.some(get)

    # then
    assert isinstance(item, Model)


def test_msgspec(override: Overrider) -> None:
    # given
    from msgspec import Struct

    class Item(Struct):
        name: str

    def get() -> Item:
        ...

    # when
    item = override.some(get)

    # then
    assert isinstance(item, Struct)


def test_sqlalchemy(override: Overrider) -> None:
    # given
    from sqlalchemy import Column, Integer
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass

    class Item(Base):
        __tablename__ = "items"
        item_id = Column(Integer, primary_key=True)

    def get() -> Item:
        ...

    # when
    item = override.some(get)

    # then
    assert isinstance(item, Base)


def test_pydantic(override: Overrider) -> None:
    # given
    from pydantic import BaseModel

    class Item(BaseModel):
        name: str

    def get() -> Item:
        ...

    # when
    item = override.some(get)

    # then
    assert isinstance(item, BaseModel)


def test_dataclass(override: Overrider) -> None:
    # given
    from dataclasses import asdict, dataclass

    @dataclass
    class Item:
        name: str

    def get() -> Item:
        ...

    # when
    item = override.some(get)

    # then
    assert "name" in asdict(item)


def test_typeddict(override: Overrider) -> None:
    # given
    from typing import TypedDict

    class Item(TypedDict):
        name: str

    def get() -> Item:
        ...

    # when
    item = override.some(get)

    # then
    assert "name" in item


def test_attrs(override: Overrider) -> None:
    # given
    from attrs import asdict, define

    @define
    class Item:
        name: str

    def get() -> Item:
        ...

    # when
    item = override.some(get)

    # then
    assert "name" in asdict(item)


@pytest.fixture()
def override() -> Iterator[Overrider]:
    app = FastAPI()
    with Overrider(app) as override:
        yield override


@pytest.fixture()
def anyio_backend() -> str:
    return "asyncio"
