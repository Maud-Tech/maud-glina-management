"""Tela de editar o produto. Exige `products.change_product`.

Fora do rascunho, código e moeda base vêm travados (a slice recusa de novo se mudarem).
"""

from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from maud.modules.products.display import PRODUCT_STATUS
from maud.modules.products.domain.product import ProductStatus
from maud.modules.products.features.create_product.page import FIELD_BY_CODE, ProductForm
from maud.modules.products.features.update_product.handler import UpdateProductCommand, execute
from maud.modules.products.screens import (
    actor_id,
    add_domain_error,
    detail_url,
    product_detail_or_404,
    reason_field,
)
from maud.shared.errors import DomainError

TEMPLATE = "modules/products/features/update_product/page.html"


class EditProductForm(ProductForm):
    reason = reason_field()


@login_required
@permission_required("products.change_product", raise_exception=True)
def product_edit(request: HttpRequest, product_id: UUID) -> HttpResponse:
    product = product_detail_or_404(product_id).product
    if product.status == ProductStatus.CLOSED:
        messages.error(request, "Produto encerrado não muda.")
        return redirect(detail_url(product.id))
    initial = {
        "code": product.code,
        "name": product.name,
        "base_currency": product.base_currency,
        "description": product.description,
        "launch_date": product.launch_date,
        "closing_date": product.closing_date,
    }
    locked = product.status != ProductStatus.DRAFT
    form = EditProductForm(request.POST if request.method == "POST" else None, initial=initial)
    form.fields["code"].disabled = locked
    form.fields["base_currency"].disabled = locked
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            execute(
                UpdateProductCommand(
                    actor_id=actor_id(request),
                    product_id=product.id,
                    code=data["code"],
                    name=data["name"],
                    base_currency=data["base_currency"],
                    description=data["description"],
                    launch_date=data["launch_date"],
                    closing_date=data["closing_date"],
                    reason=data["reason"],
                )
            )
        except DomainError as error:
            add_domain_error(form, error, FIELD_BY_CODE)
        else:
            messages.success(request, "Alterações salvas.")
            return redirect(detail_url(product.id))
    return render(
        request,
        TEMPLATE,
        {
            "form": form,
            "product": product,
            "status_label": PRODUCT_STATUS[product.status],
            "locked": locked,
        },
        status=422 if form.errors else 200,
    )
