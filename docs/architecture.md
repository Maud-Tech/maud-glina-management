# Arquitetura interna

> Padrão de estrutura dos projetos Maud: módulos, pastas, banco, documentação e regras para trabalhar com IA.
> Decisões registradas em [adr/](adr/). O estado atual do código está no `AGENTS.md` da raiz.

---

## 1. Em uma linha

**Monolito modular com vertical slices dentro de cada módulo, e um núcleo de regras puras por módulo.**

Os módulos são os contextos de negócio. Dentro de cada um, cada caso de uso é uma fatia vertical autocontida. As regras e invariantes ficam **num único lugar por módulo**, em funções puras, e não espalhadas pelas fatias.

## 2. Por que este estilo (e não os outros)

| Estilo | Avaliação | Veredito |
|---|---|---|
| **Vertical slices puro** | Ótimo para localidade: tudo de um caso de uso numa pasta, ideal para IA. Mas aceita duplicar lógica entre fatias: se uma regra existir em 3 fatias, o agente vai copiar e alterar uma delas. | Usar **dentro** dos módulos |
| **Clean / Hexagonal em camadas** | Separa bem regra de tecnologia, ao custo de port + adapter + repository + use case + DTO para cada CRUD. Muito arquivo para o agente percorrer e muita abstração sem segunda implementação. | Usar **só nas bordas reais** (parceiros, relógio) |
| **Camadas Django tradicionais** (`models.py` único, `services/` com dezenas de arquivos) | Termina em arquivos de milhares de linhas, ORM misturado com regra e testes difíceis de isolar. | Evitar |
| **Microserviços** | Times pequenos e domínios que pedem transação ACID: rede e consistência eventual sem necessidade. | Não |
| **Monolito modular + slices + núcleo puro** | Localidade das slices, regras num lugar só, fronteiras verificadas por ferramenta e um deploy só (API e Worker são o mesmo código com dois entrypoints). | ✅ |

## 3. Stack

| Peça | Escolha | Por quê |
|---|---|---|
| Linguagem | Python 3.12+ | Mesmo ecossistema dos outros sistemas da Maud. |
| Framework | **Django 5 + Django Ninja** | ORM com `select_for_update` e transações explícitas, migrations **versionadas**, admin para consulta. O Ninja dá API tipada com Pydantic e OpenAPI automático, que vira contrato para parceiros. |
| Banco | PostgreSQL 16 | Locks de linha, `NUMERIC`, constraints, triggers e advisory locks. **Testes também em Postgres** (nada de SQLite: lock e decimal se comportam diferente). |
| Worker | Processo único `manage.py worker`, agendador simples e **advisory lock** | Sem Redis nem Celery no início ([ADR 0004](adr/0004-worker-without-broker.md)). |
| Eventos para fora | **Transactional outbox** + Worker despacha webhooks assinados com retry | Nenhum evento se perde, nem é emitido sem o fato ter acontecido. |
| Qualidade | `uv`, `ruff`, `mypy` (estrito no `domain/`), `pytest` + `pytest-django`, `hypothesis`, `import-linter` | Fronteiras entre módulos **verificadas por ferramenta**, não pela boa vontade do agente. |

## 4. Módulos e direção de dependência

Cada módulo é uma Django app. **Um módulo só importa os módulos abaixo dele**, e só pela fachada pública `api.py`.

```
  entrypoints   config/ (urls, settings, api)   jobs/ (worker, agendador)
  integration   bordas com terceiros (adapters + despacho do outbox)
  modules/      módulos de negócio, em camadas (o de cima pode usar o de baixo)
  shared        núcleo: Money, Shares, clock, erros, idempotência, outbox, proteções de banco
```

- A ordem das camadas é declarada em **três lugares que precisam concordar**: `INSTALLED_APPS` (settings), contrato `layers` do import-linter (`pyproject.toml`) e a tabela do `AGENTS.md` raiz. A skill `new-module` atualiza os três.
- Quem orquestra fica acima de quem é orquestrado (ex.: um módulo de pedidos acima do de estoque).
- Só o próprio módulo escreve nas suas tabelas; os outros pedem pelo `api.py` dele.

## 5. Árvore de pastas

```
<projeto>/
├── AGENTS.md                       # FONTE: mapa, comandos, regras duras (curto). Lido por qualquer agente
├── CLAUDE.md                       # GERADO: "@AGENTS.md" (o Claude Code lê CLAUDE.md)
├── README.md                       # para humanos: como subir, rodar e começar um projeto novo
├── pyproject.toml                  # deps + ruff + mypy + pytest + import-linter (contratos de fronteira)
├── docker-compose.yml              # postgres, api, worker
├── .agents/                        # FONTE do que é de IA (ADR 0007)
│   ├── skills/                     # new-module, new-feature, new-migration
│   └── hooks/                      # protege testes de aceitação existentes
├── .claude/  .codex/               # ligam skills e hooks em cada agente (.claude/skills é GERADO)
├── docs/
│   ├── context.md                 # o negócio, em linguagem de negócio
│   ├── glossary.md                # PT ↔ código
│   ├── architecture.md              # este arquivo
│   ├── journal.md                   # uma entrada por entrega
│   ├── adr/                        # decisões numeradas e imutáveis
│   └── contracts/                  # semântica da API e dos eventos + openapi.json (GERADO)
├── scripts/
│   ├── check.py                    # TODAS as verificações (o mesmo que roda no pre-push)
│   └── sync_agents.py              # gera CLAUDE.md e .claude/skills a partir da fonte
├── src/maud/
│   ├── config/                     # settings, urls, api (monta os routers dos módulos)
│   ├── shared/                     # núcleo comum (não importa nenhum módulo)
│   ├── modules/                    # SÓ NEGÓCIO (ADR 0006)
│   │   └── example/                # módulo de demonstração (apague quando houver um real)
│   │       ├── AGENTS.md           # responsabilidade, invariantes, fachada, slices
│   │       ├── api.py              # FACHADA: única coisa que outros módulos importam
│   │       ├── router.py routes.py # rotas HTTP (routes.py só importa os endpoints)
│   │       ├── domain/             # PURO: dataclasses + funções. Proibido importar django
│   │       ├── models.py admin.py migrations/
│   │       └── features/
│   │           ├── create_item/    # referência de COMANDO
│   │           └── list_items/     # referência de CONSULTA
│   ├── integration/                # bordas com terceiros (adapters/<parceiro>/ + features/)
│   └── jobs/                       # entrypoint do Worker: agendador + advisory lock + schedule.py
└── tests/
    ├── acceptance/                 # 🔒 PROTEGIDO: cenários de negócio ponta a ponta (o oráculo)
    ├── architecture/               # regras de arquitetura (sem float, operationId estável)
    ├── properties/                 # hypothesis: invariantes
    └── concurrency/                # corridas reais no Postgres
```

### Regras da árvore

- **Teste unitário da slice mora com a slice.** Código fora de slice (`domain/`, `shared`, `jobs`) tem os testes numa subpasta `tests/`. Testes transversais ficam em `tests/` na raiz.
- **Arquivo pequeno.** Acima de ~300 linhas, o arquivo é sinal de slice ou domínio mal cortado. O agente erra mais em arquivo grande.
- **Job é código do módulo, agenda é do `jobs/`.** O job mora no módulo (exposto no `jobs.py` dele); o `jobs/schedule.py` só diz quando roda.

## 6. Anatomia de uma slice

Uma slice é **um caso de uso**: um comando (muda estado) ou uma consulta. O fluxo é sempre o mesmo:

```
endpoint.py  →  handler.py  ─┬─ idempotência (comando vindo de fora)
  (HTTP,          (transação) ├─ carrega dados (ORM direto do próprio módulo; de outros, via api.py)
   schemas)                   ├─ chama funções PURAS do domain (decide)
                              ├─ persiste o resultado (lock quando disputa saldo)
                              └─ publica evento no outbox (mesma transação)
```

Decisões embutidas:

1. **Slice usa o ORM direto, sem repository.** A regra fica testável de outra forma: o `domain/` não conhece ORM e recebe dados simples.
2. **Abstração (port) só nas bordas reais:** parceiros externos e relógio. A implementação fica em `integration/`.
3. **Comando vindo de fora é idempotente:** carrega `Idempotency-Key`, e a repetição devolve a mesma resposta.
4. **Consulta pode atravessar módulos só para leitura**, via `api.py` de cada um. Escrita em tabela de outro módulo é proibida.

Referências prontas: `modules/example/features/create_item/` (comando) e `list_items/` (consulta).

## 7. Banco de dados: a última linha de defesa

Com IA escrevendo código, as regras críticas **também** ficam no banco. Mesmo que um handler esteja errado, o Postgres recusa.

- **Ledgers append-only:** tabelas de lançamento ganham `shared.db.append_only(...)` na migration; um trigger bloqueia `UPDATE`/`DELETE`. Correção é **estorno**.
- **Saldos derivados:** saem da soma do ledger; se precisar de performance, tabela materializada atualizada na mesma transação e conferida por um job.
- **Tipos:** `Decimal` dentro de `Money` e `Shares`; `NUMERIC` no banco. **`float` é proibido** em `src/` (teste de arquitetura).
- **Constraints explícitas:** `CheckConstraint`, `UniqueConstraint` (idempotência, versões por data-base), FKs entre módulos **só no sentido da dependência**.
- **Migrations:** versionadas e revisadas por humano. Nunca editar migração já aplicada (skill `new-migration`).

## 8. Documentação para humanos e IA

**Poucos `.md`, em três níveis**, cada um com um papel. Os arquivos se chamam `AGENTS.md` (lido pelo Codex e outros); ao lado de cada um há um `CLAUDE.md` gerado com `@AGENTS.md` ([ADR 0007](adr/0007-ai-agents-single-source.md)).

| Nível | Arquivo | Quando é lido | O que contém |
|---|---|---|---|
| **Raiz** | `AGENTS.md` | Sempre | Mapa dos módulos, direção das dependências, comandos, regras duras e onde está cada doc. Curto. |
| **Pasta** | `src/maud/.../AGENTS.md` | Ao trabalhar na pasta | Responsabilidade, **invariantes**, fachada, **índice das slices (1 linha cada)**, armadilhas. |
| **Sistema** | `docs/` | Quando a tarefa pede | Contexto, glossário, ADRs, contratos. O *porquê* e o *entre-módulos*. |

**Por que não um `.md` por feature:** a docstring do `handler.py` (o que faz, invariantes, evento, erros) e os nomes de teste, frases em inglês que descrevem o comportamento (`test_duplicate_name_is_rejected_with_409`), **são** a documentação. Um `.md` por feature fica defasado, e doc desatualizada é pior que nenhuma para um agente. Exceção: slice com máquina de estados ou cálculo denso ganha um `SPEC.md` na própria pasta.

## 9. Guardrails para desenvolver com IA

1. **`tests/acceptance/` é protegido:** um hook bloqueia edição de arquivo **existente** (no Claude e no Codex); criar arquivo novo é permitido. O agente pode adicionar cenário, não mudar um existente.
2. **Cenário antes de código:** a skill `new-feature` impõe mostrar os nomes dos testes ao humano antes de implementar.
3. **Fronteiras mecânicas:** o import-linter verifica camadas, `domain/` puro e partes internas privadas.
4. **Testes de propriedade** (`hypothesis`) nas invariantes: o agente não consegue "acertar por coincidência".
5. **Uma slice por tarefa:** a tarefa nomeia o módulo e a slice.
6. **CI de bolso:** `scripts/check.py` roda tudo antes do push ([ADR 0005](adr/0005-lightweight-process.md)).
