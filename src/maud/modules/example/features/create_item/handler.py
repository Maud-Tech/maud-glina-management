"""Cadastrar item. Slice de referência de COMANDO (muda dados): copie a forma, não o conteúdo.

Passo a passo:
    1. valida e normaliza os dados (regra pura, em domain/)
    2. recusa nome que já existe
    3. grava o item
    4. publica o fato no outbox, na mesma transação

Idempotente: a mesma Idempotency-Key devolve a mesma resposta, sem gravar de novo.
Evento:      example.item_created
Erros:       422 item_name_required, item_name_too_long
             409 item_already_exists, idempotency_key_reused
"""

from dataclasses import dataclass

from maud.modules.example.domain.item import validate_new_item
from maud.modules.example.features.create_item.schemas import ItemResponse
from maud.modules.example.models import Item
from maud.shared import outbox
from maud.shared.errors import ConflictError
from maud.shared.idempotency import run_idempotent


@dataclass(frozen=True)
class CreateItemCommand:
    name: str
    idempotency_key: str


def execute(command: CreateItemCommand) -> ItemResponse:
    """Roda o cadastro uma única vez por Idempotency-Key."""
    return run_idempotent(
        scope="example.create_item",
        key=command.idempotency_key,
        request={"name": command.name},
        response_model=ItemResponse,
        operation=lambda: create_item(command),
    )


def create_item(command: CreateItemCommand) -> ItemResponse:
    # 1. Valida e normaliza
    new_item = validate_new_item(command.name)

    # 2. Recusa nome repetido (o banco também garante, com uma constraint)
    if Item.objects.filter(name__iexact=new_item.name).exists():
        raise ConflictError(f"Item '{new_item.name}' já existe", code="item_already_exists")

    # 3. Grava
    item = Item.objects.create(name=new_item.name)

    # 4. Publica o fato (o Worker entrega pelo integration)
    outbox.publish(
        "example.item_created",
        aggregate_type="item",
        aggregate_id=str(item.id),
        payload={"item_id": str(item.id), "name": item.name},
    )

    return ItemResponse.model_validate(item)
