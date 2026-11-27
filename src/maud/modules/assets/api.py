"""Fachada pública do módulo assets.

Funções aqui recebem e devolvem tipos simples (nunca models do ORM).
Mudar uma assinatura deste arquivo é mudança de contrato entre frentes: combine antes.
"""

from maud.modules.assets.models import AssetClassification


def asset_class_codes() -> frozenset[str]:
    """Códigos das classes de ativo (ex.: EQUITY, FIXED_INCOME), para regras de outros módulos."""
    return frozenset(AssetClassification.AssetClass.values)
