---
name: new-module
description: Criar um módulo de negócio novo (ou remover o módulo de demonstração example) no padrão do projeto. Use quando o pedido não cabe em nenhum módulo existente ("criar o módulo X", "um lugar para cuidar de Y").
---

# Novo módulo

Copie a **forma** do `src/maud/modules/example/` (não o conteúdo: `Item`, `create_item` e `list_items` são só demonstração).

## 1. Antes de criar (pare e mostre ao humano)
- **Precisa mesmo de módulo?** Módulo = contexto de negócio com dados e regras próprias. Um caso de uso a mais num contexto que já existe é **slice** (skill `new-feature`), não módulo.
- Proponha ao humano, numa mensagem curta, e espere o ok:
  - nome do módulo (inglês, singular ou nome do contexto, `snake_case`) e o termo em português (vai no glossário);
  - **responsável por / não faz** (1 linha cada);
  - **posição nas camadas:** de quais módulos ele depende (fica acima deles) e quais vão depender dele;
  - as primeiras slices previstas (só nomes).

## 2. Estrutura
```
src/maud/modules/<modulo>/
    __init__.py
    AGENTS.md            # responsabilidade, invariantes, fachada, slices, domain/ (forma do example)
    apps.py              # name="maud.modules.<modulo>", label="<modulo>", verbose_name em português
    api.py               # fachada: docstring padrão, vazia até alguém precisar
    router.py            # Router(tags=["<modulo>"])
    routes.py            # importa os endpoints das slices (vazio até a 1ª rota)
    models.py            # docstring: "Só este módulo escreve nestas tabelas."
    admin.py             # só se houver model; somente leitura
    domain/__init__.py
    features/__init__.py
    migrations/__init__.py
```
`jobs.py` só quando houver job. Testes de `domain/` em `domain/tests/`.

## 3. Ligar (os três lugares têm de concordar na ordem das camadas)
1. `src/maud/config/settings.py` → `INSTALLED_APPS`: entre `maud.shared` e `maud.jobs`, na ordem de dependência (de baixo para cima). A `integration` não é app Django (não tem tabelas).
2. `pyproject.toml` → import-linter:
   - contrato **Camadas**: o módulo na posição certa (a lista vai de cima para baixo);
   - contrato **domain/ é puro**: `"maud.modules.<modulo>.domain"` em `source_modules`;
   - contrato novo **"Internas de <modulo> são privadas"** (copie o do example): `source_modules` = todas as outras camadas; `forbidden_modules` = `features`, `domain` e `models` do módulo;
   - inclua `"maud.modules.<modulo>"` no `source_modules` dos contratos "Internas de ..." dos **outros** módulos e do integration.
3. `src/maud/config/api.py` → `api.add_router("/<modulo>", <modulo>_routes.router)` quando a primeira slice tiver rota HTTP.
4. `AGENTS.md` da raiz → linha nova na tabela de camadas.
5. `docs/glossary.md` → o termo do módulo e os primeiros termos do negócio dele.
6. `uv run python scripts/sync_agents.py` (gera o `CLAUDE.md` do módulo).

## 4. Pronto quando
1. `uv run python scripts/check.py` termina com "Tudo certo." (o import-linter confirma a posição).
2. Entrada nova no topo de `docs/journal.md` e, se a posição nas camadas foi uma decisão discutida, um ADR.
3. Mensagem de commit sugerida: `<modulo>: módulo criado`.
4. Lembre o humano de avisar o time (mexeu em `pyproject.toml`, settings e instruções dos agentes).

## Remover o example
Quando o primeiro módulo real tiver uma slice de comando e uma de consulta:
1. Aponte as "slices de referência" do `AGENTS.md` raiz e da skill `new-feature` para as slices reais.
2. Apague `src/maud/modules/example/`; tire-o de `INSTALLED_APPS`, de `config/api.py` e de todos os contratos do `pyproject.toml`.
3. Peça ao **humano** para apagar `tests/acceptance/test_item_creation.py` (é do exemplo, mas a pasta é protegida: o agente não apaga teste de aceitação) e troque `example_*` em `tests/architecture/test_openapi_ids.py` e `tests/concurrency/test_idempotency_race.py` pelas slices reais.
4. Troque `example.item_created` em `docs/contracts/README.md`, tire `Item` do glossário e rode `scripts/sync_agents.py` e `scripts/check.py`.
5. Se o banco de algum ambiente já tem a tabela `example_item`, crie uma migration que a remova antes de apagar o módulo (skill `new-migration`).
