"""Tela do produto, com 5 abas: visão geral, regulamento, apólice, documentos e histórico.

Exige `products.view_product`. Os botões só aparecem para quem pode gravar, e só os que a regra
de status permite; quem grava é a slice de cada ação (a tela só mostra e confirma).
"""

from typing import Any
from uuid import UUID

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from maud.modules.products.display import (
    ACTIONS,
    DOCUMENT_TYPES,
    EMPTY,
    FIELD_LABELS,
    FLOW_TERMS,
    MANDATE_STATE,
    OBJECT_TYPES,
    POLICY_STATUS,
    PRODUCT_STATUS,
    PROFILE_TERMS,
    day,
    entity_names,
    history_value,
    limit_rows,
    limit_target_options,
    moment,
    size,
    term_rows,
)
from maud.modules.products.domain.mandate import MandateState
from maud.modules.products.domain.policy import PolicyStatus
from maud.modules.products.domain.product import ALLOWED_STATUS_CHANGES, ProductStatus
from maud.modules.products.features.get_product.handler import ProductDetail
from maud.modules.products.features.list_product_history.handler import (
    EXPOSURE_LIMIT_OBJECT,
    MANDATE_OBJECT,
    HistoryEntry,
    ListProductHistoryQuery,
)
from maud.modules.products.features.list_product_history.handler import (
    execute as list_history,
)
from maud.modules.products.models import ProductDocument
from maud.modules.products.queries import activation_readiness
from maud.modules.products.screens import product_detail_or_404
from maud.shared.clock import get_clock

TEMPLATE = "modules/products/features/get_product/page.html"
TABS = (
    ("overview", "Visão geral"),
    ("mandate", "Regulamento"),
    ("policy", "Apólice"),
    ("documents", "Documentos"),
    ("history", "Histórico"),
)
HISTORY_FILTERS = (
    ("", "Tudo"),
    ("PRODUCT", "Produto"),
    ("POLICY", "Apólice"),
    ("MANDATE", "Regulamento e limites"),
    ("DOCUMENT", "Documentos"),
)
STATUS_ACTIONS: dict[ProductStatus, dict[str, Any]] = {
    ProductStatus.ACTIVE: {
        "label": "Ativar",
        "title": "Ativar o produto?",
        "text": "O produto passa a aceitar aplicações, com o regulamento em vigor.",
        "confirm": "Ativar",
        "primary": True,
    },
    ProductStatus.INACTIVE: {
        "label": "Inativar",
        "title": "Inativar o produto?",
        "text": "O produto para de aceitar novas aplicações até ser ativado de novo.",
        "confirm": "Inativar",
    },
    ProductStatus.CLOSED: {
        "label": "Encerrar",
        "title": "Encerrar o produto?",
        "text": "Encerrado é definitivo: o produto não volta a nenhum outro status e nada "
        "dele muda depois. O histórico continua disponível.",
        "confirm": "Encerrar produto",
        "danger": True,
    },
}


def status_actions(detail: ProductDetail, user: Any) -> list[dict[str, Any]]:
    """Botões de status que a regra permite a partir do status atual."""
    if not user.has_perm("products.change_product"):
        return []
    status = ProductStatus(detail.product.status)
    readiness = activation_readiness(detail.product.id, get_clock().now().date())
    actions = []
    for target in (ProductStatus.ACTIVE, ProductStatus.INACTIVE, ProductStatus.CLOSED):
        if target not in ALLOWED_STATUS_CHANGES[status]:
            continue
        action = {"status": target.value, **STATUS_ACTIONS[target], "missing": []}
        if target is ProductStatus.ACTIVE:
            if not readiness.has_effective_policy:
                action["missing"].append("uma apólice ativa e vigente hoje")
            if not readiness.has_published_mandate:
                action["missing"].append("o regulamento publicado")
        actions.append(action)
    return actions


def policy_note(detail: ProductDetail) -> str:
    policy = detail.policy
    if policy is None:
        return "não cadastrada"
    if policy.status == PolicyStatus.EXPIRED:
        return "expirada"
    if policy.effective_until is None:
        return f"vigente desde {day(policy.effective_from)}, sem data final"
    return f"vigente até {day(policy.effective_until)}"


def versions_view(detail: ProductDetail) -> list[dict[str, Any]]:
    current = detail.current_mandate.version if detail.current_mandate else None
    today = get_clock().now().date()
    rows = []
    for version in detail.versions:
        if version.state == MandateState.DRAFT:
            note = "Rascunho, ainda não vale para ninguém"
        elif version.version == current:
            note = f"Em vigor desde {day(version.effective_from)}"
        elif version.effective_from and version.effective_from > today:
            note = f"Publicada, vale para todos a partir de {day(version.effective_from)}"
        else:
            note = f"Substituída. Valeu a partir de {day(version.effective_from)}"
        author = ""
        if version.published_at:
            author = f"{version.published_by or ''}, {day(version.published_at)}"
        rows.append(
            {
                "id": version.id,
                "version": version.version,
                "draft": version.state == MandateState.DRAFT,
                "note": note,
                "reason": version.reason,
                "author": author,
            }
        )
    return rows


def history_view(
    entries: list[HistoryEntry], what: str, detail: ProductDetail
) -> list[dict[str, Any]]:
    if what == "MANDATE":
        entries = [e for e in entries if e.object_type in {MANDATE_OBJECT, EXPOSURE_LIMIT_OBJECT}]
    elif what:
        entries = [e for e in entries if e.object_type == what]
    ids = {
        str(value)
        for entry in entries
        for field, pair in entry.changes.items()
        if field in {"insurer_entity", "target"}
        for value in pair
        if value
    }
    names = entity_names(ids)
    if detail.policy is not None:
        names[str(detail.policy.id)] = detail.policy.policy_number
    rows = []
    for entry in entries:
        subject = OBJECT_TYPES.get(entry.object_type, entry.object_type)
        if entry.mandate_version is not None:
            subject = f"Regulamento v{entry.mandate_version}" + (
                " · limite" if entry.object_type == EXPOSURE_LIMIT_OBJECT else ""
            )
        date_text, time_text = moment(entry.changed_at)
        rows.append(
            {
                "date": date_text,
                "time": time_text,
                "who": entry.changed_by,
                "subject": subject,
                "action": ACTIONS.get(entry.action, entry.action),
                "reason": entry.reason,
                "changes": [
                    {
                        "field": FIELD_LABELS.get(field, field),
                        "before": history_value(field, pair[0], names),
                        "after": history_value(field, pair[1], names),
                    }
                    for field, pair in entry.changes.items()
                ],
            }
        )
    return rows


def documents_view(detail: ProductDetail) -> list[dict[str, Any]]:
    return [
        {
            "id": document.id,
            "title": document.title,
            "archived": document.archived_at is not None,
            "meta": " · ".join(
                part
                for part in (
                    DOCUMENT_TYPES.get(document.document_type, document.document_type),
                    "ligado à apólice" if document.policy_id else "",
                    size(document.size_bytes),
                    f"arquivado em {day(document.archived_at)}"
                    if document.archived_at
                    else f"enviado em {day(document.uploaded_at)}",
                )
                if part
            ),
        }
        for document in detail.documents
    ]


@login_required
@permission_required("products.view_product", raise_exception=True)
@require_GET
def product_detail(request: HttpRequest, product_id: UUID) -> HttpResponse:
    detail = product_detail_or_404(product_id)
    product = detail.product
    tab = request.GET.get("tab", "overview")
    tab = tab if tab in dict(TABS) else "overview"
    user = request.user
    closed = product.status == ProductStatus.CLOSED
    insurer = (
        entity_names([str(detail.policy.insurer_entity_id)]).get(
            str(detail.policy.insurer_entity_id), EMPTY
        )
        if detail.policy
        else EMPTY
    )
    title_start, _, title_last = product.name.rpartition(" ")
    context: dict[str, Any] = {
        "detail": detail,
        "product": product,
        "title_start": title_start,
        "title_last": title_last,
        "status_label": PRODUCT_STATUS[product.status],
        "tabs": TABS,
        "tab": tab,
        "closed": closed,
        "actions": status_actions(detail, user),
        "can_edit": user.has_perm("products.change_product") and not closed,
        "insurer": insurer,
        "policy_note": policy_note(detail),
        "policy_status_label": POLICY_STATUS.get(detail.policy.status, "") if detail.policy else "",
        "documents_count": sum(1 for d in detail.documents if d.archived_at is None),
    }
    options = limit_target_options()
    current, upcoming = detail.current_mandate, detail.upcoming_mandate
    if tab == "overview" and current is not None:
        currency = product.base_currency
        context.update(
            profile=term_rows(current, currency, PROFILE_TERMS, upcoming),
            flows=term_rows(current, currency, FLOW_TERMS, upcoming),
            limits=limit_rows(
                current.exposure_limits, options, upcoming.exposure_limits if upcoming else ()
            ),
            upcoming_version=upcoming.version if upcoming else None,
        )
    if tab == "mandate":
        can_mandate = user.has_perm("products.change_mandate") and not closed
        context.update(
            versions=versions_view(detail),
            can_start_draft=can_mandate and detail.draft_mandate is None,
            can_mandate=can_mandate,
            last_version=detail.versions[0].version if detail.versions else None,
        )
    if tab == "policy":
        policy = detail.policy
        active = policy is not None and policy.status == PolicyStatus.ACTIVE
        context.update(
            can_add_policy=policy is None and user.has_perm("products.add_policy") and not closed,
            can_change_policy=active and user.has_perm("products.change_policy") and not closed,
        )
    if tab == "documents":
        context.update(
            documents=documents_view(detail),
            document_types=list(ProductDocument.Type.choices),
            can_attach=user.has_perm("products.change_product") and not closed,
        )
    if tab == "history":
        what = request.GET.get("what", "")
        what = what if what in dict(HISTORY_FILTERS) else ""
        entries = list_history(ListProductHistoryQuery(product_id=product.id))
        context.update(
            history=history_view(entries, what, detail), history_filters=HISTORY_FILTERS, what=what
        )
    context["mandate_state_labels"] = MANDATE_STATE
    return render(request, TEMPLATE, context)
