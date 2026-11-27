"""Listagem própria por cadastro, com busca, filtros e paginação no servidor."""

from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET

from maud.modules.entities.features.list_registrations.handler import (
    ListRegistrationsQuery,
    execute,
)
from maud.modules.entities.registrations import LABELS, REGISTRY


@login_required
@require_GET
def registration_list(request: HttpRequest, resource: str) -> HttpResponse:
    if resource not in REGISTRY:
        raise Http404
    spec = REGISTRY[resource]
    if not request.user.has_perm("entities.view_" + spec.model._meta.model_name):
        raise PermissionDenied
    query = ListRegistrationsQuery(
        resource=resource,
        search=request.GET.get("q", "").strip(),
        page=request.GET.get("page", "1"),
        variant=request.GET.get("variant", ""),
        parent=request.GET.get("parent", ""),
    )
    page = execute(query)
    rows = []
    for record in page:
        cells = []
        for name in spec.columns:
            display = getattr(record, "get_" + name + "_display", None)
            value = display() if display else getattr(record, name)
            if isinstance(value, bool):
                value = "Sim" if value else "Não"
            cells.append(value if value is not None and value != "" else "—")
        rows.append(
            {
                "cells": cells,
                "url": reverse("entities_" + resource + "_edit", args=[str(record.pk)]),
            }
        )
    parameters = request.GET.copy()
    parameters.pop("page", None)
    return render(
        request,
        "modules/entities/features/list_registrations/page.html",
        {
            "title": spec.title,
            "headers": [LABELS.get(name, name) for name in spec.columns],
            "rows": rows,
            "page": page,
            "search": query.search,
            "parent": query.parent,
            "variant": query.variant,
            "variant_choices": spec.model._meta.get_field(spec.variant_field).choices
            if spec.variant_field
            else (),
            "create_url": reverse("entities_" + resource + "_new"),
            "can_add": request.user.has_perm("entities.add_" + spec.model._meta.model_name),
            "page_query": urlencode(parameters),
            "current_menu": "entities_" + resource + "_list",
        },
    )
