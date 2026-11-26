import pytest

from maud.modules.example.models import Item
from maud.shared.testing import ApiClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def three_items() -> None:
    Item.objects.create(name="Item B")
    Item.objects.create(name="Item A")
    Item.objects.create(name="Antigo", is_active=False)


def names_in(response: object) -> list[str]:
    return [item["name"] for item in response.json()]  # type: ignore[attr-defined]


@pytest.mark.usefixtures("three_items")
def test_lists_only_active_in_alphabetical_order(api: ApiClient) -> None:
    response = api.get("/example/items")

    assert response.status_code == 200
    assert names_in(response) == ["Item A", "Item B"]


@pytest.mark.usefixtures("three_items")
def test_includes_inactive_when_requested(api: ApiClient) -> None:
    response = api.get("/example/items", {"include_inactive": "true"})

    assert len(response.json()) == 3


@pytest.mark.usefixtures("three_items")
def test_searches_by_name_fragment_case_insensitively(api: ApiClient) -> None:
    response = api.get("/example/items", {"search": "  item   b "})

    assert names_in(response) == ["Item B"]
