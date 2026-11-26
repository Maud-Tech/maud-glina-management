"""Listar itens. Slice de referência de CONSULTA (só lê): copie a forma, não o conteúdo.

Sem transação de escrita, sem idempotência, sem evento.
Filtros: trecho do nome e se inclui os inativos.
"""

from dataclasses import dataclass

from maud.modules.example.domain.item import normalize_name
from maud.modules.example.features.list_items.schemas import ItemListItem
from maud.modules.example.models import Item


@dataclass(frozen=True)
class ListItemsQuery:
    search: str | None = None
    include_inactive: bool = False


def execute(query: ListItemsQuery) -> list[ItemListItem]:
    items = Item.objects.order_by("name")

    if not query.include_inactive:
        items = items.filter(is_active=True)

    if query.search and normalize_name(query.search):
        items = items.filter(name__icontains=normalize_name(query.search))

    return [ItemListItem.model_validate(item) for item in items]
