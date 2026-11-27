"""Regras puras do produto: dados de cadastro e mudança de status. Sem Django, sem banco."""

import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from maud.shared.errors import DomainError

DEFAULT_BASE_CURRENCY = "USD"
MAX_NAME_LENGTH = 200
MAX_CODE_LENGTH = 50
_CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]*$")


class ProductStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"
    CLOSED = "CLOSED"


# Mudanças de status feitas pela tela. EXPIRED só chega junto com a apólice (expire_policy).
ALLOWED_STATUS_CHANGES: dict[ProductStatus, frozenset[ProductStatus]] = {
    ProductStatus.DRAFT: frozenset({ProductStatus.ACTIVE, ProductStatus.CLOSED}),
    ProductStatus.ACTIVE: frozenset({ProductStatus.INACTIVE, ProductStatus.CLOSED}),
    ProductStatus.INACTIVE: frozenset({ProductStatus.ACTIVE, ProductStatus.CLOSED}),
    ProductStatus.EXPIRED: frozenset({ProductStatus.CLOSED}),
    ProductStatus.CLOSED: frozenset(),
}

STATUSES_THAT_EXPIRE_WITH_POLICY = frozenset({ProductStatus.ACTIVE, ProductStatus.INACTIVE})


@dataclass(frozen=True)
class ProductData:
    """Dados do produto já validados e normalizados, prontos para gravar."""

    code: str
    name: str
    description: str
    launch_date: date | None
    closing_date: date | None


@dataclass(frozen=True)
class ActivationReadiness:
    """O que precisa existir para o produto ficar ativo."""

    has_published_mandate: bool
    has_effective_policy: bool


def normalize_text(value: str) -> str:
    """Tira espaços repetidos e das pontas: '  Glina   USD ' vira 'Glina USD'."""
    return " ".join(value.split())


def validate_code(code: str) -> str:
    """Código em maiúsculas, com letras, números, '-' e '_'. Ex.: 'GLINA-USD-01'."""
    clean = code.strip().upper()
    if not clean or len(clean) > MAX_CODE_LENGTH or not _CODE_PATTERN.match(clean):
        raise DomainError(
            "Use de 1 a 50 letras, números, '-' ou '_' no código.", code="product_code_invalid"
        )
    return clean


def validate_product(
    *,
    code: str,
    name: str,
    description: str,
    launch_date: date | None,
    closing_date: date | None,
) -> ProductData:
    """Valida e normaliza os dados de cadastro do produto."""
    clean_name = normalize_text(name)
    if not clean_name:
        raise DomainError("Nome do produto é obrigatório.", code="product_name_required")
    if len(clean_name) > MAX_NAME_LENGTH:
        raise DomainError(
            f"Nome do produto passa de {MAX_NAME_LENGTH} caracteres.", code="product_name_too_long"
        )
    if launch_date and closing_date and closing_date < launch_date:
        raise DomainError(
            "O encerramento não pode ser antes do lançamento.", code="product_dates_invalid"
        )
    return ProductData(
        code=validate_code(code),
        name=clean_name,
        description=description.strip(),
        launch_date=launch_date,
        closing_date=closing_date,
    )


def check_editable(status: ProductStatus) -> None:
    """Produto encerrado não muda mais."""
    if status is ProductStatus.CLOSED:
        raise DomainError("Produto encerrado não pode ser alterado.", code="product_closed")


def check_identity_change(
    status: ProductStatus, *, code_changed: bool, currency_changed: bool, has_policy: bool
) -> None:
    """Código e moeda-base só mudam no rascunho; a moeda, só enquanto não há apólice."""
    if code_changed and status is not ProductStatus.DRAFT:
        raise DomainError("O código só muda no rascunho.", code="product_code_locked")
    if currency_changed and status is not ProductStatus.DRAFT:
        raise DomainError("A moeda-base só muda no rascunho.", code="product_currency_locked")
    if currency_changed and has_policy:
        raise DomainError(
            "A apólice já usa a moeda-base atual; a moeda não pode mudar.",
            code="product_currency_has_policy",
        )


def check_status_change(
    current: ProductStatus, target: ProductStatus, readiness: ActivationReadiness
) -> None:
    """Confere se o produto pode ir de `current` para `target`."""
    if target is current:
        raise DomainError("O produto já está nesse status.", code="product_status_unchanged")
    if target not in ALLOWED_STATUS_CHANGES[current]:
        raise DomainError(
            f"O produto não pode ir de {current.value} para {target.value}.",
            code="product_status_change_not_allowed",
        )
    if target is ProductStatus.ACTIVE:
        if not readiness.has_published_mandate:
            raise DomainError(
                "Publique o regulamento antes de ativar o produto.",
                code="product_activation_requires_published_mandate",
            )
        if not readiness.has_effective_policy:
            raise DomainError(
                "O produto precisa de uma apólice ativa e vigente para ser ativado.",
                code="product_activation_requires_effective_policy",
            )


def status_after_policy_expired(current: ProductStatus) -> ProductStatus:
    """Expirar a apólice expira o produto ativo ou inativo; rascunho e encerrado não mudam."""
    if current in STATUSES_THAT_EXPIRE_WITH_POLICY:
        return ProductStatus.EXPIRED
    return current
