from datetime import timedelta
from typing import Any

import pytest

from maud.modules.products.features.create_product.handler import CreateProductCommand
from maud.modules.products.features.create_product.handler import execute as create_product
from maud.modules.products.features.register_policy.handler import RegisterPolicyCommand, execute
from maud.modules.products.models import Policy, ProductChange
from maud.modules.products.responses import PolicyResponse, ProductResponse
from maud.modules.products.testing import TODAY
from maud.shared.errors import ConflictError, DomainError

pytestmark = pytest.mark.django_db


def command(
    actor: Any, product: ProductResponse, insurer: Any, **changes: Any
) -> RegisterPolicyCommand:
    fields: dict[str, Any] = {
        "actor_id": actor.id,
        "product_id": product.id,
        "policy_number": "AP-0001",
        "insurer_entity_id": insurer.id,
        "effective_from": TODAY,
    }
    fields.update(changes)
    return RegisterPolicyCommand(**fields)


def test_policy_is_active_in_product_base_currency(
    actor: Any, product: ProductResponse, insurer: Any
) -> None:
    policy = execute(command(actor, product, insurer, policy_number=" AP-0001 "))

    assert policy.policy_number == "AP-0001"
    assert policy.currency == "USD"
    assert policy.status == "ACTIVE"
    assert ProductChange.objects.filter(object_type="POLICY", action="CREATED").count() == 1


def test_policy_insurer_must_be_a_company(
    actor: Any, product: ProductResponse, person: Any
) -> None:
    with pytest.raises(DomainError) as error:
        execute(command(actor, product, person))

    assert error.value.code == "insurer_must_be_company"
    assert not Policy.objects.exists()


def test_second_policy_for_same_product_is_rejected(
    actor: Any, product: ProductResponse, policy: PolicyResponse, insurer: Any
) -> None:
    """Um produto, uma apólice (por enquanto)."""
    with pytest.raises(ConflictError) as error:
        execute(command(actor, product, insurer, policy_number="AP-0002"))

    assert error.value.code == "policy_already_registered"


def test_repeated_policy_number_for_same_insurer_is_rejected(
    actor: Any, policy: PolicyResponse, insurer: Any
) -> None:
    other = create_product(CreateProductCommand(actor_id=actor.id, code="P2", name="Outro"))

    with pytest.raises(ConflictError) as error:
        execute(command(actor, other, insurer, policy_number=policy.policy_number))

    assert error.value.code == "policy_number_taken"


def test_same_number_with_another_insurer_is_accepted(
    actor: Any, policy: PolicyResponse, other_insurer: Any
) -> None:
    other = create_product(CreateProductCommand(actor_id=actor.id, code="P2", name="Outro"))

    registered = execute(command(actor, other, other_insurer, policy_number=policy.policy_number))

    assert registered.policy_number == policy.policy_number


def test_effective_until_not_after_start_is_rejected(
    actor: Any, product: ProductResponse, insurer: Any
) -> None:
    with pytest.raises(DomainError) as error:
        execute(command(actor, product, insurer, effective_until=TODAY - timedelta(days=1)))

    assert error.value.code == "policy_dates_invalid"
