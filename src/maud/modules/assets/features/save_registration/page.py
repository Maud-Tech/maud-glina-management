"""Formulário separado da listagem; salvar e cancelar voltam ao próprio cadastro."""

import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from maud.modules.assets.features.save_registration.handler import (
    SaveRegistrationCommand,
    execute,
)
from maud.modules.assets.registrations import REGISTRY, registration_forms
from maud.shared.errors import DomainError


@login_required
@require_http_methods(["GET", "POST"])
def registration_edit(request: HttpRequest, resource: str, pk: str | None = None) -> HttpResponse:
    if resource not in REGISTRY:
        raise Http404
    spec = REGISTRY[resource]
    try:
        instance = get_object_or_404(spec.model, pk=pk) if pk is not None else None
    except (ValidationError, ValueError) as error:
        raise Http404 from error
    label = spec.model._meta.model_name
    can_edit = request.user.has_perm("assets." + ("change_" if instance else "add_") + label)
    if not can_edit and (
        instance is None
        or request.method == "POST"
        or not request.user.has_perm("assets.view_" + label)
    ):
        raise PermissionDenied
    variant = (
        request.POST.get("variant", "")
        if request.method == "POST"
        else request.GET.get("variant", "")
    )
    bundle = registration_forms(
        resource,
        data=request.POST if request.method == "POST" else None,
        instance=instance,
        variant=variant,
        identifier_rights={
            action: request.user.has_perm("assets." + action + "_assetidentifier")
            and (can_edit or action == "view")
            for action in ("view", "add", "change", "delete")
        },
    )
    list_url = reverse("assets_" + resource + "_list")
    key = request.POST.get("request_key", "") if request.method == "POST" else str(uuid.uuid4())
    if request.method == "POST":
        if (
            resource == "assets"
            and any(name.startswith("identifiers-") for name in request.POST)
            and not any(bundle.identifier_rights.values())
        ):
            raise PermissionDenied
        try:
            execute(
                SaveRegistrationCommand(
                    bundle=bundle,
                    key=key,
                    user_id=str(request.user.pk),
                    payload={
                        name: request.POST.getlist(name)
                        for name in request.POST
                        if name not in {"csrfmiddlewaretoken", "request_key"}
                    },
                )
            )
        except ValidationError:
            pass
        except IntegrityError:
            bundle.main.add_error(
                None, "Já existe um registro com esses dados. Confira os campos únicos."
            )
        except DomainError as error:
            bundle.main.add_error(None, error.message)
        else:
            messages.success(request, "Cadastro salvo.")
            return redirect(list_url)
    if not can_edit:
        for form in (bundle.main, bundle.detail):
            if form:
                for form_field in form.fields.values():
                    form_field.disabled = True
        if bundle.identifiers is not None:
            for item in bundle.identifiers.forms:
                for form_field in item.fields.values():
                    form_field.disabled = True
    related_links = []
    if instance is not None:
        for key_name, related in REGISTRY.items():
            if (
                key_name != "identifiers"
                and related.parent_field
                and related.model._meta.get_field(related.parent_field).related_model == spec.model
            ) and request.user.has_perm("assets.view_" + related.model._meta.model_name):
                related_links.append(
                    {
                        "title": related.title,
                        "url": reverse("assets_" + key_name + "_list")
                        + "?parent="
                        + str(instance.pk),
                    }
                )
    selected = bundle.main.fields[spec.variant_field].initial if spec.variant_field else ""
    return render(
        request,
        "modules/assets/features/save_registration/page.html",
        {
            "title": spec.title,
            "bundle": bundle,
            "list_url": list_url,
            "request_key": key,
            "editing": instance is not None,
            "can_edit": can_edit,
            "variant": selected,
            "variant_choices": spec.model._meta.get_field(spec.variant_field).choices
            if spec.variant_field
            else (),
            "related_links": related_links,
            "summary": str(instance) if instance else "Novo cadastro",
            "current_menu": "assets_" + resource + "_list",
        },
        status=422
        if (
            bundle.main.errors
            or (bundle.detail is not None and bundle.detail.errors)
            or (
                bundle.identifiers is not None
                and (bundle.identifiers.errors or bundle.identifiers.non_form_errors())
            )
        )
        else 200,
    )
