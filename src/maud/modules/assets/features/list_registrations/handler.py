"""Consulta paginada dos cadastros do próprio módulo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError
from django.core.paginator import Page, Paginator
from django.db.models import Q

from maud.modules.assets.registrations import REGISTRY


@dataclass(frozen=True)
class ListRegistrationsQuery:
    resource: str
    search: str = ""
    page: str = "1"
    variant: str = ""
    parent: str = ""


def execute(query: ListRegistrationsQuery) -> Page[Any]:
    spec = REGISTRY[query.resource]
    records = spec.model.objects.all().order_by("pk")
    if query.search:
        conditions = Q()
        for field in spec.search:
            conditions |= Q(**{field + "__icontains": query.search})
        records = records.filter(conditions)
    records = records.distinct()
    if spec.parent_field and query.parent:
        try:
            records = records.filter(**{spec.parent_field: query.parent})
        except (ValidationError, ValueError, TypeError):
            records = records.none()
    if spec.variant_field and query.variant in spec.variants:
        records = records.filter(**{spec.variant_field: query.variant})
    return Paginator(records.distinct(), 25).get_page(query.page)
