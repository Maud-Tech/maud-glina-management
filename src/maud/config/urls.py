from django.contrib import admin
from django.db import connection
from django.http import HttpRequest, JsonResponse
from django.urls import include, path

from maud.config.api import api


def health(request: HttpRequest) -> JsonResponse:
    """Sem autenticação: usado por compose/Azure para saber se o serviço e o banco respondem."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health", health),
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
    # Telas (ADR 0010): a casca e, por módulo, o pages.py com as telas das slices.
    path("", include("maud.web.urls")),
    path("", include("maud.modules.branding.pages")),
    path("", include("maud.modules.entities.pages")),
    path("", include("maud.modules.assets.pages")),
]
