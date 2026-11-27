"""Dados prontos para os testes do módulo (as fixtures ficam no conftest.py ao lado)."""

from datetime import UTC, datetime
from decimal import Decimal

from maud.modules.products.domain.mandate import LimitDimension, LimitTerms, MandateTerms

NOW = datetime(2026, 12, 1, 12, 0, tzinfo=UTC)
TODAY = NOW.date()

COMPLETE_TERMS = MandateTerms(
    risk_level=2,
    target_return_spread_pct=Decimal("2.0000"),
    liquidity_days=30,
    max_average_term_years=Decimal("3.50"),
    eligible_asset_classes=("EQUITY", "FIXED_INCOME"),
    min_initial_amount=Decimal("10000.00"),
    subscription_settlement_days=2,
    redemption_settlement_days=5,
)
EQUITY_LIMIT = LimitTerms(
    dimension=LimitDimension.ASSET_CLASS,
    target="EQUITY",
    min_pct=Decimal("0"),
    max_pct=Decimal("20"),
)
