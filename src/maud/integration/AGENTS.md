# integration: tudo que fala com terceiros

Responsável por conversar com o mundo de fora: APIs de parceiros (entrada de dados), webhooks de saída (despacho do outbox) e callbacks que parceiros nos mandam.
Não faz: regra de negócio. Busca, traduz e entrega a um módulo pelo `api.py` dele.

## Direção do fluxo (por que quase não precisamos de "ports")

```
ENTRADA  terceiro ──► integration/adapters/<parceiro>  ──traduz──► <módulo>.api.<importar>(...)
SAÍDA    <módulo> ──► shared.outbox (mesma transação) ──Worker──► integration/adapters/webhook
```

- Os módulos de negócio **nunca chamam terceiros**. Para dentro, o integration chama o `api.py` deles com dados já normalizados. Para fora, eles publicam no outbox.
- Assim não há injeção de dependência nem interface por todo lado: a dependência aponta sempre de fora para dentro.
- **Exceção:** um comando que precisa de dado externo *na hora* (ex.: uma cotação dentro de um cálculo). Aí o módulo declara um `Protocol` em `<módulo>/ports.py`, o adapter fica aqui e a ligação acontece em `config/`. Use só quando não houver alternativa; registre num ADR.

## Estrutura

```
integration/
├── adapters/                    # um subpacote por parceiro
│   └── webhook/                 # ✅ existe: webhook de saída genérico
│       ├── client.py            #    HTTP: só transporte (+ assinatura HMAC)
│       ├── mapping.py           #    nosso evento → envelope do contrato
│       ├── fake.py              #    versão de teste (sem rede)
│       └── tests/               #    cliente real contra servidor HTTP local
├── features/
│   └── dispatch_outbox/         # ✅ existe: job claim_batch → adapter webhook → mark_sent/failed
└── jobs.py                      # ✅ expõe dispatch_outbox para maud/jobs/schedule.py
```

**Referência:** `adapters/webhook/` + `features/dispatch_outbox/` mostram o padrão completo. Um adapter novo (`adapters/<parceiro>/`) copia essa forma: `client.py`, `mapping.py`, `fake.py`, `tests/`.

## Regras
- **Adapter é burro:** transporte + tradução. Decisão fica no módulo dono.
- **Payload externo nunca entra cru:** valide com schema (Pydantic) no `mapping.py` antes de chamar um módulo.
- **Todo adapter tem `fake.py`.** Teste de slice usa o fake; teste contra o serviço real fica marcado e fora do CI padrão.
- Credenciais só por variável de ambiente / cofre de segredos. Nada no código.
- Contrato de cada parceiro (formato, erros, eventos, idempotência): `docs/contracts/<parceiro>.md`.
