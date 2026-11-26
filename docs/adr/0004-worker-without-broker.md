# 0004: Worker sem broker

Status: aceito (23/11/2026)

## Contexto
Infra com orçamento sensível, escala esperada baixa, jobs poucos e periódicos (despachar outbox, rotinas diárias, conciliações).

## Decisão
Um processo `manage.py worker` com agendador simples (`maud/jobs/scheduler.py`). `pg_try_advisory_lock` garante uma instância. Sem Redis/Celery. Entregas para fora via transactional outbox no Postgres.

## Consequências
- Um serviço a menos para pagar e operar.
- Paralelismo limitado. Se precisar, migrar para fila apoiada no Postgres (ex.: procrastinate) sem mudar módulos: os jobs já são funções dos módulos.
