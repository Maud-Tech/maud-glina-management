"""Histórico append-only. As slices gravam a linha na mesma transação da alteração.

Retratos (`*_snapshot`) são dicionários simples dos campos que entram no histórico; a diferença
entre dois retratos (`changed_fields`, em domain/) vira o `changes` da linha:
{campo: [antes, depois]}.
"""

from uuid import UUID

from maud.modules.products.domain.changes import changed_fields
from maud.modules.products.domain.mandate import TERM_FIELDS
from maud.modules.products.models import (
    ExposureLimit,
    Mandate,
    MandateChange,
    Policy,
    Product,
    ProductChange,
    ProductDocument,
)
from maud.shared.clock import get_clock


def product_snapshot(product: Product) -> dict[str, object]:
    return {
        "code": product.code,
        "name": product.name,
        "description": product.description,
        "base_currency": product.base_currency_id,
        "status": product.status,
        "launch_date": product.launch_date,
        "closing_date": product.closing_date,
    }


def policy_snapshot(policy: Policy) -> dict[str, object]:
    return {
        "policy_number": policy.policy_number,
        "insurer_entity": str(policy.insurer_entity_id),
        "currency": policy.currency_id,
        "issue_date": policy.issue_date,
        "effective_from": policy.effective_from,
        "effective_until": policy.effective_until,
        "status": policy.status,
    }


def document_snapshot(document: ProductDocument) -> dict[str, object]:
    return {
        "document_type": document.document_type,
        "title": document.title,
        "policy": str(document.policy_id) if document.policy_id else None,
        "content_type": document.content_type,
        "size_bytes": document.size_bytes,
    }


def mandate_snapshot(mandate: Mandate) -> dict[str, object]:
    snapshot: dict[str, object] = {name: getattr(mandate, name) for name in TERM_FIELDS}
    snapshot["eligible_asset_classes"] = sorted(mandate.eligible_asset_classes)
    return snapshot


def limit_snapshot(limit: ExposureLimit) -> dict[str, object]:
    return {
        "dimension": limit.dimension,
        "target": limit.target,
        "min_pct": limit.min_pct,
        "max_pct": limit.max_pct,
    }


def as_created(snapshot: dict[str, object]) -> dict[str, list[object]]:
    """Registro novo: cada campo preenchido vai de None para o valor."""
    return changed_fields({}, snapshot)


def as_removed(snapshot: dict[str, object]) -> dict[str, list[object]]:
    """Registro removido: cada campo preenchido vai do valor para None."""
    return changed_fields(snapshot, {})


def record_product_change(
    *,
    product_id: UUID,
    object_type: str,
    object_id: UUID,
    action: str,
    changes: dict[str, list[object]],
    actor_id: int,
    reason: str = "",
) -> None:
    ProductChange.objects.create(
        product_id=product_id,
        object_type=object_type,
        object_id=object_id,
        action=action,
        changes=changes,
        reason=reason.strip(),
        changed_by_id=actor_id,
        changed_at=get_clock().now(),
    )


def record_mandate_change(
    *,
    mandate_id: UUID,
    action: str,
    changes: dict[str, list[object]],
    actor_id: int,
    reason: str = "",
    exposure_limit_id: UUID | None = None,
) -> None:
    MandateChange.objects.create(
        mandate_id=mandate_id,
        exposure_limit_id=exposure_limit_id,
        action=action,
        changes=changes,
        reason=reason.strip(),
        changed_by_id=actor_id,
        changed_at=get_clock().now(),
    )
