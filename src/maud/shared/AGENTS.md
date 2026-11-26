# shared: kernel compartilhado

Base de todos os módulos. **Não importa nenhum módulo de negócio.** Mudança aqui afeta todo mundo: avise o time e peça revisão.

## Conteúdo
- `shares.py`: `Shares` (Decimal, ≤ 8 casas, rejeita excesso em vez de arredondar; `truncate` arredonda para baixo; `ratio_to` deriva %)
- `money.py`: `Money` + `Currency` (precisão da moeda; moedas diferentes não operam; `rounded` explícito)
- `clock.py`: `get_clock()`, `use_clock(FixedClock(...))` em teste
- `errors.py`: `DomainError` (422), `NotFoundError` (404), `ConflictError` (409); `code` estável
- `idempotency.py`: `run_idempotent(...)` para comandos com Idempotency-Key
- `outbox.py`: `publish(...)` (dentro de transação), `claim_batch`/`mark_sent`/`mark_failed`
- `db.py`: `append_only(table)` para migrations de ledger
- `http.py`: autenticação por X-Api-Key (provisória)
- `testing.py`: `ApiClient` para testes (fixture `api` no `conftest.py` da raiz)

## Invariantes
- Nenhum float. Nenhum arredondamento implícito.
- `publish` fora de `transaction.atomic` levanta erro de propósito.
- Recusa de negócio que precisa ser repetível (ex.: reserva recusada) é **retornada** dentro do `run_idempotent`, não levantada.
