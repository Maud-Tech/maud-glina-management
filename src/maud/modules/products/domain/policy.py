"""Regras puras da apólice: número, vigência e status. Sem Django, sem banco."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from maud.shared.errors import DomainError

MAX_POLICY_NUMBER_LENGTH = 100


class PolicyStatus(StrEnum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class PolicyData:
    """Dados da apólice já validados e normalizados, prontos para gravar."""

    policy_number: str
    issue_date: date | None
    effective_from: date
    effective_until: date | None


def validate_policy(
    *,
    policy_number: str,
    issue_date: date | None,
    effective_from: date,
    effective_until: date | None,
) -> PolicyData:
    """Valida número e vigência. O fim da vigência é opcional e vem depois do início."""
    clean_number = policy_number.strip()
    if not clean_number:
        raise DomainError("Número da apólice é obrigatório.", code="policy_number_required")
    if len(clean_number) > MAX_POLICY_NUMBER_LENGTH:
        raise DomainError(
            f"Número da apólice passa de {MAX_POLICY_NUMBER_LENGTH} caracteres.",
            code="policy_number_too_long",
        )
    if effective_until is not None and effective_until <= effective_from:
        raise DomainError(
            "O fim da vigência tem de ser depois do início.", code="policy_dates_invalid"
        )
    return PolicyData(
        policy_number=clean_number,
        issue_date=issue_date,
        effective_from=effective_from,
        effective_until=effective_until,
    )


def is_effective(
    status: PolicyStatus, effective_from: date, effective_until: date | None, on: date
) -> bool:
    """Ativa e dentro da vigência no dia `on` (o último dia da vigência ainda vale)."""
    if status is not PolicyStatus.ACTIVE or on < effective_from:
        return False
    return effective_until is None or on <= effective_until


def check_policy_editable(status: PolicyStatus) -> None:
    """Apólice expirada não muda mais."""
    if status is PolicyStatus.EXPIRED:
        raise DomainError("Apólice expirada não pode ser alterada.", code="policy_expired")
