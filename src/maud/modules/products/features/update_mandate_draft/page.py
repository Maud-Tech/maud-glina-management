"""Tela do regulamento: rascunho em etapas (perfil e retorno, entrada e saída, limites).

Abrir exige `products.view_product`; gravar exige `products.change_mandate`. Versão publicada
abre só para leitura. Cada etapa manda os termos inteiros e a lista inteira de limites para a
slice (o que a etapa não mostra vai como está no rascunho). A publicação é a etapa 04, na tela
de `publish_mandate`.
"""

from dataclasses import replace
from typing import Any
from uuid import UUID

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from maud.modules.assets.api import asset_class_choices
from maud.modules.products.display import (
    DIMENSIONS,
    FLOW_TERMS,
    PROFILE_TERMS,
    limit_rows,
    limit_target_options,
    missing_to_publish,
    number,
    parse_decimal,
    parse_int,
    term_rows,
    term_text,
    trimmed,
)
from maud.modules.products.domain.mandate import LimitDimension, LimitTerms, MandateState
from maud.modules.products.features.update_mandate_draft.handler import (
    UpdateMandateDraftCommand,
    execute,
)
from maud.modules.products.models import Mandate
from maud.modules.products.queries import get_mandate, latest_published_mandate
from maud.modules.products.responses import mandate_limits, mandate_terms
from maud.modules.products.screens import (
    actor_id,
    area_input,
    product_detail_or_404,
    set_choices,
)
from maud.shared.errors import DomainError, NotFoundError

TEMPLATE = "modules/products/features/update_mandate_draft/page.html"
STEPS = (
    ("profile", "Perfil e retorno"),
    ("flows", "Entrada e saída"),
    ("limits", "Limites de exposição"),
    ("publish", "Publicação"),
)
DECIMAL_FIELDS = {
    "target_return_spread_pct",
    "max_average_term_years",
    "min_initial_amount",
    "min_additional_amount",
    "min_redemption_amount",
    "min_balance_amount",
}
FIELD_BY_CODE = {
    "mandate_risk_level_invalid": "risk_level",
    "mandate_target_return_invalid": "target_return_spread_pct",
    "mandate_average_term_invalid": "max_average_term_years",
    "mandate_asset_class_unknown": "eligible_asset_classes",
}
LIMIT_CODES = {
    "exposure_limit_target_required",
    "exposure_limit_target_not_allowed",
    "exposure_limit_range_invalid",
    "exposure_limit_asset_class_not_eligible",
    "exposure_limit_duplicated",
    "exposure_limit_target_not_found",
}


def number_input(**attrs: Any) -> forms.TextInput:
    return forms.TextInput(attrs={"class": "in", "inputmode": "decimal", **attrs})


class TermsForm(forms.Form):
    """Campos de texto livre convertidos aqui; faixas e casas decimais são da slice."""

    def clean(self) -> dict[str, Any]:
        data = super().clean() or {}
        for name in self.fields:
            if name in {"risk_level", "eligible_asset_classes", "notes"} or name not in data:
                continue
            raw = data[name] or ""
            try:
                data[name] = parse_decimal(raw) if name in DECIMAL_FIELDS else parse_int(raw)
            except ValueError:
                self.add_error(name, "Use só números (ex.: 2,50).")
        return data


class ProfileForm(TermsForm):
    risk_level = forms.TypedChoiceField(
        choices=[(str(level), str(level)) for level in range(1, 6)],
        coerce=int,
        empty_value=None,
        required=False,
    )
    target_return_spread_pct = forms.CharField(required=False, widget=number_input())
    liquidity_days = forms.CharField(required=False, widget=number_input(inputmode="numeric"))
    max_average_term_years = forms.CharField(required=False, widget=number_input())
    eligible_asset_classes = forms.MultipleChoiceField(required=False)
    notes = forms.CharField(required=False, widget=area_input())

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        set_choices(self, "eligible_asset_classes", asset_class_choices())


class FlowsForm(TermsForm):
    min_initial_amount = forms.CharField(required=False, widget=number_input())
    min_additional_amount = forms.CharField(required=False, widget=number_input())
    subscription_settlement_days = forms.CharField(
        required=False, widget=number_input(inputmode="numeric")
    )
    min_redemption_amount = forms.CharField(required=False, widget=number_input())
    min_balance_amount = forms.CharField(required=False, widget=number_input())
    redemption_notice_days = forms.CharField(
        required=False, widget=number_input(inputmode="numeric")
    )
    redemption_settlement_days = forms.CharField(
        required=False, widget=number_input(inputmode="numeric")
    )
    lock_up_months = forms.CharField(required=False, widget=number_input(inputmode="numeric"))


FORMS: dict[str, type[TermsForm]] = {"profile": ProfileForm, "flows": FlowsForm}


def load_mandate(product_id: UUID, mandate_id: UUID) -> Mandate:
    try:
        mandate = get_mandate(mandate_id)
    except NotFoundError:
        raise Http404 from None
    if mandate.product_id != product_id:
        raise Http404
    return mandate


def initial_values(mandate: Mandate) -> dict[str, Any]:
    """Valores do rascunho como texto dos campos (vírgula decimal)."""
    values: dict[str, Any] = {
        "risk_level": str(mandate.risk_level) if mandate.risk_level else None,
        "eligible_asset_classes": list(mandate.eligible_asset_classes),
        "notes": mandate.notes,
    }
    for name in (
        "liquidity_days",
        "subscription_settlement_days",
        "redemption_notice_days",
        "redemption_settlement_days",
        "lock_up_months",
    ):
        value = getattr(mandate, name)
        values[name] = "" if value is None else str(value)
    values["target_return_spread_pct"] = trimmed(mandate.target_return_spread_pct)
    values["max_average_term_years"] = trimmed(mandate.max_average_term_years)
    for name in (
        "min_initial_amount",
        "min_additional_amount",
        "min_redemption_amount",
        "min_balance_amount",
    ):
        value = getattr(mandate, name)
        values[name] = "" if value is None else number(value)
    return values


def posted_limits(request: HttpRequest) -> tuple[list[dict[str, str]], tuple[LimitTerms, ...]]:
    """Linhas de limite enviadas (para mostrar de volta) e os limites para a slice."""
    rows = []
    limits = []
    for dimension, target, minimum, maximum in zip(
        request.POST.getlist("limit_dimension"),
        request.POST.getlist("limit_target"),
        request.POST.getlist("limit_min"),
        request.POST.getlist("limit_max"),
        strict=False,
    ):
        rows.append({"dimension": dimension, "target": target, "min": minimum, "max": maximum})
        if dimension not in DIMENSIONS:
            raise ValueError("Escolha a dimensão de cada limite.")
        min_pct = parse_decimal(minimum)
        max_pct = parse_decimal(maximum)
        if min_pct is None or max_pct is None:
            raise ValueError("Preencha o mínimo e o máximo de cada limite.")
        limits.append(LimitTerms(LimitDimension(dimension), target, min_pct, max_pct))
    return rows, tuple(limits)


def limit_form_rows(mandate: Mandate) -> list[dict[str, str]]:
    return [
        {
            "dimension": limit.dimension,
            "target": limit.target,
            "min": trimmed(limit.min_pct),
            "max": trimmed(limit.max_pct),
        }
        for limit in mandate.exposure_limits.order_by("dimension", "target")
    ]


def target_groups() -> list[tuple[str, str, list[tuple[str, str]]]]:
    options = limit_target_options()
    return [(value, label, options[value]) for value, label in DIMENSIONS.items()]


def previous_values(mandate: Mandate, previous: Mandate | None, currency: str) -> dict[str, str]:
    """Para cada termo que mudou em relação à versão anterior, o valor que ela tinha."""
    if previous is None:
        return {}
    was = {}
    for name, _label in PROFILE_TERMS + FLOW_TERMS:
        before = term_text(name, previous, currency)
        if before != term_text(name, mandate, currency):
            was[name] = before
    return was


def mandate_context(product_id: UUID, mandate: Mandate) -> dict[str, Any]:
    """O que o cabeçalho, as etapas e o resumo das telas do regulamento precisam."""
    detail = product_detail_or_404(product_id)
    product = detail.product
    previous = latest_published_mandate(product_id)
    if previous is not None and previous.id == mandate.id:
        previous = (
            Mandate.objects.filter(
                product_id=product_id, state=MandateState.PUBLISHED, version__lt=mandate.version
            )
            .order_by("-version")
            .first()
        )
    terms = mandate_terms(mandate)
    return {
        "product": product,
        "mandate": mandate,
        "draft": mandate.state == MandateState.DRAFT,
        "previous": previous,
        "steps": STEPS,
        "currency": product.base_currency,
        "summary": {
            "risk": term_text("risk_level", terms, product.base_currency),
            "target_return": term_text("target_return_spread_pct", terms, product.base_currency),
            "classes": len(terms.eligible_asset_classes),
            "limits": mandate.exposure_limits.count(),
        },
        "missing": missing_to_publish(terms),
    }


@login_required
@permission_required("products.view_product", raise_exception=True)
def mandate_page(request: HttpRequest, product_id: UUID, mandate_id: UUID) -> HttpResponse:
    mandate = load_mandate(product_id, mandate_id)
    context = mandate_context(product_id, mandate)
    currency = context["currency"]
    if mandate.state != MandateState.DRAFT:
        options = limit_target_options()
        context.update(
            mode="view",
            profile=term_rows(mandate, currency, PROFILE_TERMS),
            flows=term_rows(mandate, currency, FLOW_TERMS),
            limits=limit_rows(mandate.exposure_limits.order_by("dimension", "target"), options),
        )
        return render(request, TEMPLATE, context)

    step = request.GET.get("step", "profile")
    step = step if step in {"profile", "flows", "limits"} else "profile"
    can_save = request.user.has_perm("products.change_mandate")
    form = FORMS[step](initial=initial_values(mandate)) if step in FORMS else None
    rows = limit_form_rows(mandate)
    limits_error = ""
    if request.method == "POST":
        if not can_save:
            raise PermissionDenied
        terms = mandate_terms(mandate)
        limits = mandate_limits(mandate)
        valid = True
        if form is not None:
            form = FORMS[step](request.POST)
            valid = form.is_valid()
            if valid:
                changed = {name: form.cleaned_data[name] for name in form.fields}
                if "eligible_asset_classes" in changed:
                    changed["eligible_asset_classes"] = tuple(changed["eligible_asset_classes"])
                terms = replace(terms, **changed)
        else:
            try:
                rows, limits = posted_limits(request)
            except ValueError as error:
                valid = False
                limits_error = str(error)
        if valid:
            try:
                execute(
                    UpdateMandateDraftCommand(
                        actor_id=actor_id(request),
                        mandate_id=mandate.id,
                        terms=terms,
                        limits=limits,
                    )
                )
            except DomainError as error:
                if error.code in LIMIT_CODES:
                    limits_error = error.message
                elif form is not None and error.code in FIELD_BY_CODE:
                    form.add_error(FIELD_BY_CODE[error.code], error.message)
                else:
                    messages.error(request, error.message)
            else:
                position = [key for key, _ in STEPS].index(step)
                if request.POST.get("go") == "next":
                    following = STEPS[position + 1][0]
                    if following == "publish":
                        return redirect(
                            reverse("products_mandate_publish", args=[product_id, mandate.id])
                        )
                    url = reverse("products_mandate", args=[product_id, mandate.id])
                    return redirect(f"{url}?step={following}")
                messages.success(request, "Rascunho salvo.")
                url = reverse("products_mandate", args=[product_id, mandate.id])
                return redirect(f"{url}?step={step}")
    position = [key for key, _ in STEPS].index(step)
    context.update(
        mode="edit",
        step=step,
        step_number=position + 1,
        done_steps=[key for key, _ in STEPS[:position]],
        form=form,
        can_save=can_save,
        was=previous_values(mandate, context["previous"], currency),
        limit_rows=rows,
        limits_error=limits_error,
        target_groups=target_groups(),
        dimensions=DIMENSIONS.items(),
        previous_limits=limit_rows(
            context["previous"].exposure_limits.order_by("dimension", "target"),
            limit_target_options(),
        )
        if context["previous"] is not None and step == "limits"
        else [],
    )
    failed = bool(limits_error) or (form is not None and form.errors)
    return render(request, TEMPLATE, context, status=422 if failed else 200)
