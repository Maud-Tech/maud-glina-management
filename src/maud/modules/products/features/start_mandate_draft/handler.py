"""Abrir um rascunho do regulamento. Slice de COMANDO (tela, com login).

Passo a passo:
    1. trava o produto; encerrado não muda
    2. um rascunho por produto (o banco também garante)
    3. o rascunho recebe o número seguinte e nasce como cópia da última versão publicada
       (termos e limites); sem versão publicada, nasce vazio
    4. grava o rascunho e a linha de histórico (CREATED, com a versão de origem)

Erros: 404 product_not_found
       422 product_closed
       409 mandate_draft_exists
"""

from dataclasses import dataclass
from uuid import UUID

from django.db import transaction
from django.db.models import Max

from maud.modules.products.domain.mandate import TERM_FIELDS, MandateState
from maud.modules.products.domain.product import ProductStatus, check_editable
from maud.modules.products.history import record_mandate_change
from maud.modules.products.models import ExposureLimit, Mandate, MandateChange
from maud.modules.products.queries import get_product, latest_published_mandate
from maud.modules.products.responses import MandateResponse, mandate_response
from maud.shared.errors import ConflictError


@dataclass(frozen=True)
class StartMandateDraftCommand:
    actor_id: int
    product_id: UUID


def execute(command: StartMandateDraftCommand) -> MandateResponse:
    with transaction.atomic():
        # 1. Trava o produto
        product = get_product(command.product_id, for_update=True)
        check_editable(ProductStatus(product.status))

        # 2. Um rascunho por vez
        if Mandate.objects.filter(product=product, state=MandateState.DRAFT.value).exists():
            raise ConflictError(
                "Já existe um rascunho do regulamento: edite ou publique esse.",
                code="mandate_draft_exists",
            )

        # 3. Número seguinte; cópia da última publicada
        last_version = Mandate.objects.filter(product=product).aggregate(v=Max("version"))["v"]
        source = latest_published_mandate(product.id)
        copied = {name: getattr(source, name) for name in TERM_FIELDS} if source else {}
        draft = Mandate.objects.create(
            product=product,
            version=(last_version or 0) + 1,
            state=MandateState.DRAFT.value,
            **copied,
        )
        if source is not None:
            ExposureLimit.objects.bulk_create(
                ExposureLimit(
                    mandate=draft,
                    dimension=limit.dimension,
                    target=limit.target,
                    min_pct=limit.min_pct,
                    max_pct=limit.max_pct,
                )
                for limit in source.exposure_limits.all()
            )

        # 4. Histórico
        record_mandate_change(
            mandate_id=draft.id,
            action=MandateChange.Action.CREATED,
            changes={
                "version": [None, draft.version],
                "copied_from_version": [None, source.version if source else None],
            },
            actor_id=command.actor_id,
        )

    return mandate_response(draft)
