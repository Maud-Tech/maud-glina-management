"""Cadastrar a apólice do produto. Slice de COMANDO (tela, com login).

Passo a passo:
    1. valida número e vigência (domain/policy.py)
    2. trava o produto; encerrado não muda; um produto tem uma apólice (por enquanto)
    3. a seguradora é uma Entity jurídica (entities); número único por seguradora
    4. grava a apólice ativa, na moeda-base do produto, e a linha de histórico

Erros: 404 product_not_found
       422 policy_number_required, policy_number_too_long, policy_dates_invalid, product_closed,
           insurer_not_found, insurer_must_be_company
       409 policy_already_registered, policy_number_taken
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from django.db import transaction

from maud.modules.products.domain.policy import PolicyStatus, validate_policy
from maud.modules.products.domain.product import ProductStatus, check_editable
from maud.modules.products.history import as_created, policy_snapshot, record_product_change
from maud.modules.products.models import Policy, ProductChange
from maud.modules.products.queries import check_insurer, get_product, product_policy
from maud.modules.products.responses import PolicyResponse, policy_response
from maud.shared.errors import ConflictError


@dataclass(frozen=True)
class RegisterPolicyCommand:
    actor_id: int
    product_id: UUID
    policy_number: str
    insurer_entity_id: UUID
    effective_from: date
    effective_until: date | None = None
    issue_date: date | None = None


def execute(command: RegisterPolicyCommand) -> PolicyResponse:
    # 1. Valida
    data = validate_policy(
        policy_number=command.policy_number,
        issue_date=command.issue_date,
        effective_from=command.effective_from,
        effective_until=command.effective_until,
    )

    with transaction.atomic():
        # 2. Trava o produto; uma apólice por produto
        product = get_product(command.product_id, for_update=True)
        check_editable(ProductStatus(product.status))
        if product_policy(product.id) is not None:
            raise ConflictError("Este produto já tem apólice.", code="policy_already_registered")

        # 3. Seguradora jurídica; número único por seguradora
        check_insurer(command.insurer_entity_id)
        if Policy.objects.filter(
            insurer_entity_id=command.insurer_entity_id, policy_number=data.policy_number
        ).exists():
            raise ConflictError(
                f"A seguradora já tem a apólice {data.policy_number}.", code="policy_number_taken"
            )

        # 4. Grava + histórico
        policy = Policy.objects.create(
            product=product,
            policy_number=data.policy_number,
            insurer_entity_id=command.insurer_entity_id,
            currency_id=product.base_currency_id,
            issue_date=data.issue_date,
            effective_from=data.effective_from,
            effective_until=data.effective_until,
            status=PolicyStatus.ACTIVE.value,
        )
        record_product_change(
            product_id=product.id,
            object_type=ProductChange.ObjectType.POLICY,
            object_id=policy.id,
            action=ProductChange.Action.CREATED,
            changes=as_created(policy_snapshot(policy)),
            actor_id=command.actor_id,
        )

    return policy_response(policy)
