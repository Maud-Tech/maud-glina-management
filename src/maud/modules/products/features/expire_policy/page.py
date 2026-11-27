"""Ação da aba Apólice: expirar a apólice (e, com ela, o produto).

Exige `products.change_policy`.
"""

from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from maud.modules.products.features.expire_policy.handler import ExpirePolicyCommand, execute
from maud.modules.products.screens import (
    actor_id,
    detail_url,
    product_detail_or_404,
)
from maud.shared.errors import DomainError


@login_required
@permission_required("products.change_policy", raise_exception=True)
@require_POST
def policy_expire(request: HttpRequest, product_id: UUID) -> HttpResponse:
    policy = product_detail_or_404(product_id).policy
    if policy is None:
        raise Http404
    try:
        execute(
            ExpirePolicyCommand(
                actor_id=actor_id(request),
                policy_id=policy.id,
                reason=request.POST.get("reason", ""),
            )
        )
    except DomainError as error:
        messages.error(request, error.message)
    else:
        messages.success(request, f"Apólice {policy.policy_number} expirada.")
    return redirect(detail_url(product_id, "policy"))
