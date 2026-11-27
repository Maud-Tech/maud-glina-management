import io
from pathlib import Path
from typing import Any

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from PIL import Image

from maud.modules.branding.features.update_branding.handler import UpdateBrandingCommand, execute

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_in_tmp(settings: Any, tmp_path: Path) -> None:
    settings.MEDIA_ROOT = tmp_path


def png() -> SimpleUploadedFile:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "#22BEC6").save(buffer, "PNG")
    return SimpleUploadedFile("logo.png", buffer.getvalue())


def test_logo_is_public_and_served_from_storage(client: Client) -> None:
    execute(UpdateBrandingCommand(name="Gestora Exemplo", brand_color="#22BEC6", logo=png()))

    response = client.get("/branding/logo")

    assert response.status_code == 200
    assert response["Content-Type"] == "image/png"
    assert b"".join(response.streaming_content).startswith(b"\x89PNG")  # type: ignore[attr-defined]


def test_missing_logo_returns_404(client: Client) -> None:
    assert client.get("/branding/logo").status_code == 404


def test_unknown_kind_returns_404(client: Client) -> None:
    assert client.get("/branding/settings").status_code == 404
