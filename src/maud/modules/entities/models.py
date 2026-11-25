"""Só este módulo escreve nas tabelas de entidades e catálogos relacionados."""

import uuid

from django.db import models
from django.db.models import Q


class Currency(models.Model):
    """Moeda disponível para países e futuros ativos."""

    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    decimal_places = models.PositiveSmallIntegerField(default=2)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "currencies"
        constraints = [
            models.CheckConstraint(
                condition=Q(decimal_places__lte=8),
                name="ck_currency_decimal_places_lte_8",
            ),
        ]

    def __str__(self) -> str:
        return self.code


class Country(models.Model):
    """País identificado pelo código ISO 3166-1 alpha-2."""

    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=100)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="countries")

    class Meta:
        verbose_name_plural = "countries"

    def __str__(self) -> str:
        return self.name


class Entity(models.Model):
    """Identidade central referenciada pelos demais módulos de negócio."""

    class Kind(models.TextChoices):
        PERSON = "PERSON", "Pessoa física"
        COMPANY = "COMPANY", "Pessoa jurídica"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_kind = models.CharField(max_length=20, choices=Kind.choices)
    display_name = models.CharField(max_length=300)
    registration_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="registered_entities",
        null=True,
        blank=True,
    )
    registration_number = models.CharField(max_length=150, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "entities"
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(registration_country__isnull=True, registration_number="")
                    | (Q(registration_country__isnull=False) & ~Q(registration_number=""))
                ),
                name="ck_entity_registration_complete",
            ),
            models.UniqueConstraint(
                fields=["registration_country", "registration_number"],
                condition=~Q(registration_number=""),
                name="uq_entity_country_registration",
            ),
        ]

    def __str__(self) -> str:
        return self.display_name


class EntityPerson(models.Model):
    """Dados exclusivos de uma pessoa física."""

    entity = models.OneToOneField(
        Entity,
        on_delete=models.PROTECT,
        primary_key=True,
        related_name="person_details",
    )
    full_name = models.CharField(max_length=300)
    birth_date = models.DateField(null=True, blank=True)
    birth_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="people_born",
        null=True,
        blank=True,
    )
    residence_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="residents",
        null=True,
        blank=True,
    )
    nationality_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="nationals",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.full_name


class EntityCompany(models.Model):
    """Dados exclusivos de uma pessoa jurídica."""

    entity = models.OneToOneField(
        Entity,
        on_delete=models.PROTECT,
        primary_key=True,
        related_name="company_details",
    )
    legal_name = models.CharField(max_length=300)
    trading_name = models.CharField(max_length=300, blank=True, default="")
    incorporation_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="incorporated_companies",
    )
    sector = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "entity companies"

    def __str__(self) -> str:
        return self.legal_name


class EntityAddress(models.Model):
    """Endereço internacional de uma entidade."""

    class Type(models.TextChoices):
        RESIDENTIAL = "RESIDENTIAL", "Residencial"
        REGISTERED_OFFICE = "REGISTERED_OFFICE", "Sede registrada"
        BUSINESS = "BUSINESS", "Comercial"
        MAILING = "MAILING", "Correspondência"
        LEGAL = "LEGAL", "Legal"
        OTHER = "OTHER", "Outro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity = models.ForeignKey(Entity, on_delete=models.PROTECT, related_name="addresses")
    address_type = models.CharField(max_length=30, choices=Type.choices)
    address_line_1 = models.CharField(max_length=250)
    address_line_2 = models.CharField(max_length=250, blank=True, default="")
    address_line_3 = models.CharField(max_length=250, blank=True, default="")
    locality = models.CharField(max_length=150)
    administrative_area = models.CharField(max_length=150, blank=True, default="")
    postal_code = models.CharField(max_length=30, blank=True, default="")
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="addresses")
    formatted_address = models.TextField(blank=True, default="")
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entity", "address_type"],
                condition=Q(is_primary=True),
                name="uq_entity_primary_address_type",
            ),
        ]

    def __str__(self) -> str:
        return self.formatted_address or self.address_line_1


class EntityContact(models.Model):
    """E-mail ou telefone de uma entidade."""

    class Type(models.TextChoices):
        EMAIL = "EMAIL", "E-mail"
        PHONE = "PHONE", "Telefone"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity = models.ForeignKey(Entity, on_delete=models.PROTECT, related_name="contacts")
    contact_type = models.CharField(max_length=20, choices=Type.choices)
    value = models.CharField(max_length=320)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entity", "contact_type"],
                condition=Q(is_primary=True),
                name="uq_entity_primary_contact_type",
            ),
        ]

    def __str__(self) -> str:
        return self.value
