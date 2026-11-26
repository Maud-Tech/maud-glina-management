"""Só este módulo escreve nas tabelas de ativos, preços e eventos."""

import uuid

from django.db import models
from django.db.models import F, Q


class TimestampedModel(models.Model):
    """Timestamps técnicos compartilhados pelos cadastros do módulo."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TradingVenue(models.Model):
    """Casa de negociação na qual um ativo pode possuir uma listagem."""

    code = models.CharField(max_length=30, primary_key=True)
    name = models.CharField(max_length=150)
    country = models.ForeignKey(
        "entities.Country",
        on_delete=models.PROTECT,
        related_name="trading_venues",
    )
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.code


class Asset(TimestampedModel):
    """Identidade central de qualquer ativo."""

    class Family(models.TextChoices):
        CASH = "CASH", "Caixa"
        EQUITY = "EQUITY", "Renda variável"
        DEBT = "DEBT", "Instrumento de dívida"
        FUND = "FUND", "Fundo"
        GENERIC = "GENERIC", "Ativo genérico"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Ativo"
        INACTIVE = "INACTIVE", "Inativo"
        MATURED = "MATURED", "Vencido"

    class MarketType(models.TextChoices):
        LISTED = "LISTED", "Listado"
        OTC = "OTC", "Balcão"
        PRIVATE = "PRIVATE", "Privado"
        NOT_APPLICABLE = "NOT_APPLICABLE", "Não aplicável"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset_family = models.CharField(max_length=20, choices=Family.choices)
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=100)
    currency = models.ForeignKey(
        "entities.Currency",
        on_delete=models.PROTECT,
        related_name="assets",
    )
    issuer_entity = models.ForeignKey(
        "entities.Entity",
        on_delete=models.PROTECT,
        related_name="issued_assets",
        null=True,
        blank=True,
    )
    country_of_risk = models.ForeignKey(
        "entities.Country",
        on_delete=models.PROTECT,
        related_name="risk_assets",
        null=True,
        blank=True,
    )
    market_type = models.CharField(max_length=20, choices=MarketType.choices)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return self.name


class AssetListing(TimestampedModel):
    """Ticker de um ativo em uma casa de negociação."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="listings")
    trading_venue = models.ForeignKey(
        TradingVenue,
        on_delete=models.PROTECT,
        related_name="listings",
    )
    ticker = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["trading_venue", "ticker"],
                name="uq_listing_venue_ticker",
            ),
            models.UniqueConstraint(
                fields=["asset", "trading_venue"],
                name="uq_listing_asset_venue",
            ),
            models.UniqueConstraint(
                fields=["asset"],
                condition=Q(is_primary=True),
                name="uq_listing_primary_asset",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.ticker}@{self.trading_venue_id}"


class AssetIdentifier(models.Model):
    """Identificador externo ou interno de um ativo."""

    class Type(models.TextChoices):
        ISIN = "ISIN", "ISIN"
        CUSIP = "CUSIP", "CUSIP"
        SEDOL = "SEDOL", "SEDOL"
        FIGI = "FIGI", "FIGI"
        BLOOMBERG_ID = "BLOOMBERG_ID", "Bloomberg ID"
        RIC = "RIC", "RIC"
        INTERNAL = "INTERNAL", "Interno"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="identifiers")
    identifier_type = models.CharField(max_length=20, choices=Type.choices)
    value = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["identifier_type", "value"],
                name="uq_asset_identifier_type_value",
            ),
            models.UniqueConstraint(
                fields=["asset", "identifier_type"],
                condition=Q(is_primary=True),
                name="uq_asset_primary_identifier_type",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.identifier_type}:{self.value}"


class CashAsset(models.Model):
    """Moeda representada como ativo único e compartilhado."""

    asset = models.OneToOneField(
        Asset,
        on_delete=models.PROTECT,
        primary_key=True,
        related_name="cash_details",
    )
    currency = models.OneToOneField(
        "entities.Currency",
        on_delete=models.PROTECT,
        related_name="cash_asset",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.currency_id


class Equity(TimestampedModel):
    """Detalhes de ação, recibo ou unidade negociável."""

    class Type(models.TextChoices):
        COMMON_STOCK = "COMMON_STOCK", "Ação ordinária"
        PREFERRED_STOCK = "PREFERRED_STOCK", "Ação preferencial"
        ADR = "ADR", "ADR"
        GDR = "GDR", "GDR"
        REIT = "REIT", "REIT"
        BDC = "BDC", "BDC"
        PARTNERSHIP_UNIT = "PARTNERSHIP_UNIT", "Unidade de parceria"
        OTHER = "OTHER", "Outro"

    class DividendFrequency(models.TextChoices):
        MONTHLY = "MONTHLY", "Mensal"
        QUARTERLY = "QUARTERLY", "Trimestral"
        SEMIANNUAL = "SEMIANNUAL", "Semestral"
        ANNUAL = "ANNUAL", "Anual"
        IRREGULAR = "IRREGULAR", "Irregular"
        NONE = "NONE", "Nenhuma"

    asset = models.OneToOneField(
        Asset,
        on_delete=models.PROTECT,
        primary_key=True,
        related_name="equity_details",
    )
    equity_type = models.CharField(max_length=30, choices=Type.choices)
    sector = models.CharField(max_length=100, blank=True, default="")
    industry = models.CharField(max_length=100, blank=True, default="")
    voting_rights = models.BooleanField(default=False)
    dividend_frequency = models.CharField(
        max_length=20,
        choices=DividendFrequency.choices,
        blank=True,
        default="",
    )
    underlying_asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name="depositary_receipts",
        null=True,
        blank=True,
    )
    depositary_ratio = models.DecimalField(
        max_digits=28,
        decimal_places=8,
        null=True,
        blank=True,
    )
    shares_outstanding = models.DecimalField(
        max_digits=28,
        decimal_places=8,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name_plural = "equities"
        constraints = [
            models.CheckConstraint(
                condition=Q(depositary_ratio__isnull=True) | Q(depositary_ratio__gt=0),
                name="ck_equity_depositary_ratio_positive",
            ),
            models.CheckConstraint(
                condition=Q(shares_outstanding__isnull=True) | Q(shares_outstanding__gte=0),
                name="ck_equity_shares_nonnegative",
            ),
        ]

    def __str__(self) -> str:
        return str(self.asset)


class DebtInstrument(TimestampedModel):
    """Detalhes comuns de bonds, notes e demais instrumentos de dívida."""

    class InstrumentType(models.TextChoices):
        BOND = "BOND", "Bond"
        NOTE = "NOTE", "Note"
        CERTIFICATE_OF_DEPOSIT = "CERTIFICATE_OF_DEPOSIT", "Certificado de depósito"
        COMMERCIAL_PAPER = "COMMERCIAL_PAPER", "Commercial paper"
        STRUCTURED_NOTE = "STRUCTURED_NOTE", "Nota estruturada"
        OTHER = "OTHER", "Outro"

    class DebtType(models.TextChoices):
        SOVEREIGN = "SOVEREIGN", "Soberana"
        CORPORATE = "CORPORATE", "Corporativa"
        MUNICIPAL = "MUNICIPAL", "Municipal"
        SUPRANATIONAL = "SUPRANATIONAL", "Supranacional"
        FINANCIAL_INSTITUTION = "FINANCIAL_INSTITUTION", "Instituição financeira"
        OTHER = "OTHER", "Outro"

    class CouponType(models.TextChoices):
        FIXED = "FIXED", "Fixo"
        FLOATING = "FLOATING", "Flutuante"
        ZERO_COUPON = "ZERO_COUPON", "Sem cupom"
        INFLATION_LINKED = "INFLATION_LINKED", "Ligado à inflação"
        VARIABLE = "VARIABLE", "Variável"
        CONDITIONAL = "CONDITIONAL", "Condicional"
        NONE = "NONE", "Nenhum"

    class Seniority(models.TextChoices):
        SENIOR_SECURED = "SENIOR_SECURED", "Sênior garantida"
        SENIOR_UNSECURED = "SENIOR_UNSECURED", "Sênior sem garantia"
        SUBORDINATED = "SUBORDINATED", "Subordinada"
        JUNIOR = "JUNIOR", "Júnior"
        MEZZANINE = "MEZZANINE", "Mezanino"
        PREFERRED = "PREFERRED", "Preferencial"
        OTHER = "OTHER", "Outra"

    asset = models.OneToOneField(
        Asset,
        on_delete=models.PROTECT,
        primary_key=True,
        related_name="debt_details",
    )
    instrument_type = models.CharField(max_length=30, choices=InstrumentType.choices)
    debt_type = models.CharField(max_length=30, choices=DebtType.choices)
    guarantor_entity = models.ForeignKey(
        "entities.Entity",
        on_delete=models.PROTECT,
        related_name="guaranteed_debt_instruments",
        null=True,
        blank=True,
    )
    insurer_entity = models.ForeignKey(
        "entities.Entity",
        on_delete=models.PROTECT,
        related_name="insured_debt_instruments",
        null=True,
        blank=True,
    )
    issue_date = models.DateField(null=True, blank=True)
    maturity_date = models.DateField(null=True, blank=True)
    minimum_lot = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    coupon_type = models.CharField(max_length=30, choices=CouponType.choices)
    coupon_rate = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    reference_rate = models.CharField(max_length=30, blank=True, default="")
    day_count_convention = models.CharField(max_length=20, blank=True, default="")
    seniority = models.CharField(
        max_length=30,
        choices=Seniority.choices,
        blank=True,
        default="",
    )
    secured = models.BooleanField(default=False)
    perpetual = models.BooleanField(default=False)
    callable = models.BooleanField(default=False)
    putable = models.BooleanField(default=False)
    convertible = models.BooleanField(default=False)
    defaulted = models.BooleanField(default=False)
    issue_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    redemption_value = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(minimum_lot__isnull=True) | Q(minimum_lot__gt=0),
                name="ck_debt_minimum_lot_positive",
            ),
            models.CheckConstraint(
                condition=(
                    Q(issue_date__isnull=True)
                    | Q(maturity_date__isnull=True)
                    | Q(maturity_date__gt=F("issue_date"))
                ),
                name="ck_debt_maturity_after_issue",
            ),
            models.CheckConstraint(
                condition=(
                    Q(perpetual=True, maturity_date__isnull=True)
                    | Q(perpetual=False, maturity_date__isnull=False)
                ),
                name="ck_debt_perpetual_maturity",
            ),
            models.CheckConstraint(
                condition=Q(coupon_rate__isnull=True) | Q(coupon_rate__gte=0),
                name="ck_debt_coupon_rate_nonnegative",
            ),
        ]

    def __str__(self) -> str:
        return str(self.asset)


class Fund(TimestampedModel):
    """Detalhes de uma classe de cotas negociável de um fundo."""

    class Type(models.TextChoices):
        ETF = "ETF", "ETF"
        MUTUAL_FUND = "MUTUAL_FUND", "Mutual fund"
        MONEY_MARKET_FUND = "MONEY_MARKET_FUND", "Money market fund"
        HEDGE_FUND = "HEDGE_FUND", "Hedge fund"
        PRIVATE_EQUITY_FUND = "PRIVATE_EQUITY_FUND", "Private equity fund"
        VENTURE_CAPITAL_FUND = "VENTURE_CAPITAL_FUND", "Venture capital fund"
        PRIVATE_CREDIT_FUND = "PRIVATE_CREDIT_FUND", "Private credit fund"
        REAL_ESTATE_FUND = "REAL_ESTATE_FUND", "Real estate fund"
        INFRASTRUCTURE_FUND = "INFRASTRUCTURE_FUND", "Infrastructure fund"
        COMMODITY_FUND = "COMMODITY_FUND", "Commodity fund"
        OTHER = "OTHER", "Outro"

    class DistributionPolicy(models.TextChoices):
        ACCUMULATING = "ACCUMULATING", "Acumulação"
        DISTRIBUTING = "DISTRIBUTING", "Distribuição"
        MIXED = "MIXED", "Mista"

    asset = models.OneToOneField(
        Asset,
        on_delete=models.PROTECT,
        primary_key=True,
        related_name="fund_details",
    )
    fund_type = models.CharField(max_length=30, choices=Type.choices)
    fund_name = models.CharField(max_length=200)
    share_class = models.CharField(max_length=100, blank=True, default="")
    parent_fund = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="share_classes",
        null=True,
        blank=True,
    )
    domicile_country = models.ForeignKey(
        "entities.Country",
        on_delete=models.PROTECT,
        related_name="domiciled_funds",
    )
    manager_entity = models.ForeignKey(
        "entities.Entity",
        on_delete=models.PROTECT,
        related_name="managed_funds",
        null=True,
        blank=True,
    )
    administrator_entity = models.ForeignKey(
        "entities.Entity",
        on_delete=models.PROTECT,
        related_name="administered_funds",
        null=True,
        blank=True,
    )
    custodian_entity = models.ForeignKey(
        "entities.Entity",
        on_delete=models.PROTECT,
        related_name="custodied_funds",
        null=True,
        blank=True,
    )
    legal_structure = models.CharField(max_length=50, blank=True, default="")
    open_ended = models.BooleanField(default=True)
    inception_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    nav_frequency = models.CharField(max_length=20, blank=True, default="")
    dealing_frequency = models.CharField(max_length=20, blank=True, default="")
    subscription_settlement_days = models.PositiveSmallIntegerField(null=True, blank=True)
    redemption_notice_days = models.PositiveSmallIntegerField(null=True, blank=True)
    redemption_settlement_days = models.PositiveSmallIntegerField(null=True, blank=True)
    lockup_days = models.PositiveIntegerField(null=True, blank=True)
    management_fee_pct = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        null=True,
        blank=True,
    )
    performance_fee_pct = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        null=True,
        blank=True,
    )
    high_water_mark = models.BooleanField(default=False)
    benchmark_asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name="benchmark_for_funds",
        null=True,
        blank=True,
    )
    distribution_policy = models.CharField(max_length=20, choices=DistributionPolicy.choices)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(termination_date__isnull=True)
                    | Q(inception_date__isnull=True)
                    | Q(termination_date__gte=F("inception_date"))
                ),
                name="ck_fund_termination_after_inception",
            ),
            models.CheckConstraint(
                condition=Q(management_fee_pct__isnull=True) | Q(management_fee_pct__gte=0),
                name="ck_fund_management_fee_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(performance_fee_pct__isnull=True) | Q(performance_fee_pct__gte=0),
                name="ck_fund_performance_fee_nonnegative",
            ),
        ]

    def __str__(self) -> str:
        return self.fund_name


class GenericAsset(TimestampedModel):
    """Área temporária para ativos recebidos ainda não normalizados."""

    class NormalizationStatus(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        IN_REVIEW = "IN_REVIEW", "Em revisão"
        NORMALIZED = "NORMALIZED", "Normalizado"
        IGNORED = "IGNORED", "Ignorado"

    asset = models.OneToOneField(
        Asset,
        on_delete=models.PROTECT,
        primary_key=True,
        related_name="generic_details",
    )
    generic_type = models.CharField(max_length=100, blank=True, default="")
    original_code = models.CharField(max_length=100)
    raw_data = models.JSONField(default=dict)
    normalization_status = models.CharField(
        max_length=20,
        choices=NormalizationStatus.choices,
        default=NormalizationStatus.PENDING,
    )
    normalization_notes = models.TextField(blank=True, default="")
    normalized_asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name="normalized_from_generic_assets",
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(normalization_status="NORMALIZED") | Q(normalized_asset__isnull=False),
                name="ck_generic_normalized_asset_required",
            ),
        ]

    def __str__(self) -> str:
        return str(self.asset)


class AssetClassification(TimestampedModel):
    """Classificação estratégica e de liquidez de um ativo."""

    class AssetClass(models.TextChoices):
        CASH = "CASH", "Caixa"
        FIXED_INCOME = "FIXED_INCOME", "Renda fixa"
        EQUITY = "EQUITY", "Renda variável"
        REAL_ESTATE = "REAL_ESTATE", "Imobiliário"
        ALTERNATIVES = "ALTERNATIVES", "Alternativos"
        COMMODITIES = "COMMODITIES", "Commodities"

    class LiquidityType(models.TextChoices):
        DAYS = "DAYS", "Dias"
        AT_MATURITY = "AT_MATURITY", "No vencimento"
        EVENT_BASED = "EVENT_BASED", "Baseada em evento"
        OTHER = "OTHER", "Outra"

    class Source(models.TextChoices):
        AUTOMATIC = "AUTOMATIC", "Automática"
        MANUAL = "MANUAL", "Manual"
        IMPORTED = "IMPORTED", "Importada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.OneToOneField(
        Asset,
        on_delete=models.PROTECT,
        related_name="classification",
    )
    asset_class = models.CharField(max_length=30, choices=AssetClass.choices)
    asset_subclass = models.CharField(max_length=50, blank=True, default="")
    region = models.CharField(max_length=50, blank=True, default="")
    liquidity_type = models.CharField(max_length=20, choices=LiquidityType.choices)
    liquidity_days = models.PositiveIntegerField(null=True, blank=True)
    classification_source = models.CharField(max_length=20, choices=Source.choices)
    risk_factors = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(liquidity_type="DAYS") | Q(liquidity_days__isnull=False),
                name="ck_classification_liquidity_days_required",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.asset}:{self.asset_class}"


class PriceSource(models.Model):
    """Origem de uma observação de preço."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    priority = models.PositiveSmallIntegerField()
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.code


class AssetPrice(models.Model):
    """Preço de um ativo para uma data, tipo e fonte."""

    class Type(models.TextChoices):
        MKT = "MKT", "Mercado"
        MD = "MD", "Última cotação de mercado disponível"
        CURVE = "CURVE", "Curva"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="prices")
    price_date = models.DateField()
    price = models.DecimalField(max_digits=30, decimal_places=12)
    currency = models.ForeignKey(
        "entities.Currency",
        on_delete=models.PROTECT,
        related_name="asset_prices",
    )
    price_type = models.CharField(max_length=20, choices=Type.choices)
    source = models.ForeignKey(PriceSource, on_delete=models.PROTECT, related_name="prices")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["asset", "price_date", "price_type", "source"],
                name="uq_asset_price_date_type_source",
            ),
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="ck_asset_price_nonnegative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.asset}:{self.price_date}:{self.price_type}"


class AssetEvent(models.Model):
    """Evento econômico ou societário associado a um ativo."""

    class Type(models.TextChoices):
        DIVIDEND = "DIVIDEND", "Dividendo"
        INTEREST = "INTEREST", "Juros"
        COUPON = "COUPON", "Cupom"
        AMORTIZATION = "AMORTIZATION", "Amortização"
        MATURITY = "MATURITY", "Vencimento"
        REDEMPTION = "REDEMPTION", "Resgate"
        CALL = "CALL", "Call"
        PUT = "PUT", "Put"
        STOCK_SPLIT = "STOCK_SPLIT", "Desdobramento"
        REVERSE_SPLIT = "REVERSE_SPLIT", "Grupamento"
        SPIN_OFF = "SPIN_OFF", "Spin-off"
        CAPITAL_CALL = "CAPITAL_CALL", "Chamada de capital"
        CAPITAL_DISTRIBUTION = "CAPITAL_DISTRIBUTION", "Distribuição de capital"
        FUND_DISTRIBUTION = "FUND_DISTRIBUTION", "Distribuição de fundo"
        PREMIUM = "PREMIUM", "Prêmio"
        INTEREST_ON_EQUITY = "INTEREST_ON_EQUITY", "JCP"
        OTHER = "OTHER", "Outro"

    class Status(models.TextChoices):
        SETTLED = "SETTLED", "Liquidado"
        EXPECTED = "EXPECTED", "Previsto"
        UNSETTLED = "UNSETTLED", "Não liquidado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="events")
    event_type = models.CharField(max_length=30, choices=Type.choices)
    event_date = models.DateField()
    settlement_date = models.DateField(null=True, blank=True)
    percentage_rate = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        null=True,
        blank=True,
    )
    amount_paid = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
    )
    cum_price = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
    )
    currency = models.ForeignKey(
        "entities.Currency",
        on_delete=models.PROTECT,
        related_name="asset_events",
        null=True,
        blank=True,
    )
    factor = models.DecimalField(max_digits=28, decimal_places=8, null=True, blank=True)
    event_status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.EXPECTED,
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["asset", "event_type", "event_date", "settlement_date"],
                name="uq_asset_event_identity",
                nulls_distinct=False,
            ),
            models.CheckConstraint(
                condition=Q(percentage_rate__isnull=True) | Q(percentage_rate__gte=0),
                name="ck_asset_event_rate_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(amount_paid__isnull=True) | Q(amount_paid__gte=0),
                name="ck_asset_event_amount_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(cum_price__isnull=True) | Q(cum_price__gt=0),
                name="ck_asset_event_cum_price_positive",
            ),
            models.CheckConstraint(
                condition=Q(factor__isnull=True) | Q(factor__gt=0),
                name="ck_asset_event_factor_positive",
            ),
            models.CheckConstraint(
                condition=Q(settlement_date__isnull=True) | Q(settlement_date__gte=F("event_date")),
                name="ck_asset_event_settlement_after_event",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.asset}:{self.event_type}"
