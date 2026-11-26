from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from django.apps import apps
from django.db import IntegrityError, transaction

from maud.modules.assets.models import (
    Asset,
    AssetEvent,
    AssetIdentifier,
    AssetListing,
    AssetPrice,
    CashAsset,
    DebtInstrument,
    GenericAsset,
    PriceSource,
    TradingVenue,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def usd() -> Any:
    currency_model = apps.get_model("entities", "Currency")
    return currency_model.objects.create(code="USD", name="US Dollar", symbol="US$")


@pytest.fixture
def united_states(usd: Any) -> Any:
    country_model = apps.get_model("entities", "Country")
    return country_model.objects.create(code="US", name="United States", currency=usd)


@pytest.fixture
def asset(usd: Any) -> Asset:
    return Asset.objects.create(
        asset_family=Asset.Family.EQUITY,
        name="Example Asset",
        short_name="EXAMPLE",
        currency=usd,
        market_type=Asset.MarketType.LISTED,
    )


@pytest.fixture
def venue(united_states: Any) -> TradingVenue:
    return TradingVenue.objects.create(
        code="NASDAQ",
        name="Nasdaq Stock Market",
        country=united_states,
    )


def test_asset_can_have_listings_on_multiple_venues(
    asset: Asset,
    venue: TradingVenue,
    united_states: Any,
) -> None:
    second_venue = TradingVenue.objects.create(
        code="NYSE",
        name="New York Stock Exchange",
        country=united_states,
    )
    AssetListing.objects.create(asset=asset, trading_venue=venue, ticker="EXM")
    AssetListing.objects.create(asset=asset, trading_venue=second_venue, ticker="EXM")

    assert asset.listings.count() == 2


def test_ticker_is_unique_inside_trading_venue(
    asset: Asset,
    venue: TradingVenue,
    usd: Any,
) -> None:
    AssetListing.objects.create(asset=asset, trading_venue=venue, ticker="EXM")
    second_asset = Asset.objects.create(
        asset_family=Asset.Family.EQUITY,
        name="Second Asset",
        short_name="SECOND",
        currency=usd,
        market_type=Asset.MarketType.LISTED,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        AssetListing.objects.create(
            asset=second_asset,
            trading_venue=venue,
            ticker="EXM",
        )


def test_identifier_type_and_value_are_globally_unique(asset: Asset, usd: Any) -> None:
    AssetIdentifier.objects.create(
        asset=asset,
        identifier_type=AssetIdentifier.Type.ISIN,
        value="US0000000001",
    )
    second_asset = Asset.objects.create(
        asset_family=Asset.Family.FUND,
        name="Second Asset",
        short_name="SECOND",
        currency=usd,
        market_type=Asset.MarketType.OTC,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        AssetIdentifier.objects.create(
            asset=second_asset,
            identifier_type=AssetIdentifier.Type.ISIN,
            value="US0000000001",
        )


def test_only_one_cash_asset_exists_for_each_currency(usd: Any) -> None:
    first_asset = Asset.objects.create(
        asset_family=Asset.Family.CASH,
        name="US Dollar",
        short_name="USD",
        currency=usd,
        market_type=Asset.MarketType.NOT_APPLICABLE,
    )
    CashAsset.objects.create(asset=first_asset, currency=usd)
    second_asset = Asset.objects.create(
        asset_family=Asset.Family.CASH,
        name="Duplicate US Dollar",
        short_name="USD 2",
        currency=usd,
        market_type=Asset.MarketType.NOT_APPLICABLE,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        CashAsset.objects.create(asset=second_asset, currency=usd)


def test_nonperpetual_debt_requires_maturity(asset: Asset) -> None:
    asset.asset_family = Asset.Family.DEBT
    asset.save(update_fields=["asset_family", "updated_at"])

    with pytest.raises(IntegrityError), transaction.atomic():
        DebtInstrument.objects.create(
            asset=asset,
            instrument_type=DebtInstrument.InstrumentType.BOND,
            debt_type=DebtInstrument.DebtType.CORPORATE,
            coupon_type=DebtInstrument.CouponType.FIXED,
            perpetual=False,
        )


def test_maturity_must_be_after_issue_date(asset: Asset) -> None:
    asset.asset_family = Asset.Family.DEBT
    asset.save(update_fields=["asset_family", "updated_at"])

    with pytest.raises(IntegrityError), transaction.atomic():
        DebtInstrument.objects.create(
            asset=asset,
            instrument_type=DebtInstrument.InstrumentType.BOND,
            debt_type=DebtInstrument.DebtType.CORPORATE,
            issue_date=date(2026, 1, 2),
            maturity_date=date(2026, 1, 1),
            coupon_type=DebtInstrument.CouponType.FIXED,
        )


def test_normalized_generic_asset_requires_destination(asset: Asset) -> None:
    asset.asset_family = Asset.Family.GENERIC
    asset.save(update_fields=["asset_family", "updated_at"])

    with pytest.raises(IntegrityError), transaction.atomic():
        GenericAsset.objects.create(
            asset=asset,
            raw_data={},
            normalization_status=GenericAsset.NormalizationStatus.NORMALIZED,
        )


def test_price_is_unique_by_asset_date_type_and_source(asset: Asset, usd: Any) -> None:
    source = PriceSource.objects.create(code="MANUAL", name="Manual", priority=1)
    price = {
        "asset": asset,
        "price_date": date(2026, 11, 26),
        "price": Decimal("10.000000000000"),
        "currency": usd,
        "price_type": AssetPrice.Type.MKT,
        "source": source,
    }
    AssetPrice.objects.create(**price)

    with pytest.raises(IntegrityError), transaction.atomic():
        AssetPrice.objects.create(**price)


def test_event_is_unique_by_asset_type_event_date_and_settlement(asset: Asset) -> None:
    event = {
        "asset": asset,
        "event_type": AssetEvent.Type.DIVIDEND,
        "event_date": date(2026, 11, 26),
        "settlement_date": None,
    }
    AssetEvent.objects.create(**event)

    with pytest.raises(IntegrityError), transaction.atomic():
        AssetEvent.objects.create(**event)


def test_event_settlement_cannot_precede_event_date(asset: Asset) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        AssetEvent.objects.create(
            asset=asset,
            event_type=AssetEvent.Type.INTEREST,
            event_date=date(2026, 11, 26),
            settlement_date=date(2026, 11, 25),
        )


def test_event_cum_price_must_be_positive(asset: Asset) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        AssetEvent.objects.create(
            asset=asset,
            event_type=AssetEvent.Type.DIVIDEND,
            event_date=date(2026, 11, 26),
            cum_price=Decimal("0"),
        )
