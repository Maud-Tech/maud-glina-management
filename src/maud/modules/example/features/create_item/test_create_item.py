import pytest

from maud.modules.example.models import Item
from maud.shared.models import OutboxEvent
from maud.shared.testing import ApiClient

pytestmark = pytest.mark.django_db


def test_creates_with_normalized_name_and_publishes_event(api: ApiClient) -> None:
    response = api.post("/example/items", {"name": "  Item   A "})

    assert response.status_code == 201
    assert response.json()["name"] == "Item A"
    assert Item.objects.get().name == "Item A"

    event = OutboxEvent.objects.get()
    assert event.event_type == "example.item_created"
    assert event.payload["item_id"] == response.json()["id"]


def test_repeating_request_with_same_key_does_not_duplicate(api: ApiClient) -> None:
    first = api.post("/example/items", {"name": "Item A"}, idempotency_key="pedido-1")
    repeated = api.post("/example/items", {"name": "Item A"}, idempotency_key="pedido-1")

    assert repeated.status_code == 201
    assert repeated.json() == first.json()
    assert Item.objects.count() == 1
    assert OutboxEvent.objects.count() == 1


def test_existing_name_is_rejected_with_409(api: ApiClient) -> None:
    api.post("/example/items", {"name": "Item A"}, idempotency_key="pedido-1")

    response = api.post("/example/items", {"name": "item a"}, idempotency_key="pedido-2")

    assert response.status_code == 409
    assert response.json()["code"] == "item_already_exists"


def test_empty_name_is_rejected_with_422(api: ApiClient) -> None:
    response = api.post("/example/items", {"name": "   "})

    assert response.status_code == 422
    assert response.json()["code"] == "item_name_required"
    assert not Item.objects.exists()


def test_request_without_api_key_is_rejected_with_401(api: ApiClient) -> None:
    response = api.post("/example/items", {"name": "Item A"}, api_key=None)

    assert response.status_code == 401
