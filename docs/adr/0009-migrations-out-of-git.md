# 0009: Migrations fora do git

Status: aceito (26/11/2026)

## Contexto
O combinado do time é que arquivo de migration nunca sobe para o repositório. O texto herdado do boilerplate dizia o contrário: migrations versionadas, `makemigrations --check` no pre-push e no CI. Os agentes de IA seguiam esse texto e geravam migration.

## Decisão
- Da pasta `migrations/` só o `__init__.py` vai para o git. O `.gitignore` ignora o resto.
- Agente de IA nunca roda `makemigrations` nem `migrate`. Mudança de tabela = só o `models.py`; quem gera e aplica a migration é o humano, na máquina dele.
- O bloqueio é automático em três pontos: hook `pre-commit`, `scripts/check.py` (pre-push) e CI. Os três recusam arquivo de migration.
- Os testes montam as tabelas direto dos models (`--no-migrations` do pytest-django).
- As proteções de banco (função `maud_forbid_mutation()` e triggers de ledger) saem da migration: o `post_migrate` as aplica a cada `migrate`. Ledger se marca com `@append_only` no model.

## Consequências
- Ninguém sobe migration por engano, nem com `git add .`.
- O schema não sai só do repositório: cada ambiente tem as migrations de quem o aplicou.
- Mudança de dado em tabela (antes `RunPython`) vira script revisado e rodado pelo humano.
- Substitui o trecho do ADR 0005 que punha migrations entre as verificações do pre-push e as partes sensíveis.
- Descartado: manter migrations versionadas (contraria o combinado do time).
