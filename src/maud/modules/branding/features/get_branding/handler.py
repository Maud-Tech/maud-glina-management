"""Ler a identidade da gestora. Consulta: não muda nada.

Sem cadastro ainda, devolve a identidade padrão (nome e cor de `domain/brand.py`), para a
casca das telas sempre ter o que mostrar.
"""

from dataclasses import dataclass

from maud.modules.branding.domain.brand import (
    DEFAULT_BRAND_COLOR,
    DEFAULT_NAME,
    initials,
    parse_brand_color,
)
from maud.modules.branding.models import Branding


@dataclass(frozen=True)
class BrandingView:
    name: str  # pode ser vazio: a gestora pode ter só o logotipo
    wordmark_name: str  # o que vai ao lado da marca: o nome; sem nome e sem logotipo, o padrão
    initials: str
    brand_color: str
    text_on_brand: str
    has_logo: bool
    has_favicon: bool
    version: str  # muda a cada gravação; vai na URL das imagens para o navegador não usar a antiga


def execute() -> BrandingView:
    # 1. Carrega a linha única, se já existe
    branding = Branding.objects.filter(id=Branding.SINGLETON_ID).first()
    if branding is None:
        return _view(
            DEFAULT_NAME, DEFAULT_BRAND_COLOR, has_logo=False, has_favicon=False, version="0"
        )

    # 2. Monta a visão (a cor gravada já passou pela regra; aqui só se calcula o texto)
    return _view(
        branding.name,
        branding.brand_color,
        has_logo=bool(branding.logo),
        has_favicon=bool(branding.favicon),
        version=str(int(branding.updated_at.timestamp())),
    )


def _view(
    name: str, color: str, *, has_logo: bool, has_favicon: bool, version: str
) -> BrandingView:
    brand_color = parse_brand_color(color)
    wordmark_name = name or ("" if has_logo else DEFAULT_NAME)
    return BrandingView(
        name=name,
        wordmark_name=wordmark_name,
        initials=initials(name or DEFAULT_NAME),
        brand_color=brand_color.value,
        text_on_brand=brand_color.text_on_color,
        has_logo=has_logo,
        has_favicon=has_favicon,
        version=version,
    )
