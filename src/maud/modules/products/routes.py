"""Ponto de entrada HTTP do módulo products (usado só por config/api.py).

Ainda sem rotas: a escrita é pela tela (ADR 0010) e a API de leitura é uma task separada.
"""

from maud.modules.products.router import router

__all__ = ["router"]
