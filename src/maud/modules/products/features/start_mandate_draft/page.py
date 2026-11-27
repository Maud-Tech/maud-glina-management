"""Ação da aba Regulamento: abrir o rascunho da próxima versão. Exige `products.change_mandate`.

Se já existe rascunho, leva a ele em vez de recusar.
"""

from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from maud.modules.products.features.start_mandate_draft.handler import (
    StartMandateDraftCommand,
    execute,
)
from maud.modules.products.screens import (
    actor_id,
    detail_url,
    product_detail_or_404,
)
from maud.shared.errors import DomainError


@login_required
@permission_required("products.change_mandate", raise_exception=True)
@require_POST
def mandate_start(request: HttpRequest, product_id: UUID) -> HttpResponse:
    detail = product_detail_or_404(product_id)
    if detail.draft_mandate is not None:
        return redirect(reverse("products_mandate", args=[product_id, detail.draft_mandate.id]))
    try:
        draft = execute(StartMandateDraftCommand(actor_id=actor_id(request), product_id=product_id))
    except DomainError as error:
        messages.error(request, error.message)
        return redirect(detail_url(product_id, "mandate"))
    messages.success(request, f"Rascunho da v{draft.version} aberto.")
    return redirect(reverse("products_mandate", args=[product_id, draft.id]))
