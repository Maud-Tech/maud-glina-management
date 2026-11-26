# 0005: Processo caseiro: main direta, checagem automática e diário

Status: aceito (24/11/2026)

## Contexto
Times pequenos trabalhando com IA, cada frente em módulos diferentes, sem o ritual de PR + revisão obrigatória. Mas código escrito por IA entrando quebrado na `main` é um risco real, e precisamos lembrar o que foi feito e por quê.

## Decisão
1. **Todo mundo commita na `main`**, em commits pequenos, com `git pull --rebase` antes de começar e antes de subir. Branch só para experimento ou trabalho de mais de 1–2 dias.
2. **CI de bolso:** o hook `.githooks/pre-push` roda `scripts/check.py` (banco, formato, lint, tipos, fronteiras, migrations, testes). Se falhar, o push não sobe. Instalação, uma vez por clone: `git config core.hooksPath .githooks`.
3. **Terminar = checar + documentar:** atualizar o `AGENTS.md` do módulo (lista de slices), escrever uma entrada em `docs/journal.md` e, se houve decisão de projeto, um ADR.
4. **Commit no formato `<módulo>: <o que mudou>`**, em português. Ex.: `example: busca de itens por trecho do nome`.
5. **Revisão só onde dói, sem travar:** quando o push mexe em `shared/`, `api.py`, migrations, `tests/acceptance`, `docs/contracts` ou nas instruções dos agentes, o hook mostra a lista e quem subiu avisa o time. Cada projeto acrescenta os seus módulos críticos em `SENSITIVE` (`scripts/check.py`).
6. `git push --no-verify` só em emergência, com o motivo registrado no diário.

## Gatilhos para adotar PR (só nas partes sensíveis)
- Antes de entrar em produção com dinheiro ou dado real de cliente: o PR vira a trilha de "quem aprovou o quê".
- Se a `main` quebrar duas vezes por algo que uma segunda pessoa teria pego.

O CI no GitHub (`.github/workflows/ci.yml`) roda a cada push como rede de segurança extra. Ele não bloqueia ninguém.

## Consequências
- Quase nenhum ritual novo: as checagens são automáticas e a documentação é escrita pela IA no fim da tarefa.
- A revisão depende de as pessoas avisarem; o hook lembra, mas não obriga.
