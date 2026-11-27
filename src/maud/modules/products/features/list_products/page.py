"""Tela da lista de produtos: busca, filtro de status e paginação. Exige `products.view_product`."""

from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from maud.modules.products.display import PRODUCT_STATUS, day
from maud.modules.products.features.list_products.handler import (
    ListProductsQuery,
    ProductListItem,
    execute,
)
from maud.modules.products.models import Policy

TEMPLATE = "modules/products/features/list_products/page.html"
PAGE_SIZE = 25


def policy_note(item: ProductListItem) -> str:
    if item.policy_number is None:
        return "sem apólice"
    if item.policy_status == Policy.Status.EXPIRED:
        return "expirada"
    if item.policy_effective_until is None:
        return "sem data final"
    return f"vigente até {day(item.policy_effective_until)}"


@login_required
@permission_required("products.view_product", raise_exception=True)
@require_GET
def product_list(request: HttpRequest) -> HttpResponse:
    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    items = execute(
        ListProductsQuery(
            search=search or None, status=status if status in PRODUCT_STATUS else None
        )
    )
    page = Paginator(items, PAGE_SIZE).get_page(request.GET.get("page"))
    rows = [
        {
            "item": item,
            "status_label": PRODUCT_STATUS[item.status],
            "mandate": f"v{item.mandate_version} · risco {item.risk_level}"
            if item.mandate_version
            else "—",
            "mandate_note": "" if item.mandate_version else "nenhuma versão em vigor",
            "policy": item.policy_number or "—",
            "policy_note": policy_note(item),
        }
        for item in page
    ]
    parameters = request.GET.copy()
    parameters.pop("page", None)
    return render(
        request,
        TEMPLATE,
        {
            "rows": rows,
            "page": page,
            "search": search,
            "status": status,
            "statuses": PRODUCT_STATUS.items(),
            "can_add": request.user.has_perm("products.add_product"),
            "page_query": urlencode(parameters),
        },
    )
