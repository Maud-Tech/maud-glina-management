"""Router HTTP do módulo example. Cada slice pendura a própria rota nele com @router."""

from ninja import Router

router = Router(tags=["example"])
