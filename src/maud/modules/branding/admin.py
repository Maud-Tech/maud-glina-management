from django.contrib import admin
from django.http import HttpRequest

from maud.modules.branding.models import Branding


@admin.register(Branding)
class BrandingAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Somente leitura: quem grava é a tela de Personalização (slice update_branding)."""

    list_display = ("name", "brand_color", "updated_at")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Branding | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Branding | None = None) -> bool:
        return False
