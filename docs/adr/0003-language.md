# 0003: Nomes em inglês, textos em português, glossário obrigatório

Status: aceito (25/11/2026)

## Contexto
O time e o negócio falam português. Bibliotecas, frameworks e contratos com parceiros são em inglês. Misturar os dois idiomas nos **nomes** do código (`calcular_total_fee`, `test_reserva_is_valid`) é o pior cenário: ninguém sabe qual idioma usar, a busca falha, e os agentes de IA inventam uma terceira variação.

## Decisão
**Tudo que é nome é em inglês. Tudo que é texto livre pode ser em português.**

| Inglês (nome) | Português (texto) |
|---|---|
| arquivos e pastas (inclusive `docs/`, skills, testes) | comentários e docstrings |
| módulos, classes, funções, métodos, variáveis, constantes, parâmetros | conteúdo dos `.md` (docs, ADRs, `AGENTS.md`) |
| **nomes de teste** (`test_duplicate_name_is_rejected_with_409`) | `message` de erro e logs (lidos por humanos) |
| campos de schema/JSON, rotas, tabelas e colunas | `verbose_name`, textos de admin e de tela |
| códigos de erro (`code`), nomes de evento, nomes de job | mensagens de commit e entradas do diário |

Convenções (PEP 8):
- `snake_case` para arquivos, módulos, funções, variáveis; `PascalCase` para classes; `UPPER_SNAKE_CASE` para constantes.
- Nomes descrevem o que a coisa é ou faz, sem abreviação obscura (`amount`, não `amt`; `insurer`, não `ins`).
- Teste se chama `test_<sujeito>_<comportamento>_<resultado>`, em inglês, legível como frase: `test_reservation_above_available_is_rejected`.
- Termo de negócio: o nome em inglês vem do `docs/glossary.md`. Termo novo entra lá **antes** de entrar no código.

## Consequências
- Verificação automática: `ruff` recusa identificador com acento (`PLC2401`) e `tests/architecture/test_english_names.py` recusa nomes com palavras comuns em português.
- O português continua onde ajuda a entender: o comentário explica a regra de negócio, a docstring do teste pode descrever o cenário com as palavras do negócio.
- Códigos de erro e nomes de evento são parte do contrato com parceiros: em inglês e estáveis.
