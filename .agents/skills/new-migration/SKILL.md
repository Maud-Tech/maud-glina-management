---
name: new-migration
description: Mudar tabela, campo ou constraint (models.py). Migration não vai para o git e o agente nunca roda makemigrations nem migrate. Use ao mudar qualquer models.py, especialmente ledgers, saldos e tabelas financeiras.
---

# Mudança de tabela

## Regras (ADR "Migrations fora do git")
- **Migration não vai para o git.** Da pasta `migrations/` só o `__init__.py` é versionado. O `.gitignore` ignora o resto, e o hook `pre-commit`, o `scripts/check.py` e o CI recusam qualquer outro arquivo.
- **O agente nunca roda `makemigrations` nem `migrate`**, nem escreve arquivo em `migrations/` à mão. Altere só o `models.py`.
- No fim, diga ao humano quais models mudaram: ele gera e aplica a migration na máquina dele.
- Valores financeiros: `DecimalField(max_digits=28, decimal_places=8)` para shares; `max_digits=20, decimal_places=2` para dinheiro em USD/BRL. Nunca `FloatField`.
- Constraints no banco, não só no Python: `CheckConstraint` (quantidade > 0, moeda válida), `UniqueConstraint` (idempotência, versão por data-base).
- FKs entre módulos só no sentido da dependência (módulo de cima aponta para o de baixo).

## Ledger (tabela de lançamentos)
1. Modele só INSERT: sem campos que "mudam de status". Estado = novo lançamento.
2. Marque o model:
   ```python
   from maud.shared.db import append_only


   @append_only
   class LedgerEntry(models.Model):
       amount = models.DecimalField(max_digits=20, decimal_places=2)
   ```
   A cada `migrate` (inclusive no banco de teste), o `post_migrate` cria os triggers que recusam UPDATE, DELETE e TRUNCATE.
3. Teste que UPDATE/DELETE falham (modelo: `src/maud/shared/tests/test_db.py`).

## Dados existentes
Mudança de dado em tabela financeira: script auditado, revisado e rodado pelo humano. Nunca `UPDATE` solto, e o agente não roda.

## Conferir
`uv run pytest` verde (as tabelas de teste saem direto dos models, `--no-migrations`). `git status` não mostra arquivo em `migrations/` além do `__init__.py`.
