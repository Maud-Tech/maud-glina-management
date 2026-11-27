"""Salvar a identidade da gestora (tela de Personalização). Slice de COMANDO.

Passo a passo:
    1. valida o nome e a cor (regra pura, em domain/)
    2. confere as imagens pelo conteúdo (formato e tamanho), não pelo nome do arquivo
    3. grava a linha única; imagem trocada ou removida é apagada do storage depois do commit

Não é idempotente por chave: vem da tela, com login, e gravar de novo dá o mesmo resultado.
O nome é opcional (vazio = só o logotipo, ou o nome padrão se também não houver logotipo).
Erros (422): brand_name_too_long, brand_color_invalid,
             brand_color_unreadable, image_too_large, image_unreadable, image_format_not_allowed
"""

from __future__ import annotations  # UploadedFile[bytes] só existe para o mypy

from dataclasses import dataclass
from functools import partial

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from PIL import Image, UnidentifiedImageError

from maud.modules.branding.domain.brand import parse_brand_color, validate_name
from maud.modules.branding.features.get_branding.handler import BrandingView
from maud.modules.branding.features.get_branding.handler import execute as get_branding
from maud.modules.branding.models import Branding
from maud.shared.errors import DomainError

MAX_IMAGE_BYTES = 2 * 1024 * 1024
EXTENSION_BY_FORMAT = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp", "ICO": ".ico"}
ALLOWED_FORMATS = {"logo": {"PNG", "JPEG", "WEBP"}, "favicon": {"PNG", "ICO"}}


class ImageRejectedError(DomainError):
    """Imagem recusada. `field` diz qual (logo ou favicon), para a tela mostrar no campo certo."""

    def __init__(self, message: str, *, code: str, field: str) -> None:
        super().__init__(message, code=code)
        self.field = field


@dataclass(frozen=True)
class UpdateBrandingCommand:
    name: str
    brand_color: str
    logo: UploadedFile[bytes] | None = None
    favicon: UploadedFile[bytes] | None = None
    remove_logo: bool = False
    remove_favicon: bool = False


def execute(command: UpdateBrandingCommand) -> BrandingView:
    # 1. Valida nome e cor
    name = validate_name(command.name)
    color = parse_brand_color(command.brand_color)

    # 2. Confere as imagens antes de gravar qualquer coisa
    uploads = {"logo": command.logo, "favicon": command.favicon}
    stored_names = {
        field: _checked_name(field, upload)
        for field, upload in uploads.items()
        if upload is not None
    }
    removals = {"logo": command.remove_logo, "favicon": command.remove_favicon}

    # 3. Grava a linha única
    with transaction.atomic():
        branding, _ = Branding.objects.select_for_update().get_or_create(
            id=Branding.SINGLETON_ID, defaults={"name": name, "brand_color": color.value}
        )
        branding.name = name
        branding.brand_color = color.value
        replaced: list[str] = []
        for field, upload in uploads.items():
            current = getattr(branding, field)
            if upload is not None:
                if current:
                    replaced.append(current.name)
                current.save(stored_names[field], upload, save=False)
            elif removals[field] and current:
                replaced.append(current.name)
                setattr(branding, field, "")
        branding.save()
        for old_name in replaced:
            transaction.on_commit(partial(default_storage.delete, old_name))

    return get_branding()


def _checked_name(field: str, upload: UploadedFile[bytes]) -> str:
    """Confere tamanho e formato pelo conteúdo. Devolve o nome com a extensão do formato real."""
    if upload.size is not None and upload.size > MAX_IMAGE_BYTES:
        raise ImageRejectedError("A imagem passa de 2 MB.", code="image_too_large", field=field)
    try:
        with Image.open(upload) as image:
            image.verify()
            image_format = image.format or ""
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError) as error:
        raise ImageRejectedError(
            "Não foi possível ler a imagem.", code="image_unreadable", field=field
        ) from error
    finally:
        upload.seek(0)
    if image_format not in ALLOWED_FORMATS[field]:
        allowed = ", ".join(sorted(ALLOWED_FORMATS[field]))
        raise ImageRejectedError(
            f"Formato não aceito. Use {allowed}.", code="image_format_not_allowed", field=field
        )
    return f"{field}{EXTENSION_BY_FORMAT[image_format]}"
