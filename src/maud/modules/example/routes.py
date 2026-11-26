"""Ponto de entrada HTTP do módulo example (usado só por config/api.py).

Importar o endpoint de uma slice registra a rota dela no router do módulo.
Slice nova com rota HTTP = uma linha de import aqui.
"""

from maud.modules.example.features.create_item import endpoint as _create_item  # noqa: F401
from maud.modules.example.features.list_items import endpoint as _list_items  # noqa: F401
from maud.modules.example.router import router

__all__ = ["router"]
