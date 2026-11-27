"""Fachada pública do módulo branding: a ÚNICA coisa que outros módulos podem importar daqui.

Funções aqui recebem e devolvem tipos simples ou dataclasses (nunca models do ORM).
Mudar uma assinatura deste arquivo é mudança de contrato entre frentes: combine antes.
"""

from maud.modules.branding.features.get_branding.handler import BrandingView
from maud.modules.branding.features.get_branding.handler import execute as _get_branding


def current_branding() -> BrandingView:
    """Identidade da gestora para a casca das telas (nome, cor, logotipo). Nunca falha:
    sem cadastro, devolve a identidade padrão."""
    return _get_branding()


__all__ = ["BrandingView", "current_branding"]
