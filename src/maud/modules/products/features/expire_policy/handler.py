"""Expirar a apólice (e, com ela, o produto). Slice de COMANDO (tela, com login).

Passo a passo:
    1. trava produto e apólice (nessa ordem); apólice já expirada é recusada
    2. apólice vai para EXPIRED
    3. produto ativo ou inativo vai para EXPIRED (domain/product.py); rascunho e encerrado ficam
    4. uma linha de histórico para a apólice e outra para o produto, se ele mudou

Expirado só pode ser encerrado depois (change_product_status). Renovação: a definir com o time.
Erros: 404 policy_not_found
       422 policy_already_expired
"""

from dataclasses import dataclass
from uuid import UUID

from django.db import transaction

from maud.modules.products.domain.policy import PolicyStatus
from maud.modules.products.domain.product import ProductStatus, status_after_policy_expired
from maud.modules.products.history import record_product_change
from maud.modules.products.models import ProductChange
from maud.modules.products.queries import get_policy, get_product
from maud.modules.products.responses import PolicyResponse, policy_response
from maud.shared.errors import DomainError


@dataclass(frozen=True)
class ExpirePolicyCommand:
    actor_id: int
    policy_id: UUID
    reason: str = ""


def execute(command: ExpirePolicyCommand) -> PolicyResponse:
    with transaction.atomic():
        # 1. Trava produto e apólice
        product_id = get_policy(command.policy_id).product_id
        product = get_product(product_id, for_update=True)
        policy = get_policy(command.policy_id, for_update=True)
        if policy.status == PolicyStatus.EXPIRED.value:
            raise DomainError("A apólice já está expirada.", code="policy_already_expired")

        # 2. Apólice expira
        policy.status = PolicyStatus.EXPIRED.value
        policy.save(update_fields=["status", "updated_at"])
        record_product_change(
            product_id=product.id,
            object_type=ProductChange.ObjectType.POLICY,
            object_id=policy.id,
            action=ProductChange.Action.STATUS_CHANGED,
            changes={"status": [PolicyStatus.ACTIVE.value, PolicyStatus.EXPIRED.value]},
            actor_id=command.actor_id,
            reason=command.reason,
        )

        # 3. e 4. Produto expira junto, se estava ativo ou inativo
        current = ProductStatus(product.status)
        after = status_after_policy_expired(current)
        if after is not current:
            product.status = after.value
            product.save(update_fields=["status", "updated_at"])
            record_product_change(
                product_id=product.id,
                object_type=ProductChange.ObjectType.PRODUCT,
                object_id=product.id,
                action=ProductChange.Action.STATUS_CHANGED,
                changes={"status": [current.value, after.value]},
                actor_id=command.actor_id,
                reason=f"Apólice {policy.policy_number} expirada. {command.reason}".strip(),
            )

    return policy_response(policy)
