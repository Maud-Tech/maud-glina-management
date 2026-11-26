"""POST /api/v1/example/items"""

from typing import Annotated

from django.http import HttpRequest
from ninja import Header, Status

from maud.modules.example.features.create_item.handler import CreateItemCommand, execute
from maud.modules.example.features.create_item.schemas import CreateItemRequest, ItemResponse
from maud.modules.example.router import router


@router.post("/items", response={201: ItemResponse}, summary="Cadastrar item")
def post_item(
    request: HttpRequest,
    body: CreateItemRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> Status[ItemResponse]:
    command = CreateItemCommand(name=body.name, idempotency_key=idempotency_key)
    return Status(201, execute(command))
