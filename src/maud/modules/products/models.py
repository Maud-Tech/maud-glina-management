"""Só este módulo escreve nas tabelas de produtos, regulamentos, apólices, documentos e históricos.

Moeda e seguradora vêm do módulo entities (por string, sem importar o model). Os status e
escolhas têm a mesma fonte que as regras puras: os enums de `domain/`.
"""

import uuid
from pathlib import PurePath

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import F, Q

from maud.modules.products.domain.mandate import LimitDimension, MandateState, ReturnBenchmark
from maud.modules.products.domain.policy import PolicyStatus
from maud.modules.products.domain.product import ProductStatus
from maud.shared.db import append_only


def product_document_path(instance: "ProductDocument", filename: str) -> str:
    """Nome novo e imprevisível para cada arquivo; a extensão vem do formato conferido."""
    return f"products/{uuid.uuid4().hex}{PurePath(filename).suffix.lower()}"


class Product(models.Model):
    """O que a Glina mostra na vitrine."""

    class Status(models.TextChoices):
        DRAFT = ProductStatus.DRAFT.value, "Rascunho"
        ACTIVE = ProductStatus.ACTIVE.value, "Ativo"
        INACTIVE = ProductStatus.INACTIVE.value, "Inativo"
        EXPIRED = ProductStatus.EXPIRED.value, "Expirado"
        CLOSED = ProductStatus.CLOSED.value, "Encerrado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    base_currency = models.ForeignKey(
        "entities.Currency", on_delete=models.PROTECT, related_name="products"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    launch_date = models.DateField(null=True, blank=True)
    closing_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(launch_date__isnull=True)
                | Q(closing_date__isnull=True)
                | Q(closing_date__gte=F("launch_date")),
                name="ck_product_closing_after_launch",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} · {self.name}"


class Mandate(models.Model):
    """Regulamento do produto (apelido: mandato), em versões. Versão publicada nunca muda."""

    class State(models.TextChoices):
        DRAFT = MandateState.DRAFT.value, "Rascunho"
        PUBLISHED = MandateState.PUBLISHED.value, "Publicada"

    class Benchmark(models.TextChoices):
        SOFR = ReturnBenchmark.SOFR.value, "SOFR"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="mandates")
    version = models.PositiveIntegerField()
    state = models.CharField(max_length=20, choices=State.choices, default=State.DRAFT)
    effective_from = models.DateField(null=True, blank=True)
    risk_level = models.PositiveSmallIntegerField(null=True, blank=True)
    target_return_benchmark = models.CharField(
        max_length=20, choices=Benchmark.choices, default=Benchmark.SOFR
    )
    target_return_spread_pct = models.DecimalField(
        max_digits=8, decimal_places=4, null=True, blank=True
    )
    liquidity_days = models.PositiveIntegerField(null=True, blank=True)
    max_average_term_years = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    eligible_asset_classes = ArrayField(models.CharField(max_length=30), default=list, blank=True)
    min_initial_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    min_additional_amount = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    subscription_settlement_days = models.PositiveIntegerField(null=True, blank=True)
    min_redemption_amount = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    min_balance_amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    redemption_notice_days = models.PositiveIntegerField(null=True, blank=True)
    redemption_settlement_days = models.PositiveIntegerField(null=True, blank=True)
    lock_up_months = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "version"], name="uq_mandate_version"),
            models.UniqueConstraint(
                fields=["product"],
                condition=Q(state="DRAFT"),
                name="uq_mandate_one_draft_per_product",
            ),
            models.CheckConstraint(
                condition=Q(risk_level__isnull=True) | Q(risk_level__gte=1, risk_level__lte=5),
                name="ck_mandate_risk_level_1_to_5",
            ),
            models.CheckConstraint(
                condition=Q(state="DRAFT")
                | Q(effective_from__isnull=False, published_at__isnull=False),
                name="ck_mandate_published_has_date",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.code} v{self.version}"


class ExposureLimit(models.Model):
    """Mínimo e máximo em % do PL por dimensão e alvo. Pertence a uma versão do regulamento."""

    class Dimension(models.TextChoices):
        ASSET_CLASS = LimitDimension.ASSET_CLASS.value, "Classe de ativo"
        ISSUER = LimitDimension.ISSUER.value, "Emissor"
        SINGLE_ASSET = LimitDimension.SINGLE_ASSET.value, "Ativo único"
        COUNTRY = LimitDimension.COUNTRY.value, "País"
        CURRENCY = LimitDimension.CURRENCY.value, "Moeda"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mandate = models.ForeignKey(Mandate, on_delete=models.PROTECT, related_name="exposure_limits")
    dimension = models.CharField(max_length=20, choices=Dimension.choices)
    # Classe, país ou moeda: o código. Emissor: o id da Entity. Ativo único: vazio (qualquer ativo).
    target = models.CharField(max_length=64, blank=True, default="")
    min_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_pct = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["mandate", "dimension", "target"], name="uq_exposure_limit_target"
            ),
            models.CheckConstraint(
                condition=Q(min_pct__gte=0) & Q(min_pct__lte=F("max_pct")) & Q(max_pct__lte=100),
                name="ck_exposure_limit_range",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.dimension} {self.target} {self.min_pct}-{self.max_pct}%"


class Policy(models.Model):
    """Seguro feito com a seguradora. Um por produto, por enquanto."""

    class Status(models.TextChoices):
        ACTIVE = PolicyStatus.ACTIVE.value, "Ativa"
        EXPIRED = PolicyStatus.EXPIRED.value, "Expirada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="policies")
    policy_number = models.CharField(max_length=100)
    # Papel de uma Entity jurídica; a slice confere a natureza (regra do módulo entities).
    insurer_entity = models.ForeignKey(
        "entities.Entity", on_delete=models.PROTECT, related_name="insured_policies"
    )
    currency = models.ForeignKey(
        "entities.Currency", on_delete=models.PROTECT, related_name="policies"
    )
    issue_date = models.DateField(null=True, blank=True)
    effective_from = models.DateField()
    effective_until = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "policies"
        constraints = [
            # 1:1 por enquanto. Vários por produto = remover esta constraint.
            models.UniqueConstraint(fields=["product"], name="uq_policy_one_per_product"),
            models.UniqueConstraint(
                fields=["insurer_entity", "policy_number"], name="uq_policy_number_per_insurer"
            ),
            models.CheckConstraint(
                condition=Q(effective_until__isnull=True)
                | Q(effective_until__gt=F("effective_from")),
                name="ck_policy_effective_until_after_from",
            ),
        ]

    def __str__(self) -> str:
        return self.policy_number


class ProductDocument(models.Model):
    """PDF ligado ao produto e, se for o caso, à apólice. Arquivado, nunca apagado."""

    class Type(models.TextChoices):
        MANDATE = "MANDATE", "Regulamento"
        FACT_SHEET = "FACT_SHEET", "Lâmina"
        POLICY_CONTRACT = "POLICY_CONTRACT", "Contrato da apólice"
        OTHER = "OTHER", "Outro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="documents")
    policy = models.ForeignKey(
        Policy, on_delete=models.PROTECT, related_name="documents", null=True, blank=True
    )
    document_type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to=product_document_path)
    content_type = models.CharField(max_length=100)
    size_bytes = models.PositiveBigIntegerField()
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    uploaded_at = models.DateTimeField()
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.title


@append_only
class ProductChange(models.Model):
    """Histórico do produto, da apólice e dos documentos. Só INSERT (o banco recusa o resto)."""

    class ObjectType(models.TextChoices):
        PRODUCT = "PRODUCT", "Produto"
        POLICY = "POLICY", "Apólice"
        DOCUMENT = "DOCUMENT", "Documento"

    class Action(models.TextChoices):
        CREATED = "CREATED", "Criado"
        UPDATED = "UPDATED", "Alterado"
        STATUS_CHANGED = "STATUS_CHANGED", "Status alterado"
        ARCHIVED = "ARCHIVED", "Arquivado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="changes")
    object_type = models.CharField(max_length=20, choices=ObjectType.choices)
    object_id = models.UUIDField()
    action = models.CharField(max_length=20, choices=Action.choices)
    changes = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    reason = models.TextField(blank=True, default="")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    changed_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["product", "changed_at"], name="ix_product_change_time")]

    def __str__(self) -> str:
        return f"{self.object_type} {self.action}"


@append_only
class MandateChange(models.Model):
    """Histórico do regulamento e dos seus limites, do rascunho à publicação. Só INSERT."""

    class Action(models.TextChoices):
        CREATED = "CREATED", "Criado"
        UPDATED = "UPDATED", "Alterado"
        REMOVED = "REMOVED", "Removido"
        PUBLISHED = "PUBLISHED", "Publicado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mandate = models.ForeignKey(Mandate, on_delete=models.PROTECT, related_name="changes")
    # Não é chave estrangeira: limite removido do rascunho continua no histórico.
    exposure_limit_id = models.UUIDField(null=True, blank=True)
    action = models.CharField(max_length=20, choices=Action.choices)
    changes = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    reason = models.TextField(blank=True, default="")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    changed_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["mandate", "changed_at"], name="ix_mandate_change_time")]

    def __str__(self) -> str:
        return f"{self.mandate_id} {self.action}"
