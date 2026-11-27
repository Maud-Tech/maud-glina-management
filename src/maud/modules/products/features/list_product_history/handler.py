"""Linha do tempo de um produto. Slice de CONSULTA (só lê).

Junta os dois históricos append-only, do mais novo para o mais antigo:
    - ProductChange: produto, apólice e documentos;
    - MandateChange: regulamento (com a versão) e limites (pelo id do limite).
Erros: 404 product_not_found
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from ninja import Schema

from maud.modules.products.models import MandateChange, ProductChange
from maud.modules.products.queries import get_product

MANDATE_OBJECT = "MANDATE"
EXPOSURE_LIMIT_OBJECT = "EXPOSURE_LIMIT"


class HistoryEntry(Schema):
    changed_at: datetime
    object_type: str
    object_id: UUID
    mandate_version: int | None
    action: str
    changes: dict[str, Any]
    reason: str
    changed_by: str


@dataclass(frozen=True)
class ListProductHistoryQuery:
    product_id: UUID


def execute(query: ListProductHistoryQuery) -> list[HistoryEntry]:
    product = get_product(query.product_id)
    entries = [
        HistoryEntry(
            changed_at=change.changed_at,
            object_type=change.object_type,
            object_id=change.object_id,
            mandate_version=None,
            action=change.action,
            changes=change.changes,
            reason=change.reason,
            changed_by=change.changed_by.get_username(),
        )
        for change in ProductChange.objects.filter(product=product)
        .select_related("changed_by")
        .order_by("changed_at")
    ]
    entries.extend(
        HistoryEntry(
            changed_at=change.changed_at,
            object_type=EXPOSURE_LIMIT_OBJECT if change.exposure_limit_id else MANDATE_OBJECT,
            object_id=change.exposure_limit_id or change.mandate_id,
            mandate_version=change.mandate.version,
            action=change.action,
            changes=change.changes,
            reason=change.reason,
            changed_by=change.changed_by.get_username(),
        )
        for change in MandateChange.objects.filter(mandate__product=product)
        .select_related("mandate", "changed_by")
        .order_by("changed_at")
    )
    return sorted(entries, key=lambda entry: entry.changed_at, reverse=True)
