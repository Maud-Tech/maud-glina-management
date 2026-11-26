# 0001: Monolito modular com vertical slices e domínio puro

Status: aceito (23/11/2026)

## Contexto
Times pequenos trabalhando com agentes de IA, em domínios com invariantes fortes. Vertical slices puro tende a duplicar regra entre fatias. Clean/hexagonal completo gera cerimônia sem ganho. Camadas Django tradicionais (um `models.py` gigante, serviços enormes) dificultam teste e IA. Microserviços trariam rede e consistência eventual a problemas que pedem transação ACID.

## Decisão
- Módulos = contextos de negócio, em camadas (ver `AGENTS.md`). Um módulo só importa os de baixo, e só pelo `api.py`.
- Dentro do módulo: uma pasta por caso de uso (`features/<slice>/`), e regras compartilhadas do módulo em `domain/` como funções puras.
- Slices usam o ORM direto (sem repository). Ports só nas bordas reais (parceiros externos, relógio).
- Fronteiras verificadas pelo `import-linter` no `check.py`.

## Consequências
- Localidade: tudo de um caso de uso numa pasta. Regras numa só.
- Mudar `api.py` vira mudança de contrato entre frentes.
- Ao criar módulo novo, os contratos do import-linter precisam ser atualizados (skill `new-module`).
