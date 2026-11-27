"""Ação da tela do produto: ativar, inativar ou encerrar. Exige `products.change_product`.

Vem da confirmação no detalhe; a regra (o que pode e o que falta) é da slice.
"""

from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from maud.modules.products.display import PRODUCT_STATUS
from maud.modules.products.features.change_product_status.handler import (
    ChangeProductStatusCommand,
    execute,
)
from maud.modules.products.screens import (
    actor_id,
    detail_url,
)
from maud.shared.errors import DomainError, NotFoundError


@login_required
@permission_required("products.change_product", raise_exception=True)
@require_POST
def product_status(request: HttpRequest, product_id: UUID) -> HttpResponse:
    status = request.POST.get("status", "")
    try:
        product = execute(
            ChangeProductStatusCommand(
                actor_id=actor_id(request),
                product_id=product_id,
                status=status,
                reason=request.POST.get("reason", ""),
            )
        )
    except NotFoundError:
        raise Http404 from None
    except DomainError as error:
        messages.error(request, error.message)
    else:
        messages.success(request, f"Produto agora está {PRODUCT_STATUS[product.status].lower()}.")
    return redirect(detail_url(product_id))
