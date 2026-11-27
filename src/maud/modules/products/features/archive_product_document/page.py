"""Ação da aba Documentos: arquivar (nunca apagar). Exige `products.change_product`."""

from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from maud.modules.products.features.archive_product_document.handler import (
    ArchiveProductDocumentCommand,
    execute,
)
from maud.modules.products.screens import (
    actor_id,
    detail_url,
    product_detail_or_404,
)
from maud.shared.errors import DomainError


@login_required
@permission_required("products.change_product", raise_exception=True)
@require_POST
def document_archive(request: HttpRequest, product_id: UUID, document_id: UUID) -> HttpResponse:
    if document_id not in {document.id for document in product_detail_or_404(product_id).documents}:
        raise Http404
    try:
        document = execute(
            ArchiveProductDocumentCommand(
                actor_id=actor_id(request),
                document_id=document_id,
                reason=request.POST.get("reason", ""),
            )
        )
    except DomainError as error:
        messages.error(request, error.message)
    else:
        messages.success(request, f"Documento “{document.title}” arquivado.")
    return redirect(detail_url(product_id, "documents"))
