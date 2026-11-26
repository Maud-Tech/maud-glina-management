"""GET /api/v1/example/items"""

from django.http import HttpRequest

from maud.modules.example.features.list_items.handler import ListItemsQuery, execute
from maud.modules.example.features.list_items.schemas import ItemListItem
from maud.modules.example.router import router


@router.get("/items", response=list[ItemListItem], summary="Listar itens")
def get_items(
    request: HttpRequest,
    search: str | None = None,
    include_inactive: bool = False,
) -> list[ItemListItem]:
    query = ListItemsQuery(search=search, include_inactive=include_inactive)
    return execute(query)
