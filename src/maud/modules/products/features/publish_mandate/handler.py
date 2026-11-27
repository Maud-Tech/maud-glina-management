"""Publicar o rascunho do regulamento. Slice de COMANDO (tela, com login).

A versão publicada nunca muda e vale para todos, inclusive quem já comprou, a partir da vigência.

Passo a passo:
    1. trava produto e regulamento (nessa ordem); só rascunho, de produto não encerrado
    2. confere (domain/mandate.py): termos obrigatórios preenchidos, vigência depois da versão
       anterior e, da versão 2 em diante, o motivo
    3. grava como publicada (data, quem, quando) e a linha de histórico (PUBLISHED, com o motivo)

Erros: 404 mandate_not_found
       422 mandate_not_draft, product_closed, mandate_incomplete,
           mandate_effective_date_not_after_previous, mandate_publish_reason_required
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from django.db import transaction

from maud.modules.products.domain.mandate import (
    MandateState,
    check_draft,
    check_effective_date,
    check_publish_reason,
    check_publishable,
)
from maud.modules.products.domain.product import ProductStatus, check_editable
from maud.modules.products.history import record_mandate_change
from maud.modules.products.models import MandateChange
from maud.modules.products.queries import get_mandate, get_product, latest_published_mandate
from maud.modules.products.responses import MandateResponse, mandate_response, mandate_terms
from maud.shared.clock import get_clock


@dataclass(frozen=True)
class PublishMandateCommand:
    actor_id: int
    mandate_id: UUID
    effective_from: date
    reason: str = ""


def execute(command: PublishMandateCommand) -> MandateResponse:
    with transaction.atomic():
        # 1. Trava produto e regulamento
        product_id = get_mandate(command.mandate_id).product_id
        product = get_product(product_id, for_update=True)
        mandate = get_mandate(command.mandate_id, for_update=True)
        check_editable(ProductStatus(product.status))
        check_draft(MandateState(mandate.state))

        # 2. Confere
        check_publishable(mandate_terms(mandate))
        previous = latest_published_mandate(product.id)
        check_effective_date(command.effective_from, previous.effective_from if previous else None)
        reason = check_publish_reason(mandate.version, command.reason)

        # 3. Publica + histórico
        mandate.state = MandateState.PUBLISHED.value
        mandate.effective_from = command.effective_from
        mandate.published_at = get_clock().now()
        mandate.published_by_id = command.actor_id
        mandate.save()
        record_mandate_change(
            mandate_id=mandate.id,
            action=MandateChange.Action.PUBLISHED,
            changes={
                "state": [MandateState.DRAFT.value, MandateState.PUBLISHED.value],
                "effective_from": [None, command.effective_from],
            },
            actor_id=command.actor_id,
            reason=reason,
        )

    return mandate_response(mandate)
