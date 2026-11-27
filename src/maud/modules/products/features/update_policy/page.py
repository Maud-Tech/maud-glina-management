"""Tela de editar a apólice do produto. Exige `products.change_policy`.

Apólice expirada não muda.
"""

from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from maud.modules.products.domain.policy import PolicyStatus
from maud.modules.products.features.register_policy.page import FIELD_BY_CODE, PolicyForm
from maud.modules.products.features.update_policy.handler import UpdatePolicyCommand, execute
from maud.modules.products.screens import (
    actor_id,
    add_domain_error,
    detail_url,
    product_detail_or_404,
    reason_field,
)
from maud.shared.errors import DomainError

TEMPLATE = "modules/products/features/register_policy/page.html"


class EditPolicyForm(PolicyForm):
    reason = reason_field()


@login_required
@permission_required("products.change_policy", raise_exception=True)
def policy_edit(request: HttpRequest, product_id: UUID) -> HttpResponse:
    detail = product_detail_or_404(product_id)
    policy = detail.policy
    if policy is None:
        raise Http404
    if policy.status == PolicyStatus.EXPIRED:
        messages.error(request, "Apólice expirada não muda.")
        return redirect(detail_url(product_id, "policy"))
    initial = {
        "policy_number": policy.policy_number,
        "insurer_entity_id": str(policy.insurer_entity_id),
        "issue_date": policy.issue_date,
        "effective_from": policy.effective_from,
        "effective_until": policy.effective_until,
    }
    form = EditPolicyForm(request.POST if request.method == "POST" else None, initial=initial)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            execute(
                UpdatePolicyCommand(
                    actor_id=actor_id(request),
                    policy_id=policy.id,
                    policy_number=data["policy_number"],
                    insurer_entity_id=data["insurer_entity_id"],
                    effective_from=data["effective_from"],
                    effective_until=data["effective_until"],
                    issue_date=data["issue_date"],
                    reason=data["reason"],
                )
            )
        except DomainError as error:
            add_domain_error(form, error, FIELD_BY_CODE)
        else:
            messages.success(request, "Apólice alterada.")
            return redirect(detail_url(product_id, "policy"))
    return render(
        request,
        TEMPLATE,
        {"form": form, "product": detail.product, "editing": True},
        status=422 if form.errors else 200,
    )
