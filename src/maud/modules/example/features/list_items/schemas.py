"""Formato do que sai da API nesta slice."""

from uuid import UUID

from ninja import Schema


class ItemListItem(Schema):
    id: UUID
    name: str
    is_active: bool
