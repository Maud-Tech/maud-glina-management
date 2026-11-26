# tests/acceptance — 🔒 protegido

Cenários de negócio de ponta a ponta. São o **oráculo**: o código se ajusta a eles, nunca o contrário.

- **Agente de IA:** pode **criar** arquivo novo aqui. **Não pode editar** arquivo existente: o hook `.agents/hooks/protect_acceptance_tests.py` bloqueia (no Claude Code e no Codex).
- **Humano:** se um cenário existente estiver errado, mude num commit só para isso, com a justificativa de negócio no diário (`docs/journal.md`), e avise o time para alguém revisar.
- Um teste por regra. Nome em inglês, legível como frase: `test_<sujeito>_<comportamento>_<resultado>` (ex.: `test_partner_receives_event_at_least_once_even_after_failures`). A regra em palavras do negócio pode ir na docstring, em português.
- Passe pela API pública (HTTP) sempre que possível. Não importe internals de módulo.
