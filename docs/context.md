# Contexto do projeto

> O documento que humanos e agentes de IA leem para entender o negócio. Curto de propósito: decisão vira ADR, termo vira glossário.
> Desenho completo: [`glina-architecture.svg`](glina-architecture.svg).

## 1. Em uma frase
O **app de gestão** sabe o que existe e quanto vale. Não conhece cliente.

## 2. Quem é dono do quê
| Assunto | Dono | Observação |
|---|---|---|
| Apólices, contas, movimentos, posições, preços | **Este app** | No Postgres dele |
| Fechamentos (todas as versões), total conferido, pendências | **Este app** | Publicados pela API de leitura |
| Clientes, pedaços, reservas, negócios | App de passivo (`maud-glina-liability`) | Este app não conhece nada disso |
| Extratos, posições e preços de origem | Custódia | Este app ingere e confere |

## 3. Atores e parceiros
```
Custódia ──extratos, posições, preços──► Worker deste app (ingere e confere)

Leitor interno ──lê (sentido único)──► API de leitura deste app
(hoje: o app de passivo)
```
Este app não sabe quem lê e nunca chama o leitor. Por isso pode ser vendido sozinho.

## 4. As peças
| Peça | O que faz |
|---|---|
| Telas (white label) | toda a operação da gestora: cadastros, conferência, fechamentos, pendências, personalização ([ADR 0010](adr/0010-web-screens-white-label.md), [`ui.md`](ui.md)) |
| API (só leitura, interna) | fechamento por apólice, data e versão; total conferido; pendências |
| Backend | apólices, contas correntes, ativos; PL por data; oficializa e retifica sem editar versão publicada |
| Worker | ingere extratos, posições e preços; confere com a custódia; reprocessa gerando versão nova |
| PostgreSQL | apólices, contas, movimentos, posições, preços, fechamentos (todas as versões), pendências |

## 5. Regras que não podem quebrar
Como trata o reprocessamento:
- Todo fechamento tem apólice, data, versão e status: preliminar (com pendências nomeadas), oficial, retificado (versão nova, com motivo e delta).
- Reprocessar gera versão nova; a antiga fica gravada.
- Falta de informação sai como preliminar, nunca como estimativa escondida.

E também:
- A gestão confere a posição de cada apólice com a custódia e publica o total conferido. Só o que bateu conta.
- Versão publicada nunca é editada.
- Este app não conhece cliente e não sabe que o app de passivo existe.
- Banco separado, nenhuma tabela em comum. Nenhum banco tem rota de fora.

Elas viram testes em `tests/acceptance/` e `tests/properties/`.

E sobre as telas:
- Cada gestora tem a sua instalação, com o seu nome, logotipo e cor.
- Todo cadastro tem tela, e a tela grava pela slice.

## 6. Fora de escopo
- Clientes, pedaços, reservas, venda, saldo e posição do cliente: app de passivo.
- Falar com o sistema da Glina ou com o porteiro.
- API de escrita para fora: a API deste app é só de leitura e interna.
- Várias gestoras na mesma instalação.

## 7. Fontes
- Desenho "Arquitetura Glina" (porteiro na AWS + app de passivo + app de gestão), fechado com o time em 26/11/2026.
