from django.contrib import admin
from django.http import HttpRequest

from maud.modules.example.models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Somente leitura: escrita passa pela slice create_item (validação + evento).

    Se a operação precisar cadastrar pelo admin, o admin deve CHAMAR o handler da slice,
    nunca salvar o model direto (senão a validação e o evento do outbox não acontecem).
    """

    list_display = ("name", "is_active", "created_at")
    search_fields = ("name",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Item | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Item | None = None) -> bool:
        return False
