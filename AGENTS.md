# maud-glina-management

O **app de gestão** da arquitetura Glina: sabe o que existe e quanto vale. Não conhece cliente ([ADR 0008](docs/adr/0008-management-app.md)).
Contexto de negócio: `docs/context.md` · Arquitetura: `docs/architecture.md` · Termos: `docs/glossary.md` · Desenho: `docs/glina-architecture.svg`.

## Lugar na arquitetura Glina (ADR 0008)

Três repositórios: `maud-glina-api` (porteiro, AWS), `maud-glina-liability` (app de passivo) e `maud-glina-management` (este). Este roda na Maud, dentro de casa.

- **Pode ser vendido sozinho.** Por isso **não sabe que o app de passivo existe**: nunca chama o passivo, e nenhum nome, endereço ou tabela dele aparece no código daqui.
- **Não conhece cliente.** Nada de cliente, pedaço, reserva ou venda neste repositório.
- **Banco próprio.** Nenhuma tabela em comum com outro app. Nenhum banco tem rota de fora.
- **A API é só de leitura e interna:** fechamento por apólice, data e versão; total conferido; pendências.
- **White label, uma instalação por gestora** ([ADR 0010](docs/adr/0010-web-screens-white-label.md)). Toda a operação é por tela, em Django + htmx, no padrão de [`docs/ui.md`](docs/ui.md). Todo cadastro tem tela; o admin é só leitura.
- **Versão publicada nunca é editada.** Reprocessar gera versão nova; a antiga fica gravada.
- **Falta de informação sai como preliminar**, com as pendências nomeadas, nunca como estimativa escondida.

**Situação:** `entities` e `assets` possuem models e telas de listagem, criação e edição.
Cada cadastro tem sua própria lista e o formulário retorna a ela ao salvar ou cancelar.
A casca (`web/`) e `branding` seguem o [ADR 0010](docs/adr/0010-web-screens-white-label.md).

## Mapa (monolito modular; cada pasta tem seu AGENTS.md)

**Antes de mexer em uma pasta de `src/maud/`, leia o `AGENTS.md` dela** (invariantes e slices existentes). Alguns agentes carregam sozinhos, outros não: na dúvida, leia.

Camadas, de baixo para cima. Um módulo **só importa módulos abaixo dele** e **só pelo `api.py`** deles.
**Regra de negócio só em `src/maud/modules/`.** O resto de `src/maud/` é infraestrutura: núcleo comum, bordas e entrypoints ([ADR 0006](docs/adr/0006-modules-separate-from-infra.md)).

| # | Pasta | Responsável por |
|---|---|---|
| 1 | `shared/` | Núcleo: Money, Shares, clock, erros, idempotência, outbox, proteções de banco |
| 2 | `modules/branding/` | Identidade da gestora (white label): nome, cor, logotipo, ícone da aba |
| 3 | `modules/entities/` | Cadastro mestre de pessoas físicas e jurídicas, países, moedas, endereços e contatos |
| 4 | `modules/assets/` | Cadastro mestre, classificação, preços e eventos de ativos offshore |
| 5 | `modules/example/` | **Demonstração** (não é negócio): a forma de um módulo e das slices de referência. Apagar quando existir um módulo real |
| 6 | `integration/` | Bordas: adapters de parceiros e entrega do outbox (webhook) |
| 7 | `jobs/`, `web/`, `config/` | Entrypoints: Worker (agenda), telas (casca, login, painel) e API/URLs |

Módulo novo entra nesta tabela, entre `shared/` e `integration/`, na ordem de dependência (skill `new-module`).

## Anatomia de um módulo

`api.py` (fachada p/ outros módulos) · `router.py` + `routes.py` (rotas HTTP p/ config) · `pages.py` (telas p/ config) · `jobs.py` (jobs p/ Worker) · `domain/` (regras **puras**, sem Django) · `features/<slice>/` (handler, endpoint, schemas, test) · `models.py` · `migrations/` · `admin.py`.
**Onde ficam os testes:** na slice, ao lado do handler (`features/<slice>/test_*.py`). Fora de slice (`domain/`, `shared`, `jobs`), numa subpasta `tests/`. Testes transversais em `tests/` na raiz (acceptance, properties, concurrency, architecture).
**Não há camada de repository:** a slice usa o ORM do próprio módulo direto. Consulta repetida por várias slices do módulo → `<módulo>/queries.py`. Dado de outro módulo → `api.py` dele.
**Terceiros:** só em `integration/adapters/<parceiro>/`. Módulos de negócio nunca chamam terceiros (ver `src/maud/integration/AGENTS.md`).
**Caches:** tudo em `.cache/` (ignorado pelo git).
**Slices de referência** (copie a forma, não o conteúdo): comando `modules/example/features/create_item/`, consulta `modules/example/features/list_items/`.

## Pedido do dev → caminho no padrão

| O dev pede | Faça assim |
|---|---|
| "criar o módulo X" / "um lugar para cuidar de Y" | skill `new-module` |
| "cadastrar / consultar / calcular / rotina de ..." | skill `new-feature` (cenários antes de código) |
| tela nova ou mudança visual | protótipo em `docs/ui/` + imagem para o humano aprovar **antes** do código; padrão em `docs/ui.md` |
| mudar tabela, campo, constraint | skill `new-migration` |
| falar com um sistema de fora (API, webhook, arquivo) | adapter em `integration/adapters/<parceiro>/` (forma do `webhook/`) + contrato em `docs/contracts/<parceiro>.md` |
| decisão que vale para o projeto todo | ADR novo em `docs/adr/` (copie `0000-template.md`) |

Pedido que não cabe em nenhum caminho: pare e pergunte antes de inventar estrutura nova.

## Comandos

```
docker compose up -d db               # Postgres de dev (porta em POSTGRES_PORT, padrão 5435)
uv sync                               # dependências
# makemigrations e migrate: só o humano roda, na máquina dele (migration não vai para o git)
uv run python scripts/check.py        # TODAS as verificações (o mesmo que roda antes do push)
uv run pytest                         # só os testes (Postgres real; nunca SQLite)
```

Antes de dizer que terminou: **`uv run python scripts/check.py` termina com "Tudo certo."**

## Como trabalhamos (ADR 0005)

- Direto na `main`, commits pequenos. `git pull --rebase` antes de começar e antes de subir.
- Commit: `<módulo>: <o que mudou>`, em português. Ex.: `example: busca de itens por trecho do nome`.
- O hook de `pre-push` roda o `scripts/check.py`; se falhar, o push não sobe. Nunca sugira `--no-verify`.
- **Terminar = checar + documentar:** (1) `scripts/check.py` passa, (2) lista de slices do `AGENTS.md` do módulo atualizada, (3) entrada nova no topo de `docs/journal.md` (modelo no próprio arquivo), (4) ADR se houve decisão de projeto.
- Mexeu em `shared/`, `api.py`, `models.py`, `tests/acceptance`, `docs/contracts` ou nas instruções dos agentes: diga ao humano para avisar o time.

## Regras duras

1. **Nunca edite teste existente em `tests/acceptance/`** (o hook bloqueia). Cenário novo = arquivo novo. Se um cenário parece errado, pare e pergunte.
2. **Não ajuste teste para passar.** Teste falhando = código errado até prova em contrário. Mudar asserção existente exige dizer por quê ao humano.
3. **Dinheiro e cotas são `Money`/`Shares` (Decimal).** `float` é proibido em `src/` (teste de arquitetura). Arredondar é sempre explícito.
4. **`domain/` é puro:** sem Django, sem I/O, sem relógio. Recebe dados, devolve decisão.
5. **Escrita vinda de fora é idempotente** (`run_idempotent`) e **todo fato publicado para fora vai pelo outbox** na mesma transação.
6. **Ledgers são append-only** (`@append_only` de `shared.db` no model; os triggers entram a cada `migrate`). Correção = estorno, nunca UPDATE/DELETE.
7. **Migration não vai para o git, e o agente nunca roda `makemigrations` nem `migrate`** ([ADR 0009](docs/adr/0009-migrations-out-of-git.md)). Mudou tabela: altere só o `models.py` e avise o humano, que gera e aplica na máquina dele (skill `new-migration`). O hook `pre-commit`, o `scripts/check.py` e o CI recusam arquivo de migration.
8. **Só o próprio módulo escreve nas suas tabelas.** Outros módulos pedem via `api.py`.
9. **Uma slice por tarefa.** Feature nova: skill `new-feature` (cenários antes de código).
10. **Todo nome em inglês; português só em texto livre** (seção abaixo e [ADR 0003](docs/adr/0003-language.md)).
11. Nada de `datetime.now()` em regra de negócio: use `get_clock().now()`.
12. **Tela grava só pela slice** (o mesmo `handler`), nunca direto no model. Nada de CSS solto na tela nem de recurso vindo de CDN: tudo sai da casca e do `docs/ui.md`.
13. **Arquivo enviado vai pelo storage padrão do Django** (hoje `media/`, depois storage de objetos). Nunca monte caminho de arquivo na mão; abrir arquivo exige login (só o logotipo é público).

## Nomenclatura (ADR 0003)

**Inglês, sempre:** nomes de arquivos e pastas (inclusive docs, skills e testes), módulos, classes, funções, métodos, variáveis, constantes, parâmetros, **nomes de teste**, campos de schema/JSON, rotas, tabelas, colunas, códigos de erro, eventos e jobs.
**Português, à vontade:** comentários, docstrings, conteúdo dos `.md`, `message` de erro, logs, textos de tela/admin, commits e diário.

- `snake_case` (arquivos, funções, variáveis) · `PascalCase` (classes) · `UPPER_SNAKE_CASE` (constantes). Sem abreviação obscura.
- Teste: `test_<sujeito>_<comportamento>_<resultado>`, legível como frase. Ex.: `test_duplicate_name_is_rejected_with_409`. O cenário em palavras do negócio vai na docstring, se ajudar.
- Termo de negócio: o nome em inglês vem de `docs/glossary.md`. Não existe lá? Adicione **antes** de usar no código.

| ❌ Evite | ✅ Use |
|---|---|
| `test_nome_repetido_e_recusado` | `test_duplicate_name_is_rejected` |
| `def calcular_taxa(valor)` | `def calculate_fee(amount)` |
| `aviso = ...` | `event = ...` |
| `docs/diario.md`, skill `nova-feature` | `docs/journal.md`, skill `new-feature` |

A verificação é automática: `ruff` recusa acento em nome e `tests/architecture/test_english_names.py` recusa palavras comuns em português.

## Agentes de IA (Claude Code, Codex, outros)

Fonte única: **`AGENTS.md`** (raiz e pastas) e **`.agents/`** (skills e hooks). Edite só ali ([ADR 0007](docs/adr/0007-ai-agents-single-source.md)).
- Os `CLAUDE.md` e o `.claude/skills/` são **gerados**: `uv run python scripts/sync_agents.py`. O `check.py` falha se estiverem desatualizados.
- Skills: `.agents/skills/<nome>/SKILL.md`. No Claude, `/new-feature`; no Codex, `$new-feature`.
- AGENTS.md novo numa pasta: crie e rode o `sync_agents.py`.

## Onde está o quê

- Decisões já tomadas (não reabrir sem motivo): `docs/adr/`
- Regras da API e dos eventos: `docs/contracts/README.md`; um arquivo por parceiro em `docs/contracts/`
- OpenAPI gerado: `uv run python manage.py export_openapi_schema --api maud.config.api.api --indent 2 --output docs/contracts/openapi.json`
