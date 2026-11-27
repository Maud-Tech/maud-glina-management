from typing import Any

import pytest

from maud.modules.products.features.create_product.handler import CreateProductCommand, execute
from maud.modules.products.models import Product, ProductChange
from maud.shared.errors import ConflictError, DomainError

pytestmark = pytest.mark.django_db


def test_product_is_created_as_draft_in_usd(actor: Any, usd: Any) -> None:
    """Sem moeda informada, o produto nasce em USD e em rascunho."""
    product = execute(
        CreateProductCommand(actor_id=actor.id, code=" glina-usd-01", name=" Glina  USD ")
    )

    assert product.code == "GLINA-USD-01"
    assert product.name == "Glina USD"
    assert product.base_currency == "USD"
    assert product.status == "DRAFT"


def test_creation_is_recorded_in_history_with_author(actor: Any, usd: Any) -> None:
    product = execute(CreateProductCommand(actor_id=actor.id, code="P1", name="Produto"))

    change = ProductChange.objects.get()
    assert change.object_type == "PRODUCT"
    assert change.object_id == product.id
    assert change.action == "CREATED"
    assert change.changes["code"] == [None, "P1"]
    assert change.changed_by == actor


def test_duplicate_product_code_is_rejected(actor: Any, usd: Any) -> None:
    execute(CreateProductCommand(actor_id=actor.id, code="P1", name="Produto"))

    with pytest.raises(ConflictError) as error:
        execute(CreateProductCommand(actor_id=actor.id, code="p1", name="Outro"))

    assert error.value.code == "product_code_taken"
    assert Product.objects.count() == 1


def test_unregistered_currency_is_rejected(actor: Any, usd: Any) -> None:
    with pytest.raises(DomainError) as error:
        execute(
            CreateProductCommand(actor_id=actor.id, code="P1", name="Produto", base_currency="JPY")
        )

    assert error.value.code == "currency_not_found"
    assert not Product.objects.exists()
