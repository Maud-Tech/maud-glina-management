---
name: new-migration
description: Criar ou alterar tabelas com segurança (migrations Django). Use ao mudar qualquer models.py, especialmente ledgers, saldos e tabelas financeiras.
---

# Nova migração

## Regras
- Gere com `uv run python manage.py makemigrations <app>` e **revise o arquivo gerado**. Migrations são versionadas (nunca no .gitignore).
- **Nunca edite migration já aplicada** em qualquer ambiente compartilhado: crie outra.
- Valores financeiros: `DecimalField(max_digits=28, decimal_places=8)` para shares; `max_digits=20, decimal_places=2` para dinheiro em USD/BRL. Nunca `FloatField`.
- Constraints no banco, não só no Python: `CheckConstraint` (quantidade > 0, moeda válida), `UniqueConstraint` (idempotência, versão por data-base).
- FKs entre módulos só no sentido da dependência (módulo de cima aponta para o de baixo).

## Ledger (tabela de lançamentos)
1. Modele só INSERT: sem campos que "mudam de status". Estado = novo lançamento.
2. Na migration, depois do `CreateModel`:
   ```python
   from maud.shared.db import append_only

   dependencies = [..., ("shared", "0002_forbid_mutation_function")]
   operations = [migrations.CreateModel(...), append_only("<app>_<model>")]
   ```
3. Teste que UPDATE/DELETE falham (modelo: `src/maud/shared/tests/test_db.py`).

## Dados existentes
Mudança de dado em tabela financeira: migration reversível (`RunPython` com `reverse_code`) ou script auditado revisado por humano. Nunca `UPDATE` solto.

## Conferir
`uv run python manage.py makemigrations --check --dry-run` não pode acusar mudanças pendentes; `uv run pytest` verde.
