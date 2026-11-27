"""Apoio comum às telas do módulo (ADR 0010): campos de formulário e endereços.

A tela monta o comando e chama o handler da slice; erro de regra volta para o campo certo.
"""

from collections.abc import Iterable
from typing import Any
from uuid import UUID

from django import forms
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest
from django.urls import reverse

from maud.modules.products.features.get_product.handler import GetProductQuery, ProductDetail
from maud.modules.products.features.get_product.handler import execute as get_product
from maud.shared.errors import DomainError, NotFoundError

DATE_FORMAT = "%Y-%m-%d"  # o que o <input type="date"> manda


def text_input(**attrs: Any) -> forms.TextInput:
    return forms.TextInput(attrs={"class": "in", **attrs})


def date_input() -> forms.DateInput:
    return forms.DateInput(attrs={"class": "in", "type": "date"}, format=DATE_FORMAT)


def select_input() -> forms.Select:
    return forms.Select(attrs={"class": "in"})


def area_input(rows: int = 3, **attrs: Any) -> forms.Textarea:
    return forms.Textarea(attrs={"class": "in", "rows": rows, **attrs})


def date_field(*, required: bool = False) -> forms.DateField:
    return forms.DateField(required=required, input_formats=[DATE_FORMAT], widget=date_input())


def reason_field() -> forms.CharField:
    return forms.CharField(required=False, max_length=2000, widget=area_input(2))


def actor_id(request: HttpRequest) -> int:
    """Quem está operando (as telas exigem login antes de chegar aqui)."""
    if request.user.pk is None:
        raise PermissionDenied
    return int(request.user.pk)


def set_choices(form: forms.Form, name: str, choices: Iterable[tuple[str, str]]) -> None:
    field = form.fields[name]
    assert isinstance(field, forms.ChoiceField)
    field.choices = list(choices)


def add_domain_error(form: forms.Form, error: DomainError, field_by_code: dict[str, str]) -> None:
    """Põe a mensagem da regra no campo dela (ou no topo do formulário, se não for de um campo)."""
    form.add_error(field_by_code.get(error.code), error.message)


def product_detail_or_404(product_id: UUID) -> ProductDetail:
    try:
        return get_product(GetProductQuery(product_id=product_id))
    except NotFoundError:
        raise Http404 from None


def detail_url(product_id: UUID, tab: str | None = None) -> str:
    url = reverse("products_detail", args=[product_id])
    return f"{url}?tab={tab}" if tab else url
