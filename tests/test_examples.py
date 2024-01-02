from collections.abc import Iterator
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from fastapi_overrider import Overrider

items = {
    0: {
        "name": "Foo",
    },
    1: {
        "name": "Bar",
    },
}


class Item(BaseModel):
    item_id: int
    name: str


class User(BaseModel):
    name: str
    authenticated: bool = False


class MyOverrider(Overrider):
    def user(self, *, name: str, authenticated: bool = False) -> None:
        self(get_user, User(name=name, authenticated=authenticated))


async def lookup_item(item_id: int) -> Item:
    item = items[item_id]
    return Item(item_id=item_id, **item)


def get_user() -> User:
    return User(name="Frank")


async def get_time_of_day() -> str:
    return "evening"


# example: Override with value
def test_get_item(client: TestClient, override: Overrider) -> None:
    override_item = Item(item_id=0, name="Bar")
    override.value(lookup_item, override_item)

    response = client.get("/item/0").json()

    assert Item(**response) == override_item


# example: use as context manager
def test_get_item_context_manager(client: TestClient, app: FastAPI) -> None:
    with Overrider(app) as override:
        override_item = Item(item_id=0, name="Bar")
        override.value(lookup_item, override_item)

        response = client.get("/item/0").json()

        assert Item(**response) == override_item


# example: `override.value()` returns the override value
def test_get_item_return_value(client: TestClient, override: Overrider) -> None:
    item = override.value(lookup_item, Item(item_id=0, name="Bar"))

    response = client.get("/item/0").json()

    assert Item(**response) == item


# example: override with a callable
def test_get_item_function(client: TestClient, override: Overrider) -> None:
    item = Item(item_id=0, name="Bar")
    override.function(lookup_item, lambda item_id: item)  # noqa: ARG005

    response = client.get("/item/0").json()

    assert Item(**response) == item


# example: drop-in replacement
def test_get_item_drop_in(client: TestClient, override: Overrider) -> None:
    item = Item(item_id=0, name="Bar")

    def override_lookup_item(item_id: int) -> Item:  # noqa: ARG001
        return item

    override[lookup_item] = override_lookup_item

    response = client.get("/item/0").json()

    assert Item(**response) == item


# example: override with mock
def test_get_item_mock(client: TestClient, override: Overrider) -> None:
    item = Item(item_id=0, name="Bar")
    mock_lookup = override.mock(lookup_item)
    mock_lookup.return_value = item

    response = client.get("/item/0")

    mock_lookup.assert_called_once_with(item_id=0)
    assert Item(**response.json()) == item


# example: spy on a dependency
def test_get_item_spy(client: TestClient, override: Overrider) -> None:
    spy = override.spy(lookup_item)

    client.get("/item/0")

    spy.assert_called_with(item_id=0)


# example: directly set a callable
def test_get_item_call_callable(client: TestClient, override: Overrider) -> None:
    item = Item(item_id=0, name="Bar")
    override(lookup_item, lambda item_id: item)  # noqa: ARG005

    response = client.get("/item/0").json()

    assert Item(**response) == item


# example: directly set a value
def test_get_item_call_value(client: TestClient, override: Overrider) -> None:
    item = override(lookup_item, Item(item_id=0, name="Bar"))

    response = client.get("/item/0").json()

    assert Item(**response) == item


# example: directly create a mock
def test_get_item_call_mock(client: TestClient, override: Overrider) -> None:
    item = Item(item_id=0, name="Bar")
    mock_lookup = override(lookup_item)
    mock_lookup.return_value = item

    response = client.get("/item/0")

    mock_lookup.assert_called_once_with(item_id=0)
    assert Item(**response.json()) == item


# example: reusable overrides
def test_get_greeting(
    client: TestClient,
    as_dave: Overrider,  # noqa: ARG001
    in_the_morning: Overrider,  # noqa: ARG001
) -> None:
    response = client.get("/")

    assert response.text == '"Good morning, Dave."'


# example: convenience methods
def test_open_pod_bay_doors(client: TestClient, my_override: MyOverrider) -> None:
    my_override.user(name="Dave", authenticated=False)

    response = client.get("/open/pod_bay_doors")

    assert response.text == "\"I'm afraid I can't let you do that, Dave.\""


# example polyfactory
def test_get_some_item(client: TestClient, override: Overrider) -> None:
    item = override.some(lookup_item, name="Foo")

    response = client.get(f"/item/{item.item_id}")

    assert item.name == "Foo"
    assert item == Item(**response.json())


def test_get_five_items(client: TestClient, override: Overrider) -> None:
    items = override.batch(lookup_item, 5)

    for item in items:
        response = client.get(f"/item/{item.item_id}")
        assert item == Item(**response.json())


def test_cover_get_items(client: TestClient, override: Overrider) -> None:
    items = override.cover(lookup_item)

    for item in items:
        response = client.get(f"/item/{item.item_id}")
        assert item == Item(**response.json())


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture()
def override(app: FastAPI) -> Iterator[Overrider]:
    with Overrider(app) as override:
        yield override


@pytest.fixture()
def app() -> FastAPI:
    app = FastAPI()

    @app.get("/item/{item_id}")
    async def get_item(lookup: Annotated[Item, Depends(lookup_item)]) -> Item:
        return lookup

    @app.get("/")
    async def greet(
        user: Annotated[User, Depends(get_user)],
        time_of_day: Annotated[str, Depends(get_time_of_day)],
    ) -> str:
        return f"Good {time_of_day}, {user.name}."

    @app.get("/open/pod_bay_doors")
    def open_pod_bay_doors(user: Annotated[User, Depends(get_user)]) -> str:
        if user.authenticated:
            return f"OK, {user.name}"
        return f"I'm afraid I can't let you do that, {user.name}."

    return app


@pytest.fixture()
def as_dave(app: FastAPI) -> Iterator[Overrider]:
    with Overrider(app) as override:
        override(get_user, User(name="Dave", authenticated=True))
        yield override


@pytest.fixture()
def in_the_morning(app: FastAPI) -> Iterator[Overrider]:
    with Overrider(app) as override:
        override(get_time_of_day, "morning")
        yield override


@pytest.fixture()
def my_override(app: FastAPI) -> Iterator["MyOverrider"]:
    with MyOverrider(app) as override:
        yield override
