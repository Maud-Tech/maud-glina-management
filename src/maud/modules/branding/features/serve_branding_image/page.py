"""Entrega o logotipo e o ícone da aba da gestora. Público (ADR 0010): aparecem até na tela
de login. Lê pelo storage padrão, então funciona igual com a pasta media/ e com o S3."""

import mimetypes

from django.http import FileResponse, Http404, HttpRequest
from django.views.decorators.http import require_GET

from maud.modules.branding.models import Branding

KINDS = ("logo", "favicon")


@require_GET
def branding_image(request: HttpRequest, kind: str) -> FileResponse:
    if kind not in KINDS:
        raise Http404
    branding = Branding.objects.filter(id=Branding.SINGLETON_ID).first()
    image = getattr(branding, kind) if branding is not None else None
    if not image:
        raise Http404
    try:
        handle = image.open("rb")
    except FileNotFoundError as error:
        raise Http404 from error
    content_type = mimetypes.guess_type(image.name)[0] or "application/octet-stream"
    response = FileResponse(handle, content_type=content_type)
    response["Cache-Control"] = "public, max-age=300"
    response["X-Content-Type-Options"] = "nosniff"
    return response
