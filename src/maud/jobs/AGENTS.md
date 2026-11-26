# jobs: Worker

Entrypoint do processo Worker (`manage.py worker`). Só decide **o que roda quando** (`schedule.py`); o código de cada job mora no módulo dono e é exposto pelo `jobs.py` dele.

## Regras
- Uma instância só (advisory lock); não adicionar paralelismo sem ADR.
- Job é idempotente e abre a própria transação; pode rodar de novo sem duplicar efeito.
- Exceção num job é logada e não derruba os outros.
- Cadeia com dependências (ex.: importar → calcular → publicar) é um job orquestrador no módulo dono, não lógica aqui.
