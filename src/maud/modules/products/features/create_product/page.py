"""Tela de produto novo (nasce em rascunho). Exige `products.add_product`.

O formulário daqui também serve à tela de edição (`update_product/page.py`).
"""

from typing import Any

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from maud.modules.products.display import currency_options
from maud.modules.products.domain.product import DEFAULT_BASE_CURRENCY
from maud.modules.products.features.create_product.handler import CreateProductCommand, execute
from maud.modules.products.screens import (
    actor_id,
    add_domain_error,
    area_input,
    date_field,
    detail_url,
    select_input,
    set_choices,
    text_input,
)
from maud.shared.errors import DomainError

TEMPLATE = "modules/products/features/create_product/page.html"
FIELD_BY_CODE = {
    "product_code_invalid": "code",
    "product_code_taken": "code",
    "product_code_locked": "code",
    "product_name_required": "name",
    "product_name_too_long": "name",
    "product_dates_invalid": "closing_date",
    "currency_not_found": "base_currency",
    "product_currency_locked": "base_currency",
    "product_currency_has_policy": "base_currency",
}


class ProductForm(forms.Form):
    code = forms.CharField(max_length=50, widget=text_input(autocomplete="off"))
    name = forms.CharField(max_length=200, widget=text_input())
    base_currency = forms.ChoiceField(widget=select_input())
    description = forms.CharField(required=False, widget=area_input())
    launch_date = date_field()
    closing_date = date_field()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        set_choices(self, "base_currency", currency_options())


@login_required
@permission_required("products.add_product", raise_exception=True)
def product_new(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                product = execute(
                    CreateProductCommand(
                        actor_id=actor_id(request),
                        code=data["code"],
                        name=data["name"],
                        description=data["description"],
                        base_currency=data["base_currency"],
                        launch_date=data["launch_date"],
                        closing_date=data["closing_date"],
                    )
                )
            except DomainError as error:
                add_domain_error(form, error, FIELD_BY_CODE)
            else:
                messages.success(request, f"Produto {product.code} criado em rascunho.")
                return redirect(detail_url(product.id))
    else:
        form = ProductForm(initial={"base_currency": DEFAULT_BASE_CURRENCY})
    return render(request, TEMPLATE, {"form": form}, status=422 if form.errors else 200)
