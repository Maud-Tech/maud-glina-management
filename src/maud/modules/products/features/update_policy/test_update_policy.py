from typing import Any

import pytest

from maud.modules.products.features.expire_policy.handler import ExpirePolicyCommand
from maud.modules.products.features.expire_policy.handler import execute as expire_policy
from maud.modules.products.features.update_policy.handler import UpdatePolicyCommand, execute
from maud.modules.products.models import ProductChange
from maud.modules.products.responses import PolicyResponse
from maud.shared.errors import DomainError

pytestmark = pytest.mark.django_db


def command(actor: Any, policy: PolicyResponse, **changes: Any) -> UpdatePolicyCommand:
    fields: dict[str, Any] = {
        "actor_id": actor.id,
        "policy_id": policy.id,
        "policy_number": policy.policy_number,
        "insurer_entity_id": policy.insurer_entity_id,
        "effective_from": policy.effective_from,
        "effective_until": policy.effective_until,
        "issue_date": policy.issue_date,
    }
    fields.update(changes)
    return UpdatePolicyCommand(**fields)


def test_insurer_change_is_recorded_with_before_and_after(
    actor: Any, policy: PolicyResponse, insurer: Any, other_insurer: Any
) -> None:
    updated = execute(command(actor, policy, insurer_entity_id=other_insurer.id, reason="cessão"))

    assert updated.insurer_entity_id == other_insurer.id
    change = ProductChange.objects.get(object_type="POLICY", action="UPDATED")
    assert change.changes == {"insurer_entity": [str(insurer.id), str(other_insurer.id)]}
    assert change.reason == "cessão"


def test_new_insurer_must_be_a_company(actor: Any, policy: PolicyResponse, person: Any) -> None:
    with pytest.raises(DomainError) as error:
        execute(command(actor, policy, insurer_entity_id=person.id))

    assert error.value.code == "insurer_must_be_company"


def test_expired_policy_cannot_be_updated(actor: Any, policy: PolicyResponse) -> None:
    expire_policy(ExpirePolicyCommand(actor_id=actor.id, policy_id=policy.id))

    with pytest.raises(DomainError) as error:
        execute(command(actor, policy, policy_number="AP-9999"))

    assert error.value.code == "policy_expired"
