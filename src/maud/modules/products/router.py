"""Router HTTP do módulo products. Cada slice pendura a própria rota nele com @router."""

from ninja import Router

router = Router(tags=["products"])
