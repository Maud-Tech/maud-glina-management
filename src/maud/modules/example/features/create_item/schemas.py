"""Formato do que entra e do que sai da API nesta slice."""

from uuid import UUID

from ninja import Schema


class CreateItemRequest(Schema):
    name: str


class ItemResponse(Schema):
    id: UUID
    name: str
    is_active: bool
