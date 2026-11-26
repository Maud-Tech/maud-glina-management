"""Ponto de entrada HTTP do módulo assets; vazio até a primeira slice com endpoint."""

from maud.modules.assets.router import router

__all__ = ["router"]
