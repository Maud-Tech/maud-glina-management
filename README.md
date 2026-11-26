# maud-glina-management

O **app de gestão** da arquitetura Glina: **sabe o que existe e quanto vale**. Não conhece cliente.

![Arquitetura Glina](docs/glina-architecture.svg)

| Peça do desenho | Repositório | Onde roda |
|---|---|---|
| API (porteiro) | `maud-glina-api` | AWS, conta da Maud |
| App de passivo | `maud-glina-liability` | Maud, dentro de casa |
| **App de gestão** | `maud-glina-management` (este) | Maud, dentro de casa |

## As peças deste app

Um código, dois processos, um banco:

| Peça | O que faz | Comando |
|---|---|---|
| **API** (só leitura, interna) | fechamento por apólice, data e versão; total conferido; pendências | `manage.py runserver` (dev) / gunicorn |
| **Backend** | apólices, contas correntes, ativos; PL por data; oficializa e retifica sem editar versão publicada | os módulos em `src/maud/modules/` |
| **Worker** | ingere extratos, posições e preços; confere com a custódia; reprocessa gerando versão nova | `manage.py worker` |
| **PostgreSQL** | apólices, contas, movimentos, posições, preços, fechamentos (todas as versões), pendências | `docker compose up -d db` |

### Como trata o reprocessamento

- Todo fechamento tem apólice, data, versão e status: **preliminar** (com pendências nomeadas), **oficial**, **retificado** (versão nova, com motivo e delta).
- Reprocessar gera versão nova; a antiga fica gravada.
- Falta de informação sai como preliminar, nunca como estimativa escondida.

### Fronteiras

- Este app **pode ser vendido sozinho**: não sabe que o app de passivo existe e nunca chama ele.
- Quem precisa dos números lê a API de leitura. Hoje, o leitor é o app de passivo.
- Banco separado, nenhuma tabela em comum. Nenhum banco tem rota de fora.

## Situação

Estrutura inicial, criada a partir do `maud-boilerplate`. **Ainda não há módulo de negócio**: só o módulo de demonstração `example`, que sai quando o primeiro módulo real tiver uma slice de comando e uma de consulta (skill `new-module`, seção "Remover o example").

Próximos passos, pelo padrão: definir os termos em `docs/glossary.md`, criar o primeiro módulo com a skill `new-module` e as primeiras slices com `new-feature`.

## Subir local

Pré-requisitos: Python 3.12, [uv](https://docs.astral.sh/uv/) e Docker.

```
cp .env.example .env
docker compose up -d db                  # Postgres na porta 5435
uv sync
uv run python manage.py migrate
git config core.hooksPath .githooks      # uma vez por clone: liga a checagem antes do push
uv run python manage.py runserver 8002   # API em http://localhost:8002/api/v1/docs
uv run python manage.py worker           # Worker (outro terminal)
```

Tudo em containers: `docker compose up --build` (API na porta 8002).

Cada repositório da arquitetura usa portas próprias, para os três rodarem lado a lado: porteiro 8000; passivo 8001 e Postgres 5434; gestão 8002 e Postgres 5435.

No Linux/macOS, se o hook não rodar: `chmod +x .githooks/pre-push`.

## Verificações

```
uv run python scripts/check.py
```

Roda as mesmas verificações do pre-push: agentes de IA sincronizados, banco migrado, formatação, lint, tipos, fronteiras entre módulos, migrations e testes (em Postgres real, nunca SQLite).

## Como trabalhamos

Resumo do [ADR 0005](docs/adr/0005-lightweight-process.md):

- Direto na `main`, commits pequenos, `git pull --rebase` antes de começar e antes de subir.
- Antes de cada push, o hook roda todas as verificações. Se algo falhar, o push não sobe.
- Terminar uma tarefa inclui documentar: entrada nova em [`docs/journal.md`](docs/journal.md) e lista de slices do módulo atualizada.
- **Nomes em inglês, textos em português** ([ADR 0003](docs/adr/0003-language.md)).

## Agentes de IA

Funciona com **Claude Code** e **Codex**. Instruções, skills e hooks têm uma fonte só: `AGENTS.md` e `.agents/`. O que é do Claude (`CLAUDE.md`, `.claude/skills/`) é gerado:

```
uv run python scripts/sync_agents.py
```

Skills: `/new-module`, `/new-feature`, `/new-migration` no Claude; `$new-module`... no Codex. **Codex, uma vez por pessoa:** abra o Codex na raiz do repositório e aprove o hook do projeto em `/hooks`.

## Onde ler

- `AGENTS.md`: mapa do código e regras (vale para humanos e para qualquer agente de IA)
- `docs/context.md`: o papel deste app na arquitetura Glina
- `docs/architecture.md`: por que a estrutura do código é assim
- `docs/adr/`: decisões registradas (a deste app é a 0008)
- `docs/glossary.md`: termos do negócio
- `docs/contracts/`: regras da API, eventos e um arquivo por parceiro
- `docs/journal.md`: o que foi entregue, por quê e o que ficou pendente
