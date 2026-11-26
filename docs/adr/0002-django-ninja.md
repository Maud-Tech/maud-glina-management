# 0002: Django 5 + Django Ninja

Status: aceito (23/11/2026)

## Contexto
O time domina Django. Precisamos de API tipada com contrato publicável para parceiros, transações explícitas e locks de linha.

## Decisão
Django 5 (ORM, migrations, admin) + Django Ninja (rotas tipadas com Pydantic, OpenAPI automático). Postgres 16. Testes com pytest-django em Postgres real (nunca SQLite).

## Consequências
- Admin dá telas de consulta de graça. Escrita pelo admin deve chamar o handler da slice, não salvar model direto.
- OpenAPI gerado vira artefato do contrato (`docs/contracts/openapi.json`).
- Alternativa descartada: FastAPI + SQLAlchemy (perde admin e familiaridade).
