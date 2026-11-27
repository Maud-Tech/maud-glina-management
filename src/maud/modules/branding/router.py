"""Router HTTP do módulo branding. Sem rotas de API: a identidade é editada pela tela."""

from ninja import Router

router = Router(tags=["branding"])
