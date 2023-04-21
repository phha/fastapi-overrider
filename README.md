# fastapi-overrider

Easy and safe dependency overrides for your [FastAPI](https://fastapi.tiangolo.com/) tests. 

## Installation

`pip install fastapi-overrider`

## Usage

Use it as pytest fixture to ensure every test is run with a clean set of overrides:

```python
@pytest.fixture(scope="function")
def override(app: FastAPI):
    with Overrider(app) as override:
        yield override

def test_get_item(client: TestClient, override: Overrider):
    override.value(dependencies.retrieve_items, ["Foo"])
    response = client.get("/item/0")
    assert response.text == "Foo"
```

Alternatively use it as a context manager:

```python
def test_get_item(client: TestClient, app: FastAPI):
    with Overrider(app) as override:
        override.value(dependencies.retrieve_items, ["Foo"])
        response = client.get("/item/0")
        assert response.text == "Foo"
```

In both cases the overrides will be cleaned up after the test.

The above examples also show how to override a dependency with just the desired return
value. Overrider will take care of creating a matching wrapper function and setting it
as an override.

`override.value()` returns the override value:

```python
def test_get_content(client: TestClient, override: Overrider):
    override.value(dependencies.retrieve_items, SomeModel()).content = "Foo"
    response = client.get("/content/")
    assert response.text == "Foo"
```

```python
def test_get_content(client: TestClient, override: Overrider):
    model = override.value(dependencies.retrieve_items, SomeModel())
    model.id = 0
    model.text = "Foo"
    response = client.get("/content/")
    assert response.text == "0: Foo"
```

`override.function()` accepts a callable`:

```python
def test_get_item(client: TestClient, override: Overrider):
    def override_retrieve_item(id: int):
        return f"{id}: Foo"
    override.function(dependencies.retrieve_items, override_retrieve_item)
    response = client.get("/item/0")
    assert response.text == "0: Foo"
```

Use it as a drop-in replacement for `app.dependency_overrides`:

```python
def test_get_item(client: TestClient, override: Overrider):
    def override_retrieve_item(id: int):
        return f"{id}: Foo"
    override[dependencies.retrieve_items] = override_retrieve_item
    response = client.get("/item/0")
    assert response.text == "0: Foo"
```

Overrider can create mocks for you:

```python
def test_get_item(client: TestClient, override: Overrider):
    mock_retriever = override.mock(dependencies.retrieve_items)
    mock_retriever.return_value = "Foo"
    response = client.get("/item/0")

    mock_retriever.assert_called_with(0)
    assert response.text == "Foo"
```

Reuse common overrides:

```python
@pytest.fixture(scope="function")
def as_dave(app: FastAPI):
    with Overrider(app) as override:
        mock_user = override,mock(dependencies.get_user)
        mock_user.name = "Dave"
        yield override

def test_get_greeting(client: TestClient, as_dave: Overrider):
    response = client.get("/")
    assert response.text == "Good morning, Dave"
```

Extend it with your own convenience methods:

```python
class MyOverrider(Overrider):
    def user(self, username: str, uid: str, authenticated: bool = False):
        mock_user = self.mock(dependencies.get_user)
        mock_user.username = username
        mock_user.uid = uid
        mock_user.authenticate.return_value = authenticated

@pytest.fixture(scope="function")
def override(app: FastAPI):
    with MyOverrider(app) as override:
        yield override
```
