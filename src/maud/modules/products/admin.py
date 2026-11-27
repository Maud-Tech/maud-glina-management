from django.contrib import admin
from django.http import HttpRequest

from maud.modules.products.models import (
    ExposureLimit,
    Mandate,
    MandateChange,
    Policy,
    Product,
    ProductChange,
    ProductDocument,
)


class ReadOnlyAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Consulta apenas: escrita passa pelas slices (validação + histórico na mesma transação)."""

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: object | None = None) -> bool:
        return False


@admin.register(Product)
class ProductAdmin(ReadOnlyAdmin):
    list_display = ("code", "name", "base_currency", "status", "launch_date")
    list_filter = ("status",)
    search_fields = ("code", "name")


@admin.register(Mandate)
class MandateAdmin(ReadOnlyAdmin):
    list_display = ("product", "version", "state", "effective_from", "risk_level")
    list_filter = ("state",)


@admin.register(ExposureLimit)
class ExposureLimitAdmin(ReadOnlyAdmin):
    list_display = ("mandate", "dimension", "target", "min_pct", "max_pct")


@admin.register(Policy)
class PolicyAdmin(ReadOnlyAdmin):
    list_display = ("policy_number", "product", "insurer_entity", "status", "effective_from")
    list_filter = ("status",)


@admin.register(ProductDocument)
class ProductDocumentAdmin(ReadOnlyAdmin):
    list_display = ("title", "product", "document_type", "uploaded_at", "archived_at")


@admin.register(ProductChange)
class ProductChangeAdmin(ReadOnlyAdmin):
    list_display = ("product", "object_type", "action", "changed_by", "changed_at")


@admin.register(MandateChange)
class MandateChangeAdmin(ReadOnlyAdmin):
    list_display = ("mandate", "action", "exposure_limit_id", "changed_by", "changed_at")
