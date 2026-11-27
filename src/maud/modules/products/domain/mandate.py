"""Regras puras do regulamento (mandato) e dos limites de exposição. Sem Django, sem banco.

O rascunho aceita termos incompletos (a tela preenche aos poucos); `check_publishable` exige o
que falta antes de publicar. Versão publicada nunca muda e vale para todos a partir da vigência.
"""

from collections.abc import Sequence
from dataclasses import dataclass, fields, replace
from datetime import date
from decimal import Decimal
from enum import StrEnum

from maud.shared.errors import DomainError

MIN_RISK_LEVEL = 1
MAX_RISK_LEVEL = 5
MAX_SPREAD_PCT = Decimal("100")
SPREAD_PLACES = 4
AMOUNT_PLACES = 2
PCT_PLACES = 2
TERM_YEARS_PLACES = 2
HUNDRED = Decimal("100")


class MandateState(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class ReturnBenchmark(StrEnum):
    SOFR = "SOFR"


class LimitDimension(StrEnum):
    ASSET_CLASS = "ASSET_CLASS"
    ISSUER = "ISSUER"
    SINGLE_ASSET = "SINGLE_ASSET"
    COUNTRY = "COUNTRY"
    CURRENCY = "CURRENCY"


@dataclass(frozen=True)
class MandateTerms:
    """Termos de uma versão do regulamento. No rascunho, `None` = ainda não preenchido."""

    risk_level: int | None = None
    target_return_benchmark: ReturnBenchmark = ReturnBenchmark.SOFR
    target_return_spread_pct: Decimal | None = None
    liquidity_days: int | None = None
    max_average_term_years: Decimal | None = None
    eligible_asset_classes: tuple[str, ...] = ()
    min_initial_amount: Decimal | None = None
    min_additional_amount: Decimal | None = None
    subscription_settlement_days: int | None = None
    min_redemption_amount: Decimal | None = None
    min_balance_amount: Decimal | None = None
    redemption_notice_days: int | None = None
    redemption_settlement_days: int | None = None
    lock_up_months: int | None = None
    notes: str = ""


TERM_FIELDS: tuple[str, ...] = tuple(field.name for field in fields(MandateTerms))

_AMOUNT_FIELDS = (
    "min_initial_amount",
    "min_additional_amount",
    "min_redemption_amount",
    "min_balance_amount",
)
_COUNT_FIELDS = (
    "liquidity_days",
    "subscription_settlement_days",
    "redemption_notice_days",
    "redemption_settlement_days",
    "lock_up_months",
)

# O que não pode faltar para publicar. Os demais termos são opcionais.
REQUIRED_TO_PUBLISH: tuple[str, ...] = (
    "risk_level",
    "target_return_spread_pct",
    "liquidity_days",
    "max_average_term_years",
    "min_initial_amount",
    "subscription_settlement_days",
    "redemption_settlement_days",
)


@dataclass(frozen=True)
class LimitTerms:
    """Um limite de exposição: mínimo e máximo em % do PL para uma dimensão e um alvo."""

    dimension: LimitDimension
    target: str
    min_pct: Decimal
    max_pct: Decimal

    @property
    def key(self) -> tuple[LimitDimension, str]:
        return (self.dimension, self.target)


def _places(value: Decimal) -> int | None:
    """Casas decimais de um Decimal finito; None se for NaN ou infinito."""
    exponent = value.as_tuple().exponent
    if not isinstance(exponent, int):
        return None
    return max(0, -exponent)


def _within_places(value: Decimal, places: int) -> bool:
    found = _places(value)
    return found is not None and found <= places


def validate_terms(terms: MandateTerms, valid_asset_classes: frozenset[str]) -> MandateTerms:
    """Confere faixas e casas decimais do que foi preenchido. Devolve os termos normalizados."""
    if terms.risk_level is not None and not MIN_RISK_LEVEL <= terms.risk_level <= MAX_RISK_LEVEL:
        raise DomainError(
            f"Nível de risco vai de {MIN_RISK_LEVEL} a {MAX_RISK_LEVEL}.",
            code="mandate_risk_level_invalid",
        )
    spread = terms.target_return_spread_pct
    if spread is not None and (
        not _within_places(spread, SPREAD_PLACES) or abs(spread) >= MAX_SPREAD_PCT
    ):
        raise DomainError(
            "Spread do retorno-alvo: % ao ano, até 4 casas decimais.",
            code="mandate_target_return_invalid",
        )
    term_years = terms.max_average_term_years
    if term_years is not None and (
        not _within_places(term_years, TERM_YEARS_PLACES) or term_years <= 0
    ):
        raise DomainError(
            "Prazo médio máximo: anos, maior que zero, até 2 casas decimais.",
            code="mandate_average_term_invalid",
        )
    for name in _AMOUNT_FIELDS:
        amount: Decimal | None = getattr(terms, name)
        if amount is not None and (not _within_places(amount, AMOUNT_PLACES) or amount < 0):
            raise DomainError(
                "Valores de entrada e saída: zero ou mais, até 2 casas decimais.",
                code="mandate_amount_invalid",
            )
    for name in _COUNT_FIELDS:
        count: int | None = getattr(terms, name)
        if count is not None and count < 0:
            raise DomainError(
                "Prazos em dias ou meses não podem ser negativos.", code="mandate_term_invalid"
            )
    classes = tuple(sorted({code.strip().upper() for code in terms.eligible_asset_classes}))
    unknown = [code for code in classes if code not in valid_asset_classes]
    if unknown:
        raise DomainError(
            f"Classe de ativo desconhecida: {', '.join(unknown)}.",
            code="mandate_asset_class_unknown",
        )
    return replace(terms, eligible_asset_classes=classes, notes=terms.notes.strip())


def normalize_limit(limit: LimitTerms) -> LimitTerms:
    """Alvo sem espaços; códigos (classe, país, moeda) em maiúsculas; emissor em minúsculas."""
    target = limit.target.strip()
    if limit.dimension is LimitDimension.ISSUER:
        target = target.lower()
    elif limit.dimension is not LimitDimension.SINGLE_ASSET:
        target = target.upper()
    return replace(limit, target=target)


def validate_limits(
    limits: Sequence[LimitTerms], eligible_asset_classes: tuple[str, ...]
) -> tuple[LimitTerms, ...]:
    """Faixa 0 ≤ mín ≤ máx ≤ 100, alvo coerente com a dimensão, um limite por dimensão e alvo."""
    seen: set[tuple[LimitDimension, str]] = set()
    clean: list[LimitTerms] = []
    for raw in limits:
        limit = normalize_limit(raw)
        if limit.dimension is LimitDimension.SINGLE_ASSET and limit.target:
            raise DomainError(
                "Limite por ativo único vale para qualquer ativo: deixe o alvo vazio.",
                code="exposure_limit_target_not_allowed",
            )
        if limit.dimension is not LimitDimension.SINGLE_ASSET and not limit.target:
            raise DomainError("Informe o alvo do limite.", code="exposure_limit_target_required")
        if not (
            _within_places(limit.min_pct, PCT_PLACES)
            and _within_places(limit.max_pct, PCT_PLACES)
            and 0 <= limit.min_pct <= limit.max_pct <= HUNDRED
        ):
            raise DomainError(
                "Limite: 0 ≤ mínimo ≤ máximo ≤ 100, até 2 casas decimais.",
                code="exposure_limit_range_invalid",
            )
        if (
            limit.dimension is LimitDimension.ASSET_CLASS
            and limit.target not in eligible_asset_classes
        ):
            raise DomainError(
                f"A classe {limit.target} não está entre as classes elegíveis.",
                code="exposure_limit_asset_class_not_eligible",
            )
        if limit.key in seen:
            raise DomainError(
                f"Limite repetido para {limit.dimension.value} {limit.target}.".strip(),
                code="exposure_limit_duplicated",
            )
        seen.add(limit.key)
        clean.append(limit)
    return tuple(clean)


def check_draft(state: MandateState) -> None:
    """Só o rascunho é editado ou publicado."""
    if state is not MandateState.DRAFT:
        raise DomainError(
            "Versão publicada nunca muda: crie um rascunho novo.", code="mandate_not_draft"
        )


def check_publishable(terms: MandateTerms) -> None:
    """Para publicar, os termos obrigatórios e ao menos uma classe elegível."""
    missing = [name for name in REQUIRED_TO_PUBLISH if getattr(terms, name) is None]
    if not terms.eligible_asset_classes:
        missing.append("eligible_asset_classes")
    if missing:
        raise DomainError(
            f"Preencha antes de publicar: {', '.join(missing)}.", code="mandate_incomplete"
        )


def check_effective_date(effective_from: date, previous_effective_from: date | None) -> None:
    """A versão nova começa a valer depois da anterior."""
    if previous_effective_from is not None and effective_from <= previous_effective_from:
        raise DomainError(
            "A vigência da versão nova tem de começar depois da vigência da anterior "
            f"({previous_effective_from.isoformat()}).",
            code="mandate_effective_date_not_after_previous",
        )


def check_publish_reason(version: int, reason: str) -> str:
    """Da versão 2 em diante, publicar exige o motivo (vale para todos, inclusive quem comprou)."""
    clean = reason.strip()
    if version > 1 and not clean:
        raise DomainError(
            "Diga o motivo da versão nova: ela vale para todos, inclusive quem já comprou.",
            code="mandate_publish_reason_required",
        )
    return clean
