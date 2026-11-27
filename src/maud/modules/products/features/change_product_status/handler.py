"""Mudar o status do produto (ativar, inativar, encerrar). Slice de COMANDO (tela, com login).

Passo a passo:
    1. trava o produto
    2. confere a mudança (domain/product.py): ativar exige regulamento publicado e apólice ativa
       e vigente hoje; EXPIRED não se escolhe aqui (chega com a apólice, em expire_policy)
    3. grava o status e a linha de histórico na mesma transação

Erros: 404 product_not_found
       422 product_status_unknown, product_status_unchanged, product_status_change_not_allowed,
           product_activation_requires_published_mandate,
           product_activation_requires_effective_policy
"""

from dataclasses import dataclass
from uuid import UUID

from django.db import transaction

from maud.modules.products.domain.product import ProductStatus, check_status_change
from maud.modules.products.history import record_product_change
from maud.modules.products.models import ProductChange
from maud.modules.products.queries import activation_readiness, get_product
from maud.modules.products.responses import ProductResponse, product_response
from maud.shared.clock import get_clock
from maud.shared.errors import DomainError


@dataclass(frozen=True)
class ChangeProductStatusCommand:
    actor_id: int
    product_id: UUID
    status: str
    reason: str = ""


def execute(command: ChangeProductStatusCommand) -> ProductResponse:
    try:
        target = ProductStatus(command.status)
    except ValueError:
        raise DomainError(
            f"Status desconhecido: {command.status}.", code="product_status_unknown"
        ) from None

    with transaction.atomic():
        # 1. Trava
        product = get_product(command.product_id, for_update=True)
        current = ProductStatus(product.status)

        # 2. Confere
        today = get_clock().now().date()
        check_status_change(current, target, activation_readiness(product.id, today))

        # 3. Grava + histórico
        product.status = target.value
        product.save(update_fields=["status", "updated_at"])
        record_product_change(
            product_id=product.id,
            object_type=ProductChange.ObjectType.PRODUCT,
            object_id=product.id,
            action=ProductChange.Action.STATUS_CHANGED,
            changes={"status": [current.value, target.value]},
            actor_id=command.actor_id,
            reason=command.reason,
        )

    return product_response(product)
