from django.contrib import admin
from django.http import HttpRequest

from maud.modules.entities.models import (
    Country,
    Currency,
    Entity,
    EntityAddress,
    EntityCompany,
    EntityContact,
    EntityPerson,
)


class ReadOnlyAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Consulta apenas; futuras escritas passarão pelas slices do módulo."""

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return False


@admin.register(Currency)
class CurrencyAdmin(ReadOnlyAdmin):
    list_display = ("code", "name", "symbol", "decimal_places", "active")
    search_fields = ("code", "name")


@admin.register(Country)
class CountryAdmin(ReadOnlyAdmin):
    list_display = ("code", "name", "currency")
    search_fields = ("code", "name")


@admin.register(Entity)
class EntityAdmin(ReadOnlyAdmin):
    list_display = ("display_name", "entity_kind", "registration_country", "updated_at")
    search_fields = ("display_name", "registration_number")
    list_filter = ("entity_kind", "registration_country")


@admin.register(EntityPerson)
class EntityPersonAdmin(ReadOnlyAdmin):
    list_display = ("full_name", "residence_country", "updated_at")
    search_fields = ("full_name",)


@admin.register(EntityCompany)
class EntityCompanyAdmin(ReadOnlyAdmin):
    list_display = ("legal_name", "trading_name", "incorporation_country", "updated_at")
    search_fields = ("legal_name", "trading_name")


@admin.register(EntityAddress)
class EntityAddressAdmin(ReadOnlyAdmin):
    list_display = ("entity", "address_type", "country", "is_primary")
    search_fields = ("entity__display_name", "address_line_1", "locality")
    list_filter = ("address_type", "country", "is_primary")


@admin.register(EntityContact)
class EntityContactAdmin(ReadOnlyAdmin):
    list_display = ("entity", "contact_type", "value", "is_primary")
    search_fields = ("entity__display_name", "value")
    list_filter = ("contact_type", "is_primary")
