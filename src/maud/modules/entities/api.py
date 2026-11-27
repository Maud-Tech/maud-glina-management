"""Consultas públicas de cadastros para os módulos consumidores."""

from typing import Any, cast

from django.db.models import QuerySet

from maud.modules.entities.models import Country, Currency, Entity


def reference_queryset(kind: str) -> QuerySet[Any]:
    """Referências cadastrais; identidade central, nunca detalhes de pessoa/empresa."""
    registry: dict[str, Any] = {"country": Country, "currency": Currency, "entity": Entity}
    return cast(QuerySet[Any], registry[kind].objects.all().order_by("pk"))
