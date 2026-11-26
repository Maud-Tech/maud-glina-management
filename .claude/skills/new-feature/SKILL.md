---
name: new-feature
description: Criar uma slice (caso de uso) nova num módulo. Use sempre que for implementar comando, consulta, endpoint ou job novo. Impõe cenários antes de código.
---

# Nova feature (slice)

Copie a **forma** (não o conteúdo) das slices de referência: comando `src/maud/modules/example/features/create_item/`, consulta `src/maud/modules/example/features/list_items/`.

## 1. Localize antes de escrever
- Qual módulo é dono do dado que muda? (`AGENTS.md` da raiz → tabela de módulos). A slice vive nele. Nenhum módulo é dono? Use a skill `new-module` antes. Nunca crie slice de negócio no `example`.
- Leia o `AGENTS.md` do módulo: invariantes e slices existentes. Se já existe slice parecida, estenda em vez de duplicar.
- Termos: `docs/glossary.md`. Termo novo? Adicione lá primeiro.

## 2. Cenários primeiro (pare e mostre ao humano)
Escreva **só os nomes** dos testes e mostre ao humano antes de implementar. Nome **em inglês**, legível como frase (`test_<sujeito>_<comportamento>_<resultado>`); ao lado de cada um, uma linha em português dizendo a regra de negócio, para o humano validar:
```
test_reservation_with_enough_balance_holds_shares      # reserva com saldo bloqueia as shares
test_reservation_above_available_is_rejected_with_422  # acima do disponível é recusada
test_repeated_request_with_same_key_holds_only_once    # repetir o pedido não bloqueia de novo
```
- caminho feliz, cada recusa de negócio (com o `code` do erro), repetição com a mesma Idempotency-Key, e concorrência se a slice disputa saldo.
- Todo nome novo (arquivo, classe, função, variável, campo, evento, `code`) segue a seção **Nomenclatura** do `AGENTS.md` raiz: inglês, termos do `docs/glossary.md`.
- Se a regra for de aceitação (visível para parceiros/operação), crie também um arquivo NOVO em `tests/acceptance/`.

## 3. Estrutura
```
src/maud/modules/<módulo>/features/<verbo_substantivo>/
    __init__.py
    handler.py        # docstring: o que faz, invariantes, idempotência, evento, erros
    schemas.py        # entrada/saída (ninja.Schema)
    endpoint.py       # só se exposta via HTTP
    test_<nome>.py
    SPEC.md           # só se tiver máquina de estados ou cálculo denso
```
Regra que outras slices do módulo também usam → `src/maud/modules/<módulo>/domain/` (pura, testada sem banco em `domain/tests/`).

## 4. Handler (ordem fixa)
Convenção de nomes: a entrada é uma dataclass `<Acao>Command` (comando) ou `<Acao>Query` (consulta), a função pública é `execute(...)`, as respostas são `<Coisa>Response` / `<Coisa>ListItem`. Passos numerados em comentário.

1. `run_idempotent(...)` se for comando vindo de fora.
2. Carregar dados (ORM direto do próprio módulo; de outros módulos só via `api.py`).
3. Decidir com função pura do `domain/`.
4. Persistir. Lock (`select_for_update`) quando disputa saldo.
5. `outbox.publish("<modulo>.<fato_no_passado>", ...)` na mesma transação.
6. Devolver o schema de saída.

## 5. Ligar
- Endpoint: no `endpoint.py`, `from maud.modules.<módulo>.router import router` e `@router.post(...)` / `@router.get(...)` direto; em `src/maud/modules/<módulo>/routes.py`, uma linha importando o endpoint (e o módulo em `config/api.py` se for o primeiro).
- Job: exponha em `src/maud/modules/<módulo>/jobs.py` e agende em `src/maud/jobs/schedule.py`.
- Fachada: se outro módulo precisa, exponha em `api.py` (mudança de contrato: avise o humano).
- Atualize a lista de slices no `AGENTS.md` do módulo (1 linha).

## 6. Pronto quando
1. `uv run python scripts/check.py` termina com "Tudo certo.".
2. Nenhum teste existente foi alterado (se foi, diga qual e por quê).
3. Todo nome novo está em inglês, inclusive os testes (o `check.py` confere acento e palavras comuns em português, mas não pega tudo: revise).
4. Lista de slices do `AGENTS.md` do módulo atualizada.
5. Entrada nova no topo de `docs/journal.md`, seguindo o modelo do arquivo.
6. Mensagem de commit sugerida no formato `<módulo>: <o que mudou>`.
7. Se tocou em parte sensível (`shared/`, `api.py`, migrations, `tests/acceptance`, `docs/contracts`, instruções de agentes), lembre o humano de avisar o time.
