# 0007: Agentes de IA: `AGENTS.md` e `.agents/` como fonte única

Status: aceito (24/11/2026)

## Contexto
Times usam mais de um agente: Claude Code e Codex. Cada um procura as instruções num lugar diferente:

| | Claude Code | Codex |
|---|---|---|
| Instruções | `CLAUDE.md`; o de uma subpasta é carregado quando ele trabalha nela; aceita `@arquivo` | `AGENTS.md`, só os do caminho raiz → pasta onde foi aberto, no início; sem `@arquivo` |
| Skills | `.claude/skills/` | `.agents/skills/` |
| Hooks | `.claude/settings.json` | `.codex/hooks.json` (cada pessoa aprova uma vez em `/hooks`) |

Manter duas cópias à mão é garantia de que elas vão divergir, e o agente confia no que está escrito.

## Decisão
1. **Fonte única:** `AGENTS.md` (raiz e pastas) e `.agents/` (skills e hooks). Só se edita ali.
2. **O que é do Claude é gerado** por `scripts/sync_agents.py`: um `CLAUDE.md` com `@AGENTS.md` ao lado de cada `AGENTS.md`, e `.claude/skills/` como cópia de `.agents/skills/`. O `check.py` (e portanto o pre-push) falha se estiver desatualizado.
3. **Hooks:** um script só (`.agents/hooks/`), ligado nos dois agentes. Ele entende a edição do Claude (`file_path`) e o patch do Codex (`apply_patch`).
4. **O `AGENTS.md` raiz manda ler o `AGENTS.md` da pasta antes de mexer nela**, porque o Codex não carrega o do módulo sozinho.
5. Nada no `AGENTS.md` depende de recurso exclusivo de um agente.

## Consequências
- Agente novo que leia `AGENTS.md` funciona sem mudança. Se ele exigir outro arquivo, entra no `sync_agents.py`.
- Hooks só pegam edição pela ferramenta de edição. Mudança feita via shell (`sed`, script) passa. A rede de segurança continua sendo o pre-push, que lista partes sensíveis, e o fato de teste de aceitação ser cenário de negócio.
- O tamanho conta: o Codex para de ler instruções depois de 32 KiB somados. Os `AGENTS.md` continuam curtos.
