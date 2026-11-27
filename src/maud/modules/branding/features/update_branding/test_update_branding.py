import io
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from maud.modules.branding.features.get_branding.handler import execute as get_branding
from maud.modules.branding.features.update_branding.handler import (
    MAX_IMAGE_BYTES,
    UpdateBrandingCommand,
    execute,
)
from maud.modules.branding.models import Branding
from maud.shared.errors import DomainError

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_in_tmp(settings: Any, tmp_path: Path) -> None:
    settings.MEDIA_ROOT = tmp_path


def image(fmt: str = "PNG", name: str = "logo.png") -> SimpleUploadedFile:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "#22BEC6").save(buffer, fmt)
    return SimpleUploadedFile(name, buffer.getvalue())


def command(**changes: Any) -> UpdateBrandingCommand:
    fields: dict[str, Any] = {"name": "Gestora Exemplo", "brand_color": "#22BEC6"}
    fields.update(changes)
    return UpdateBrandingCommand(**fields)


def test_without_saved_branding_the_default_identity_is_used() -> None:
    view = get_branding()

    assert view.name == "Gestão de apólices"
    assert view.brand_color == "#22BEC6"
    assert not view.has_logo


def test_saves_trimmed_name_and_normalized_color() -> None:
    view = execute(command(name="  Gestora   Exemplo ", brand_color="8b5cf6"))

    assert view.name == "Gestora Exemplo"
    assert view.initials == "GE"
    assert view.brand_color == "#8B5CF6"
    assert view.text_on_brand == "#FFFFFF"


def test_blank_name_with_logo_shows_only_the_logo() -> None:
    view = execute(command(name="  ", logo=image()))

    assert view.name == ""
    assert view.wordmark_name == ""
    assert Branding.objects.get().name == ""


def test_blank_name_without_logo_falls_back_to_default_wordmark() -> None:
    view = execute(command(name=""))

    assert view.name == ""
    assert view.wordmark_name == "Gestão de apólices"
    assert view.initials == "GA"


def test_saving_twice_keeps_a_single_row() -> None:
    execute(command(name="Primeira"))
    execute(command(name="Segunda"))

    assert Branding.objects.count() == 1
    assert Branding.objects.get().name == "Segunda"


def test_unreadable_color_is_rejected_and_nothing_is_saved() -> None:
    with pytest.raises(DomainError) as error:
        execute(command(brand_color="#787878"))

    assert error.value.code == "brand_color_unreadable"
    assert not Branding.objects.exists()


def test_logo_is_stored_with_extension_of_its_real_format() -> None:
    execute(command(logo=image(fmt="JPEG", name="logo.png")))

    logo = Branding.objects.get().logo
    assert str(logo.name).endswith(".jpg")
    assert default_storage.exists(str(logo.name))


def test_file_that_is_not_an_image_is_rejected() -> None:
    with pytest.raises(DomainError) as error:
        execute(command(logo=SimpleUploadedFile("logo.png", b"not an image")))

    assert error.value.code == "image_unreadable"
    assert not Branding.objects.exists()


def test_image_in_format_not_allowed_is_rejected() -> None:
    with pytest.raises(DomainError) as error:
        execute(command(logo=image(fmt="GIF", name="logo.gif")))

    assert error.value.code == "image_format_not_allowed"


def test_image_over_size_limit_is_rejected() -> None:
    too_big = SimpleUploadedFile("logo.png", b"x" * (MAX_IMAGE_BYTES + 1))

    with pytest.raises(DomainError) as error:
        execute(command(logo=too_big))

    assert error.value.code == "image_too_large"


def test_replacing_logo_deletes_old_file_after_commit(
    django_capture_on_commit_callbacks: Callable[..., Any],
) -> None:
    with django_capture_on_commit_callbacks(execute=True):
        execute(command(logo=image()))
    old_name = str(Branding.objects.get().logo.name)

    with django_capture_on_commit_callbacks(execute=True):
        execute(command(logo=image()))

    new_name = str(Branding.objects.get().logo.name)
    assert new_name != old_name
    assert default_storage.exists(new_name)
    assert not default_storage.exists(old_name)


def test_removing_logo_clears_field_and_deletes_file(
    django_capture_on_commit_callbacks: Callable[..., Any],
) -> None:
    with django_capture_on_commit_callbacks(execute=True):
        execute(command(logo=image()))
    old_name = str(Branding.objects.get().logo.name)

    with django_capture_on_commit_callbacks(execute=True):
        view = execute(command(remove_logo=True))

    assert not view.has_logo
    assert not default_storage.exists(old_name)
