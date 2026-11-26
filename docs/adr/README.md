# ADRs: decisões registradas

Uma decisão por arquivo, numerada, **imutável**. Mudou de ideia? Novo ADR que "substitui o 000X", e o antigo ganha `Status: substituído por 000Y`.
Formato: Contexto → Decisão → Consequências. Curto. Comece copiando `0000-template.md`.

As decisões 0001–0007 vêm do boilerplate e valem para todo projeto criado a partir dele. Decisões do projeto começam em 0008.

| # | Decisão | Status |
|---|---|---|
| 0001 | Monolito modular com vertical slices e domínio puro | aceito |
| 0002 | Django 5 + Django Ninja | aceito |
| 0003 | Código em inglês, docs em português, glossário obrigatório | aceito |
| 0004 | Worker sem broker (advisory lock + agendador simples) | aceito |
| 0005 | Processo caseiro: main direta, checagem automática e diário | aceito |
| 0006 | Módulos de negócio em `modules/`, separados da infraestrutura | aceito |
| 0007 | Agentes de IA: AGENTS.md e .agents/ como fonte única (Claude e Codex) | aceito |
| 0008 | Este serviço é o app de gestão da arquitetura Glina e pode ser vendido sozinho | aceito |
| 0009 | Migrations fora do git; o agente nunca roda makemigrations nem migrate | aceito |
