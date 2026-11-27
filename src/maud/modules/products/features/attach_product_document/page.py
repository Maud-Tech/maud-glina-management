"""Ação da aba Documentos: enviar um PDF. Exige `products.change_product`.

Contrato da apólice fica ligado à apólice do produto, quando houver.
"""

from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from maud.modules.products.features.attach_product_document.handler import (
    AttachProductDocumentCommand,
    execute,
)
from maud.modules.products.models import ProductDocument
from maud.modules.products.screens import (
    actor_id,
    detail_url,
    product_detail_or_404,
)
from maud.shared.errors import DomainError


@login_required
@permission_required("products.change_product", raise_exception=True)
@require_POST
def document_attach(request: HttpRequest, product_id: UUID) -> HttpResponse:
    detail = product_detail_or_404(product_id)
    upload = request.FILES.get("file")
    document_type = request.POST.get("document_type", "")
    if upload is None:
        messages.error(request, "Escolha o arquivo PDF.")
        return redirect(detail_url(product_id, "documents"))
    policy_id = (
        detail.policy.id
        if detail.policy and document_type == ProductDocument.Type.POLICY_CONTRACT
        else None
    )
    try:
        document = execute(
            AttachProductDocumentCommand(
                actor_id=actor_id(request),
                product_id=product_id,
                document_type=document_type,
                title=request.POST.get("title", ""),
                file=upload,
                policy_id=policy_id,
            )
        )
    except DomainError as error:
        messages.error(request, error.message)
    else:
        messages.success(request, f"Documento “{document.title}” enviado.")
    return redirect(detail_url(product_id, "documents"))
