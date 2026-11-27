"""Ver um produto com tudo o que ele tem. Slice de CONSULTA (só lê).

Traz: o produto, a apólice, a versão do regulamento que vale hoje, a próxima versão já publicada
(vigência futura), o rascunho aberto e os documentos (vigentes primeiro, arquivados depois).
Erros: 404 product_not_found
"""

from dataclasses import dataclass
from uuid import UUID

from django.db.models import F
from ninja import Schema

from maud.modules.products.domain.mandate import MandateState
from maud.modules.products.models import Mandate, ProductDocument
from maud.modules.products.queries import current_mandate, get_product, product_policy
from maud.modules.products.responses import (
    DocumentResponse,
    MandateResponse,
    PolicyResponse,
    ProductResponse,
    document_response,
    mandate_response,
    policy_response,
    product_response,
)
from maud.shared.clock import get_clock


class ProductDetail(Schema):
    product: ProductResponse
    policy: PolicyResponse | None
    current_mandate: MandateResponse | None
    upcoming_mandate: MandateResponse | None
    draft_mandate: MandateResponse | None
    documents: list[DocumentResponse]


@dataclass(frozen=True)
class GetProductQuery:
    product_id: UUID


def execute(query: GetProductQuery) -> ProductDetail:
    product = get_product(query.product_id)
    today = get_clock().now().date()
    policy = product_policy(product.id)
    current = current_mandate(product.id, today)
    upcoming = (
        Mandate.objects.filter(
            product=product, state=MandateState.PUBLISHED.value, effective_from__gt=today
        )
        .order_by("effective_from")
        .first()
    )
    draft = Mandate.objects.filter(product=product, state=MandateState.DRAFT.value).first()
    documents = ProductDocument.objects.filter(product=product).order_by(
        F("archived_at").desc(nulls_first=True), "-uploaded_at"
    )
    return ProductDetail(
        product=product_response(product),
        policy=policy_response(policy) if policy else None,
        current_mandate=mandate_response(current) if current else None,
        upcoming_mandate=mandate_response(upcoming) if upcoming else None,
        draft_mandate=mandate_response(draft) if draft else None,
        documents=[document_response(document) for document in documents],
    )
