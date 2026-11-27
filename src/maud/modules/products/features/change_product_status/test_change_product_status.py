from datetime import timedelta
from typing import Any

import pytest

from maud.modules.products.features.change_product_status.handler import (
    ChangeProductStatusCommand,
    execute,
)
from maud.modules.products.features.update_policy.handler import UpdatePolicyCommand
from maud.modules.products.features.update_policy.handler import execute as update_policy
from maud.modules.products.models import Product, ProductChange
from maud.modules.products.responses import MandateResponse, PolicyResponse, ProductResponse
from maud.modules.products.testing import TODAY
from maud.shared.errors import DomainError

pytestmark = pytest.mark.django_db


def change(actor: Any, product: ProductResponse, status: str, reason: str = "") -> ProductResponse:
    return execute(
        ChangeProductStatusCommand(
            actor_id=actor.id, product_id=product.id, status=status, reason=reason
        )
    )


def test_activation_without_published_mandate_is_rejected(
    actor: Any, product: ProductResponse, policy: PolicyResponse
) -> None:
    with pytest.raises(DomainError) as error:
        change(actor, product, "ACTIVE")

    assert error.value.code == "product_activation_requires_published_mandate"
    assert Product.objects.get().status == "DRAFT"


def test_activation_without_policy_is_rejected(
    actor: Any, product: ProductResponse, published_mandate: MandateResponse
) -> None:
    with pytest.raises(DomainError) as error:
        change(actor, product, "ACTIVE")

    assert error.value.code == "product_activation_requires_effective_policy"


def test_activation_with_policy_not_yet_effective_is_rejected(
    actor: Any,
    product: ProductResponse,
    policy: PolicyResponse,
    published_mandate: MandateResponse,
    insurer: Any,
) -> None:
    update_policy(
        UpdatePolicyCommand(
            actor_id=actor.id,
            policy_id=policy.id,
            policy_number=policy.policy_number,
            insurer_entity_id=insurer.id,
            effective_from=TODAY + timedelta(days=1),
        )
    )

    with pytest.raises(DomainError) as error:
        change(actor, product, "ACTIVE")

    assert error.value.code == "product_activation_requires_effective_policy"


def test_product_with_published_mandate_and_effective_policy_is_activated(
    actor: Any, product: ProductResponse, policy: PolicyResponse, published_mandate: MandateResponse
) -> None:
    assert change(actor, product, "ACTIVE", reason="lançamento").status == "ACTIVE"

    history = ProductChange.objects.get(action="STATUS_CHANGED")
    assert history.changes == {"status": ["DRAFT", "ACTIVE"]}
    assert history.reason == "lançamento"


def test_active_product_goes_inactive_and_back(
    actor: Any, product: ProductResponse, policy: PolicyResponse, published_mandate: MandateResponse
) -> None:
    change(actor, product, "ACTIVE")

    assert change(actor, product, "INACTIVE").status == "INACTIVE"
    assert change(actor, product, "ACTIVE").status == "ACTIVE"


def test_expired_cannot_be_chosen_on_screen(
    actor: Any, product: ProductResponse, policy: PolicyResponse, published_mandate: MandateResponse
) -> None:
    change(actor, product, "ACTIVE")

    with pytest.raises(DomainError) as error:
        change(actor, product, "EXPIRED")

    assert error.value.code == "product_status_change_not_allowed"


def test_closed_product_cannot_change_status(actor: Any, product: ProductResponse) -> None:
    change(actor, product, "CLOSED")

    with pytest.raises(DomainError) as error:
        change(actor, product, "ACTIVE")

    assert error.value.code == "product_status_change_not_allowed"


def test_unknown_status_is_rejected(actor: Any, product: ProductResponse) -> None:
    with pytest.raises(DomainError) as error:
        change(actor, product, "PAUSED")

    assert error.value.code == "product_status_unknown"
