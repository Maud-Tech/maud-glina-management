"""Abrir o PDF de um documento, no navegador. Exige login e `products.view_product`."""

from uuid import UUID

from django.contrib.auth.decorators import login_required, permission_required
from django.http import FileResponse, Http404, HttpRequest
from django.views.decorators.http import require_GET

from maud.modules.products.features.open_product_document.handler import (
    OpenProductDocumentQuery,
    execute,
)
from maud.shared.errors import NotFoundError


@login_required
@permission_required("products.view_product", raise_exception=True)
@require_GET
def document_open(request: HttpRequest, product_id: UUID, document_id: UUID) -> FileResponse:
    try:
        document = execute(OpenProductDocumentQuery(product_id=product_id, document_id=document_id))
    except NotFoundError:
        raise Http404 from None
    response = FileResponse(
        document.content, content_type=document.content_type, filename=f"{document.title}.pdf"
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response
