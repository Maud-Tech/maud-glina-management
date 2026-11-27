"""Formatos de saída usados por várias slices do módulo (o que a tela e a futura API recebem)."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema

from maud.modules.products.domain.mandate import (
    LimitDimension,
    LimitTerms,
    MandateTerms,
    ReturnBenchmark,
)
from maud.modules.products.models import (
    ExposureLimit,
    Mandate,
    Policy,
    Product,
    ProductDocument,
)


class ProductResponse(Schema):
    id: UUID
    code: str
    name: str
    description: str
    base_currency: str
    status: str
    launch_date: date | None
    closing_date: date | None


class PolicyResponse(Schema):
    id: UUID
    product_id: UUID
    policy_number: str
    insurer_entity_id: UUID
    currency: str
    issue_date: date | None
    effective_from: date
    effective_until: date | None
    status: str


class ExposureLimitResponse(Schema):
    id: UUID
    dimension: str
    target: str
    min_pct: Decimal
    max_pct: Decimal


class MandateResponse(Schema):
    id: UUID
    product_id: UUID
    version: int
    state: str
    effective_from: date | None
    risk_level: int | None
    target_return_benchmark: str
    target_return_spread_pct: Decimal | None
    liquidity_days: int | None
    max_average_term_years: Decimal | None
    eligible_asset_classes: list[str]
    min_initial_amount: Decimal | None
    min_additional_amount: Decimal | None
    subscription_settlement_days: int | None
    min_redemption_amount: Decimal | None
    min_balance_amount: Decimal | None
    redemption_notice_days: int | None
    redemption_settlement_days: int | None
    lock_up_months: int | None
    notes: str
    published_at: datetime | None
    exposure_limits: list[ExposureLimitResponse]


class DocumentResponse(Schema):
    id: UUID
    product_id: UUID
    policy_id: UUID | None
    document_type: str
    title: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime
    archived_at: datetime | None


def product_response(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        code=product.code,
        name=product.name,
        description=product.description,
        base_currency=product.base_currency_id,
        status=product.status,
        launch_date=product.launch_date,
        closing_date=product.closing_date,
    )


def policy_response(policy: Policy) -> PolicyResponse:
    return PolicyResponse(
        id=policy.id,
        product_id=policy.product_id,
        policy_number=policy.policy_number,
        insurer_entity_id=policy.insurer_entity_id,
        currency=policy.currency_id,
        issue_date=policy.issue_date,
        effective_from=policy.effective_from,
        effective_until=policy.effective_until,
        status=policy.status,
    )


def limit_response(limit: ExposureLimit) -> ExposureLimitResponse:
    return ExposureLimitResponse(
        id=limit.id,
        dimension=limit.dimension,
        target=limit.target,
        min_pct=limit.min_pct,
        max_pct=limit.max_pct,
    )


def mandate_response(mandate: Mandate) -> MandateResponse:
    limits = mandate.exposure_limits.order_by("dimension", "target")
    return MandateResponse(
        id=mandate.id,
        product_id=mandate.product_id,
        version=mandate.version,
        state=mandate.state,
        effective_from=mandate.effective_from,
        risk_level=mandate.risk_level,
        target_return_benchmark=mandate.target_return_benchmark,
        target_return_spread_pct=mandate.target_return_spread_pct,
        liquidity_days=mandate.liquidity_days,
        max_average_term_years=mandate.max_average_term_years,
        eligible_asset_classes=list(mandate.eligible_asset_classes),
        min_initial_amount=mandate.min_initial_amount,
        min_additional_amount=mandate.min_additional_amount,
        subscription_settlement_days=mandate.subscription_settlement_days,
        min_redemption_amount=mandate.min_redemption_amount,
        min_balance_amount=mandate.min_balance_amount,
        redemption_notice_days=mandate.redemption_notice_days,
        redemption_settlement_days=mandate.redemption_settlement_days,
        lock_up_months=mandate.lock_up_months,
        notes=mandate.notes,
        published_at=mandate.published_at,
        exposure_limits=[limit_response(limit) for limit in limits],
    )


def document_response(document: ProductDocument) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        product_id=document.product_id,
        policy_id=document.policy_id,
        document_type=document.document_type,
        title=document.title,
        content_type=document.content_type,
        size_bytes=document.size_bytes,
        uploaded_at=document.uploaded_at,
        archived_at=document.archived_at,
    )


def mandate_terms(mandate: Mandate) -> MandateTerms:
    """Os termos gravados, no formato das regras puras."""
    return MandateTerms(
        risk_level=mandate.risk_level,
        target_return_benchmark=ReturnBenchmark(mandate.target_return_benchmark),
        target_return_spread_pct=mandate.target_return_spread_pct,
        liquidity_days=mandate.liquidity_days,
        max_average_term_years=mandate.max_average_term_years,
        eligible_asset_classes=tuple(mandate.eligible_asset_classes),
        min_initial_amount=mandate.min_initial_amount,
        min_additional_amount=mandate.min_additional_amount,
        subscription_settlement_days=mandate.subscription_settlement_days,
        min_redemption_amount=mandate.min_redemption_amount,
        min_balance_amount=mandate.min_balance_amount,
        redemption_notice_days=mandate.redemption_notice_days,
        redemption_settlement_days=mandate.redemption_settlement_days,
        lock_up_months=mandate.lock_up_months,
        notes=mandate.notes,
    )


def mandate_limits(mandate: Mandate) -> tuple[LimitTerms, ...]:
    return tuple(
        LimitTerms(
            dimension=LimitDimension(limit.dimension),
            target=limit.target,
            min_pct=limit.min_pct,
            max_pct=limit.max_pct,
        )
        for limit in mandate.exposure_limits.order_by("dimension", "target")
    )
