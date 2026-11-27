"""Listar produtos. Slice de CONSULTA (só lê).

Filtros: trecho do código ou do nome, e status. Cada linha traz a versão do regulamento que vale
hoje e o nível de risco dela (vazios enquanto não houver versão vigente) e a apólice, se houver.
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from django.db.models import Q
from ninja import Schema

from maud.modules.products.domain.mandate import MandateState
from maud.modules.products.domain.product import normalize_text
from maud.modules.products.models import Mandate, Policy, Product
from maud.shared.clock import get_clock


class ProductListItem(Schema):
    id: UUID
    code: str
    name: str
    status: str
    base_currency: str
    mandate_version: int | None
    risk_level: int | None
    policy_number: str | None = None
    policy_status: str | None = None
    policy_effective_until: date | None = None


@dataclass(frozen=True)
class ListProductsQuery:
    search: str | None = None
    status: str | None = None


def execute(query: ListProductsQuery) -> list[ProductListItem]:
    products = Product.objects.order_by("code")
    search = normalize_text(query.search or "")
    if search:
        products = products.filter(Q(code__icontains=search) | Q(name__icontains=search))
    if query.status:
        products = products.filter(status=query.status)
    rows = list(products)

    # Versão vigente hoje de cada produto, numa consulta só
    today = get_clock().now().date()
    current: dict[UUID, Mandate] = {}
    for mandate in Mandate.objects.filter(
        product_id__in=[product.id for product in rows],
        state=MandateState.PUBLISHED.value,
        effective_from__lte=today,
    ).order_by("product_id", "effective_from"):
        current[mandate.product_id] = mandate  # a última de cada produto fica
    policies = {
        policy.product_id: policy
        for policy in Policy.objects.filter(product_id__in=[product.id for product in rows])
    }

    return [
        ProductListItem(
            id=product.id,
            code=product.code,
            name=product.name,
            status=product.status,
            base_currency=product.base_currency_id,
            mandate_version=current[product.id].version if product.id in current else None,
            risk_level=current[product.id].risk_level if product.id in current else None,
            policy_number=policies[product.id].policy_number if product.id in policies else None,
            policy_status=policies[product.id].status if product.id in policies else None,
            policy_effective_until=(
                policies[product.id].effective_until if product.id in policies else None
            ),
        )
        for product in rows
    ]
