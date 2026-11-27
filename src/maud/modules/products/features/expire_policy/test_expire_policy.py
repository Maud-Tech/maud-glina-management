from typing import Any

import pytest

from maud.modules.products.features.change_product_status.handler import (
    ChangeProductStatusCommand,
)
from maud.modules.products.features.change_product_status.handler import (
    execute as change_status,
)
from maud.modules.products.features.expire_policy.handler import ExpirePolicyCommand, execute
from maud.modules.products.models import Product, ProductChange
from maud.modules.products.responses import MandateResponse, PolicyResponse, ProductResponse
from maud.shared.errors import DomainError

pytestmark = pytest.mark.django_db


def test_expiring_policy_expires_active_product(
    actor: Any, product: ProductResponse, policy: PolicyResponse, published_mandate: MandateResponse
) -> None:
    change_status(
        ChangeProductStatusCommand(actor_id=actor.id, product_id=product.id, status="ACTIVE")
    )

    expired = execute(ExpirePolicyCommand(actor_id=actor.id, policy_id=policy.id, reason="fim"))

    assert expired.status == "EXPIRED"
    assert Product.objects.get().status == "EXPIRED"
    product_change = ProductChange.objects.get(
        object_type="PRODUCT", action="STATUS_CHANGED", reason__startswith="Apólice"
    )
    assert product_change.changes == {"status": ["ACTIVE", "EXPIRED"]}
    assert product_change.reason == "Apólice AP-0001 expirada. fim"


def test_draft_product_stays_draft_when_policy_expires(
    actor: Any, product: ProductResponse, policy: PolicyResponse
) -> None:
    execute(ExpirePolicyCommand(actor_id=actor.id, policy_id=policy.id))

    assert Product.objects.get().status == "DRAFT"
    assert not ProductChange.objects.filter(object_type="PRODUCT", action="STATUS_CHANGED").exists()


def test_expiring_twice_is_rejected(actor: Any, policy: PolicyResponse) -> None:
    execute(ExpirePolicyCommand(actor_id=actor.id, policy_id=policy.id))

    with pytest.raises(DomainError) as error:
        execute(ExpirePolicyCommand(actor_id=actor.id, policy_id=policy.id))

    assert error.value.code == "policy_already_expired"


def test_expired_product_can_only_be_closed(
    actor: Any, product: ProductResponse, policy: PolicyResponse, published_mandate: MandateResponse
) -> None:
    change_status(
        ChangeProductStatusCommand(actor_id=actor.id, product_id=product.id, status="ACTIVE")
    )
    execute(ExpirePolicyCommand(actor_id=actor.id, policy_id=policy.id))

    with pytest.raises(DomainError) as error:
        change_status(
            ChangeProductStatusCommand(actor_id=actor.id, product_id=product.id, status="ACTIVE")
        )
    assert error.value.code == "product_status_change_not_allowed"

    closed = change_status(
        ChangeProductStatusCommand(actor_id=actor.id, product_id=product.id, status="CLOSED")
    )
    assert closed.status == "CLOSED"
