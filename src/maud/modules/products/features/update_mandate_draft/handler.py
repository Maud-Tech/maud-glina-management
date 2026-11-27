"""Editar o rascunho do regulamento e os seus limites. Slice de COMANDO (tela, com login).

A tela manda os termos inteiros e a lista inteira de limites; a slice grava a diferença.

Passo a passo:
    1. valida termos e limites (domain/mandate.py) e confere os alvos (país, moeda, emissor)
    2. trava produto e regulamento (nessa ordem); só rascunho, de produto não encerrado
    3. termos: grava só o que mudou, com uma linha de histórico (UPDATED)
    4. limites, comparados por dimensão e alvo: novo (CREATED), mínimo ou máximo trocado
       (UPDATED) e ausente (REMOVED, a linha guarda os valores que ele tinha)

Erros: 404 mandate_not_found
       422 mandate_not_draft, product_closed, mandate_risk_level_invalid,
           mandate_target_return_invalid, mandate_average_term_invalid, mandate_amount_invalid,
           mandate_term_invalid, mandate_asset_class_unknown, exposure_limit_target_required,
           exposure_limit_target_not_allowed, exposure_limit_range_invalid,
           exposure_limit_asset_class_not_eligible, exposure_limit_duplicated,
           exposure_limit_target_not_found
"""

from dataclasses import dataclass, fields
from uuid import UUID

from django.db import transaction

from maud.modules.assets.api import asset_class_codes
from maud.modules.products.domain.changes import changed_fields
from maud.modules.products.domain.mandate import (
    LimitTerms,
    MandateState,
    MandateTerms,
    check_draft,
    validate_limits,
    validate_terms,
)
from maud.modules.products.domain.product import ProductStatus, check_editable
from maud.modules.products.history import (
    as_created,
    as_removed,
    limit_snapshot,
    mandate_snapshot,
    record_mandate_change,
)
from maud.modules.products.models import ExposureLimit, MandateChange
from maud.modules.products.queries import check_limit_targets, get_mandate, get_product
from maud.modules.products.responses import MandateResponse, mandate_response


@dataclass(frozen=True)
class UpdateMandateDraftCommand:
    actor_id: int
    mandate_id: UUID
    terms: MandateTerms
    limits: tuple[LimitTerms, ...] = ()
    reason: str = ""


def execute(command: UpdateMandateDraftCommand) -> MandateResponse:
    # 1. Valida termos, limites e alvos
    terms = validate_terms(command.terms, asset_class_codes())
    limits = validate_limits(command.limits, terms.eligible_asset_classes)
    check_limit_targets(limits)

    with transaction.atomic():
        # 2. Trava produto e regulamento
        product_id = get_mandate(command.mandate_id).product_id
        product = get_product(product_id, for_update=True)
        mandate = get_mandate(command.mandate_id, for_update=True)
        check_editable(ProductStatus(product.status))
        check_draft(MandateState(mandate.state))

        # 3. Termos
        before = mandate_snapshot(mandate)
        for field in fields(MandateTerms):
            value = getattr(terms, field.name)
            setattr(mandate, field.name, list(value) if isinstance(value, tuple) else value)
        changes = changed_fields(before, mandate_snapshot(mandate))
        if changes:
            mandate.save()
            record_mandate_change(
                mandate_id=mandate.id,
                action=MandateChange.Action.UPDATED,
                changes=changes,
                actor_id=command.actor_id,
                reason=command.reason,
            )

        # 4. Limites: diferença por dimensão e alvo
        existing = {
            (limit.dimension, limit.target): limit for limit in mandate.exposure_limits.all()
        }
        wanted = {(limit.dimension.value, limit.target): limit for limit in limits}
        for key, old in existing.items():
            if key not in wanted:
                snapshot = limit_snapshot(old)
                old_id = old.id
                old.delete()
                record_mandate_change(
                    mandate_id=mandate.id,
                    exposure_limit_id=old_id,
                    action=MandateChange.Action.REMOVED,
                    changes=as_removed(snapshot),
                    actor_id=command.actor_id,
                    reason=command.reason,
                )
        for key, new in wanted.items():
            current = existing.get(key)
            if current is None:
                created = ExposureLimit.objects.create(
                    mandate=mandate,
                    dimension=new.dimension.value,
                    target=new.target,
                    min_pct=new.min_pct,
                    max_pct=new.max_pct,
                )
                record_mandate_change(
                    mandate_id=mandate.id,
                    exposure_limit_id=created.id,
                    action=MandateChange.Action.CREATED,
                    changes=as_created(limit_snapshot(created)),
                    actor_id=command.actor_id,
                    reason=command.reason,
                )
                continue
            before_limit = limit_snapshot(current)
            current.min_pct = new.min_pct
            current.max_pct = new.max_pct
            limit_changes = changed_fields(before_limit, limit_snapshot(current))
            if limit_changes:
                current.save(update_fields=["min_pct", "max_pct"])
                record_mandate_change(
                    mandate_id=mandate.id,
                    exposure_limit_id=current.id,
                    action=MandateChange.Action.UPDATED,
                    changes=limit_changes,
                    actor_id=command.actor_id,
                    reason=command.reason,
                )

    return mandate_response(mandate)
