"""Tela de Personalização (ADR 0010): só para quem tem `branding.change_branding`.

A tela não grava nada sozinha: monta o comando e chama o handler da slice.
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from maud.modules.branding.features.get_branding.handler import execute as get_branding
from maud.modules.branding.features.update_branding.handler import (
    ImageRejectedError,
    UpdateBrandingCommand,
    execute,
)
from maud.shared.errors import DomainError

TEMPLATE = "modules/branding/features/update_branding/page.html"
SWATCHES = ["#22BEC6", "#3B82F6", "#10B981", "#8B5CF6", "#F97316", "#E11D48"]
FIELD_BY_CODE = {
    "brand_name_too_long": "name",
    "brand_color_invalid": "brand_color",
    "brand_color_unreadable": "brand_color",
}


class BrandingForm(forms.Form):
    name = forms.CharField(max_length=200, required=False)
    brand_color = forms.CharField(max_length=20, required=False)
    logo = forms.FileField(required=False)
    favicon = forms.FileField(required=False)
    remove_logo = forms.BooleanField(required=False)
    remove_favicon = forms.BooleanField(required=False)


@login_required
@permission_required("branding.change_branding", raise_exception=True)
def branding_settings(request: HttpRequest) -> HttpResponse:
    current = get_branding()
    if request.method == "POST":
        form = BrandingForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            try:
                execute(
                    UpdateBrandingCommand(
                        name=data["name"],
                        brand_color=data["brand_color"],
                        logo=data["logo"],
                        favicon=data["favicon"],
                        remove_logo=data["remove_logo"],
                        remove_favicon=data["remove_favicon"],
                    )
                )
            except ImageRejectedError as error:
                form.add_error(error.field, error.message)
            except DomainError as error:
                form.add_error(FIELD_BY_CODE.get(error.code), error.message)
            else:
                messages.success(request, "Personalização salva.")
                return redirect("branding_settings")
    else:
        form = BrandingForm(initial={"name": current.name, "brand_color": current.brand_color})

    chosen_color = str(form["brand_color"].value() or current.brand_color).upper()
    return render(
        request,
        TEMPLATE,
        {"form": form, "current": current, "swatches": SWATCHES, "chosen_color": chosen_color},
        status=422 if form.errors else 200,
    )
