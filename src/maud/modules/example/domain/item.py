"""Regras puras do item: sem banco, sem Django. Recebem dados, devolvem dados ou erro."""

from dataclasses import dataclass

from maud.shared.errors import DomainError

MAX_NAME_LENGTH = 200


@dataclass(frozen=True)
class NewItem:
    """Dados de um item já validados e normalizados, prontos para gravar."""

    name: str


def validate_new_item(name: str) -> NewItem:
    """Valida e normaliza os dados de cadastro de um item."""
    clean_name = normalize_name(name)

    if not clean_name:
        raise DomainError("Nome do item é obrigatório", code="item_name_required")

    if len(clean_name) > MAX_NAME_LENGTH:
        raise DomainError(
            f"Nome do item passa de {MAX_NAME_LENGTH} caracteres",
            code="item_name_too_long",
        )

    return NewItem(name=clean_name)


def normalize_name(name: str) -> str:
    """Remove espaços repetidos e das pontas: '  Item   A ' vira 'Item A'."""
    return " ".join(name.split())
