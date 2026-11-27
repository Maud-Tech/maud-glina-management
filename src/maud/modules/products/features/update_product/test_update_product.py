from datetime import date
from typing import Any

import pytest

from maud.modules.products.features.change_product_status.handler import (
    ChangeProductStatusCommand,
)
from maud.modules.products.features.change_product_status.handler import (
    execute as change_status,
)
from maud.modules.products.features.update_product.handler import UpdateProductCommand, execute
from maud.modules.products.models import ProductChange
from maud.modules.products.responses import MandateResponse, PolicyResponse, ProductResponse
from maud.shared.errors import DomainError

pytestmark = pytest.mark.django_db


def command(actor: Any, product: ProductResponse, **changes: Any) -> UpdateProductCommand:
    fields: dict[str, Any] = {
        "actor_id": actor.id,
        "product_id": product.id,
        "code": product.code,
        "name": product.name,
        "base_currency": product.base_currency,
        "description": product.description,
    }
    fields.update(changes)
    return UpdateProductCommand(**fields)


def test_changes_are_recorded_with_before_and_after_and_reason(
    actor: Any, product: ProductResponse
) -> None:
    updated = execute(
        command(
            actor, product, name="Glina USD Moderado", launch_date=date(2027, 1, 4), reason="ajuste"
        )
    )

    assert updated.name == "Glina USD Moderado"
    change = ProductChange.objects.filter(action="UPDATED").get()
    assert change.changes == {
        "launch_date": [None, "2027-01-04"],
        "name": ["Glina USD Conservador", "Glina USD Moderado"],
    }
    assert change.reason == "ajuste"


def test_saving_without_changes_records_nothing(actor: Any, product: ProductResponse) -> None:
    execute(command(actor, product))

    assert not ProductChange.objects.filter(action="UPDATED").exists()


def test_base_currency_can_change_in_draft_without_policy(
    actor: Any, product: ProductResponse, eur: Any
) -> None:
    assert execute(command(actor, product, base_currency="EUR")).base_currency == "EUR"


def test_base_currency_cannot_change_once_policy_exists(
    actor: Any, product: ProductResponse, policy: PolicyResponse, eur: Any
) -> None:
    with pytest.raises(DomainError) as error:
        execute(command(actor, product, base_currency="EUR"))

    assert error.value.code == "product_currency_has_policy"


def test_code_cannot_change_after_draft(
    actor: Any,
    product: ProductResponse,
    policy: PolicyResponse,
    published_mandate: MandateResponse,
) -> None:
    change_status(
        ChangeProductStatusCommand(actor_id=actor.id, product_id=product.id, status="ACTIVE")
    )

    with pytest.raises(DomainError) as error:
        execute(command(actor, product, code="NOVO-CODIGO"))

    assert error.value.code == "product_code_locked"


def test_closed_product_cannot_be_updated(actor: Any, product: ProductResponse) -> None:
    change_status(
        ChangeProductStatusCommand(actor_id=actor.id, product_id=product.id, status="CLOSED")
    )

    with pytest.raises(DomainError) as error:
        execute(command(actor, product, name="Outro nome"))

    assert error.value.code == "product_closed"
