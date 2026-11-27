"""Etapa 04 do regulamento: publicar o rascunho. Exige `products.change_mandate`.

Mostra o que muda em relação à versão anterior e pede a vigência (depois da anterior) e o motivo
(obrigatório da v2 em diante). Quem confere é a slice.
"""

from datetime import timedelta
from typing import Any
from uuid import UUID

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from maud.modules.products.display import (
    FLOW_TERMS,
    PROFILE_TERMS,
    limit_rows,
    limit_target_options,
    term_text,
)
from maud.modules.products.domain.mandate import MandateState
from maud.modules.products.features.publish_mandate.handler import PublishMandateCommand, execute
from maud.modules.products.features.update_mandate_draft.page import (
    STEPS,
    load_mandate,
    mandate_context,
)
from maud.modules.products.models import Mandate
from maud.modules.products.screens import (
    actor_id,
    add_domain_error,
    area_input,
    date_field,
    detail_url,
)
from maud.shared.clock import get_clock
from maud.shared.errors import DomainError

TEMPLATE = "modules/products/features/publish_mandate/page.html"
FIELD_BY_CODE = {
    "mandate_effective_date_not_after_previous": "effective_from",
    "mandate_publish_reason_required": "reason",
}


class PublishForm(forms.Form):
    effective_from = date_field(required=True)
    reason = forms.CharField(required=False, max_length=2000, widget=area_input())


def what_changes(mandate: Mandate, previous: Mandate | None, currency: str) -> list[str]:
    """Frases do que muda em relação à versão anterior (termos e limites)."""
    if previous is None:
        return []
    lines = []
    for name, label in PROFILE_TERMS + FLOW_TERMS:
        before, after = term_text(name, previous, currency), term_text(name, mandate, currency)
        if before != after:
            lines.append(f"{label}: {before} → {after}")
    options = limit_target_options()
    old = {
        row["label"]: row["value"] for row in limit_rows(previous.exposure_limits.all(), options)
    }
    new = {row["label"]: row["value"] for row in limit_rows(mandate.exposure_limits.all(), options)}
    for label, value in new.items():
        if label not in old:
            lines.append(f"Limite novo: {label}, {value}")
        elif old[label] != value:
            lines.append(f"Limite {label}: {old[label]} → {value}")
    lines.extend(f"Limite sai: {label}" for label in old if label not in new)
    return lines


@login_required
@permission_required("products.change_mandate", raise_exception=True)
def mandate_publish(request: HttpRequest, product_id: UUID, mandate_id: UUID) -> HttpResponse:
    mandate = load_mandate(product_id, mandate_id)
    if mandate.state != MandateState.DRAFT:
        return redirect(reverse("products_mandate", args=[product_id, mandate.id]))
    context = mandate_context(product_id, mandate)
    previous: Mandate | None = context["previous"]
    today = get_clock().now().date()
    suggested = today
    if previous is not None and previous.effective_from and previous.effective_from >= today:
        suggested = previous.effective_from + timedelta(days=1)
    form = PublishForm(
        request.POST if request.method == "POST" else None,
        initial={"effective_from": suggested},
    )
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            published = execute(
                PublishMandateCommand(
                    actor_id=actor_id(request),
                    mandate_id=mandate.id,
                    effective_from=data["effective_from"],
                    reason=data["reason"],
                )
            )
        except DomainError as error:
            add_domain_error(form, error, FIELD_BY_CODE)
        else:
            messages.success(
                request,
                f"Regulamento v{published.version} publicado. Vale para todos a partir de "
                f"{published.effective_from:%d/%m/%Y}.",
            )
            return redirect(detail_url(product_id, "mandate"))
    extra: dict[str, Any] = {
        "mode": "publish",
        "step": "publish",
        "step_number": 4,
        "done_steps": [key for key, _ in STEPS[:3]],
        "form": form,
        "changes": what_changes(mandate, previous, context["currency"]),
        "reason_required": mandate.version > 1,
    }
    context.update(extra)
    return render(request, TEMPLATE, context, status=422 if form.errors else 200)
