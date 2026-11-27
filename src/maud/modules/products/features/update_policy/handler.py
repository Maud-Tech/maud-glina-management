"""Alterar os dados da apólice. Slice de COMANDO (tela, com login).

Passo a passo:
    1. valida número e vigência (domain/policy.py)
    2. trava produto e apólice (nessa ordem); produto encerrado ou apólice expirada não mudam
    3. seguradora trocada é conferida (Entity jurídica); número único por seguradora
    4. grava só se algo mudou, com a linha de histórico na mesma transação

Status não muda aqui: expirar é a slice expire_policy. A moeda segue a do produto.
Erros: 404 policy_not_found
       422 policy_expired, product_closed, insurer_not_found, insurer_must_be_company
           (+ os de register_policy)
       409 policy_number_taken
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from django.db import transaction

from maud.modules.products.domain.changes import changed_fields
from maud.modules.products.domain.policy import (
    PolicyStatus,
    check_policy_editable,
    validate_policy,
)
from maud.modules.products.domain.product import ProductStatus, check_editable
from maud.modules.products.history import policy_snapshot, record_product_change
from maud.modules.products.models import Policy, ProductChange
from maud.modules.products.queries import check_insurer, get_policy, get_product
from maud.modules.products.responses import PolicyResponse, policy_response
from maud.shared.errors import ConflictError


@dataclass(frozen=True)
class UpdatePolicyCommand:
    actor_id: int
    policy_id: UUID
    policy_number: str
    insurer_entity_id: UUID
    effective_from: date
    effective_until: date | None = None
    issue_date: date | None = None
    reason: str = ""


def execute(command: UpdatePolicyCommand) -> PolicyResponse:
    # 1. Valida
    data = validate_policy(
        policy_number=command.policy_number,
        issue_date=command.issue_date,
        effective_from=command.effective_from,
        effective_until=command.effective_until,
    )

    with transaction.atomic():
        # 2. Trava produto e apólice
        product_id = get_policy(command.policy_id).product_id
        product = get_product(product_id, for_update=True)
        policy = get_policy(command.policy_id, for_update=True)
        check_editable(ProductStatus(product.status))
        check_policy_editable(PolicyStatus(policy.status))

        # 3. Seguradora e número
        if command.insurer_entity_id != policy.insurer_entity_id:
            check_insurer(command.insurer_entity_id)
        if (
            Policy.objects.filter(
                insurer_entity_id=command.insurer_entity_id, policy_number=data.policy_number
            )
            .exclude(pk=policy.pk)
            .exists()
        ):
            raise ConflictError(
                f"A seguradora já tem a apólice {data.policy_number}.", code="policy_number_taken"
            )

        # 4. Grava só o que mudou
        before = policy_snapshot(policy)
        policy.policy_number = data.policy_number
        policy.insurer_entity_id = command.insurer_entity_id
        policy.issue_date = data.issue_date
        policy.effective_from = data.effective_from
        policy.effective_until = data.effective_until
        changes = changed_fields(before, policy_snapshot(policy))
        if changes:
            policy.save()
            record_product_change(
                product_id=product.id,
                object_type=ProductChange.ObjectType.POLICY,
                object_id=policy.id,
                action=ProductChange.Action.UPDATED,
                changes=changes,
                actor_id=command.actor_id,
                reason=command.reason,
            )

    return policy_response(policy)
