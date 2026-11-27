"""Tela de cadastrar a apólice do produto. Exige `products.add_policy`.

A seguradora vem das pessoas jurídicas do cadastro de entidades; a moeda é a do produto.
O formulário daqui também serve à edição (`update_policy/page.py`).
"""

from typing import Any
from uuid import UUID

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from maud.modules.products.display import insurer_options
from maud.modules.products.features.register_policy.handler import RegisterPolicyCommand, execute
from maud.modules.products.screens import (
    actor_id,
    add_domain_error,
    date_field,
    detail_url,
    product_detail_or_404,
    select_input,
    set_choices,
    text_input,
)
from maud.shared.errors import DomainError

TEMPLATE = "modules/products/features/register_policy/page.html"
FIELD_BY_CODE = {
    "policy_number_required": "policy_number",
    "policy_number_too_long": "policy_number",
    "policy_number_taken": "policy_number",
    "policy_dates_invalid": "effective_until",
    "insurer_not_found": "insurer_entity_id",
    "insurer_must_be_company": "insurer_entity_id",
}


class PolicyForm(forms.Form):
    policy_number = forms.CharField(max_length=100, widget=text_input(autocomplete="off"))
    insurer_entity_id = forms.TypedChoiceField(coerce=UUID, widget=select_input())
    issue_date = date_field()
    effective_from = date_field(required=True)
    effective_until = date_field()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        set_choices(
            self,
            "insurer_entity_id",
            [
                ("", "Escolha a seguradora"),
                *insurer_options(),
            ],
        )


@login_required
@permission_required("products.add_policy", raise_exception=True)
def policy_new(request: HttpRequest, product_id: UUID) -> HttpResponse:
    detail = product_detail_or_404(product_id)
    if detail.policy is not None:
        return redirect(detail_url(product_id, "policy"))
    form = PolicyForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            policy = execute(
                RegisterPolicyCommand(
                    actor_id=actor_id(request),
                    product_id=product_id,
                    policy_number=data["policy_number"],
                    insurer_entity_id=data["insurer_entity_id"],
                    effective_from=data["effective_from"],
                    effective_until=data["effective_until"],
                    issue_date=data["issue_date"],
                )
            )
        except DomainError as error:
            add_domain_error(form, error, FIELD_BY_CODE)
        else:
            messages.success(request, f"Apólice {policy.policy_number} cadastrada.")
            return redirect(detail_url(product_id, "policy"))
    return render(
        request,
        TEMPLATE,
        {"form": form, "product": detail.product, "editing": False},
        status=422 if form.errors else 200,
    )
