# Contratos

Como este serviço conversa com quem está de fora. **A forma exata dos payloads é o OpenAPI gerado** (`openapi.json`, nunca editado à mão); aqui fica a semântica.

Gerar o OpenAPI:
```
uv run python manage.py export_openapi_schema --api maud.config.api.api --indent 2 --output docs/contracts/openapi.json
```

## Regras de toda chamada (padrão do boilerplate)

| Item | Regra |
|---|---|
| Base | `/api/v1/` (versão no caminho; mudança incompatível = `/v2/`) |
| Autenticação | Header `X-Api-Key` (`shared/http.py`). Esquema definitivo (HMAC, mTLS, OAuth) combinado com cada parceiro |
| Idempotência | Todo POST de comando exige `Idempotency-Key` (≤ 200 chars). Repetir com o mesmo corpo devolve a mesma resposta. Mesma chave com corpo diferente → 409 `idempotency_key_reused` |
| Erros | JSON `{"code": "...", "message": "..."}`. `code` é estável (inglês), `message` é para humanos |
| HTTP | 401 sem chave · 404 `not_found` · 409 conflito · 422 regra de negócio violada |
| Números | Decimais como string JSON (`"1234.56"`, `"10.12345678"`), nunca float |
| Datas | Instantes em ISO-8601 UTC; data-base como `YYYY-MM-DD` |
| operationId | `<módulo>_<função>` (ex.: `example_post_item`); não muda quando arquivos mudam de lugar |

## Eventos (webhook de saída)

Envelope enviado pelo Worker (`integration/adapters/webhook/`):

```json
{
  "event_id": "uuid",
  "event_type": "<módulo>.<fato_no_passado>",
  "occurred_at": "2026-01-05T12:00:00Z",
  "aggregate": {"type": "<agregado>", "id": "<id>"},
  "payload": { }
}
```

- Entrega **pelo menos uma vez**: o destino deve deduplicar por `event_id`.
- Ordem garantida só por agregado.
- Retentativa com espera crescente; depois de muitas falhas o evento fica `dead` e precisa de ação humana (`shared/outbox.py`).
- Headers: `X-Maud-Event-Id` e, com segredo configurado, `X-Maud-Signature: sha256=<HMAC-SHA256 do corpo>`.
- Configuração: `WEBHOOK_URL` e `WEBHOOK_SECRET`. Sem URL, os avisos ficam na fila e não se perdem.

| Evento | Quando |
|---|---|
| `example.item_created` | Item cadastrado (módulo de demonstração) |

## Um arquivo por parceiro

Para cada parceiro, crie `docs/contracts/<parceiro>.md` com: princípios (o que é comando, o que é evento), autenticação combinada, eventos que ele recebe ou envia, erros específicos e **itens em aberto** (marque com ⚠️).
