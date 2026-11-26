from django.contrib import admin
from django.http import HttpRequest

from maud.modules.assets.models import (
    Asset,
    AssetClassification,
    AssetEvent,
    AssetIdentifier,
    AssetListing,
    AssetPrice,
    CashAsset,
    DebtInstrument,
    Equity,
    Fund,
    GenericAsset,
    PriceSource,
    TradingVenue,
)


class ReadOnlyAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Consulta apenas; futuras escritas passarão pelas slices do módulo."""

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return False


@admin.register(TradingVenue)
class TradingVenueAdmin(ReadOnlyAdmin):
    list_display = ("code", "name", "country", "active")
    search_fields = ("code", "name")


@admin.register(Asset)
class AssetAdmin(ReadOnlyAdmin):
    list_display = ("name", "asset_family", "currency", "market_type", "status")
    search_fields = ("name", "short_name")
    list_filter = ("asset_family", "market_type", "status", "currency")


@admin.register(AssetListing)
class AssetListingAdmin(ReadOnlyAdmin):
    list_display = ("asset", "ticker", "trading_venue", "is_primary", "active")
    search_fields = ("asset__name", "ticker")
    list_filter = ("trading_venue", "is_primary", "active")


@admin.register(AssetIdentifier)
class AssetIdentifierAdmin(ReadOnlyAdmin):
    list_display = ("asset", "identifier_type", "value", "is_primary")
    search_fields = ("asset__name", "value")
    list_filter = ("identifier_type", "is_primary")


@admin.register(CashAsset)
class CashAssetAdmin(ReadOnlyAdmin):
    list_display = ("asset", "currency")


@admin.register(Equity)
class EquityAdmin(ReadOnlyAdmin):
    list_display = ("asset", "equity_type", "sector")
    list_filter = ("equity_type",)


@admin.register(DebtInstrument)
class DebtInstrumentAdmin(ReadOnlyAdmin):
    list_display = ("asset", "instrument_type", "debt_type", "maturity_date")
    list_filter = ("instrument_type", "debt_type", "perpetual")


@admin.register(Fund)
class FundAdmin(ReadOnlyAdmin):
    list_display = ("asset", "fund_type", "fund_name", "share_class", "domicile_country")
    search_fields = ("asset__name", "fund_name", "share_class")
    list_filter = ("fund_type", "domicile_country", "open_ended")


@admin.register(GenericAsset)
class GenericAssetAdmin(ReadOnlyAdmin):
    list_display = ("asset", "original_code", "normalization_status")
    search_fields = ("asset__name", "original_code")
    list_filter = ("normalization_status",)


@admin.register(AssetClassification)
class AssetClassificationAdmin(ReadOnlyAdmin):
    list_display = ("asset", "asset_class", "asset_subclass", "liquidity_type")
    list_filter = ("asset_class", "liquidity_type", "classification_source")


@admin.register(PriceSource)
class PriceSourceAdmin(ReadOnlyAdmin):
    list_display = ("code", "name", "priority", "active")
    search_fields = ("code", "name")


@admin.register(AssetPrice)
class AssetPriceAdmin(ReadOnlyAdmin):
    list_display = ("asset", "price_date", "price", "currency", "price_type", "source")
    list_filter = ("price_type", "source", "currency")


@admin.register(AssetEvent)
class AssetEventAdmin(ReadOnlyAdmin):
    list_display = (
        "asset",
        "event_date",
        "settlement_date",
        "event_type",
        "amount_paid",
        "cum_price",
        "factor",
        "event_status",
    )
    list_filter = ("event_type", "event_status")
