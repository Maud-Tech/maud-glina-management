"""Telas do módulo branding (ADR 0010). O `config/urls.py` inclui este arquivo.

Uma linha por tela de slice. Superfície pública do módulo, como o `routes.py` da API.
"""

from django.urls import path

from maud.modules.branding.features.serve_branding_image.page import branding_image
from maud.modules.branding.features.update_branding.page import branding_settings

urlpatterns = [
    path("settings/branding/", branding_settings, name="branding_settings"),
    path("branding/<str:kind>", branding_image, name="branding_image"),
]
