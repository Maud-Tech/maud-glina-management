# Glossário

Fonte única dos termos. **Todo nome no código é em inglês** (arquivos, classes, funções, variáveis, testes, campos, eventos); **comentários, docs e mensagens podem ser em português** ([ADR 0003](adr/0003-language.md)). A coluna "Código" é o nome que se usa no código. Termo novo entra aqui antes de entrar no código.

## Termos do negócio

Os nomes em inglês ainda **não foram escolhidos**: escolha com o time e preencha a coluna "Código" antes de criar o primeiro módulo. As definições abaixo são só o que o desenho da arquitetura diz.

| Português (negócio) | Código | Definição |
|---|---|---|
| App de gestão | este app (`maud-glina-management`) | Sabe o que existe e quanto vale. Não conhece cliente. |
| Apólice | _a definir_ | Tem fechamento por data e versão, e um total conferido. |
| Conta corrente | _a definir_ | _a definir com o time_ |
| Ativo | _a definir_ | _a definir com o time_ |
| Movimento | _a definir_ | _a definir com o time_ |
| Posição | _a definir_ | Conferida com a custódia. |
| Preço | _a definir_ | Ingerido pelo Worker. |
| PL | _a definir_ | Calculado por data. |
| Custódia | _a definir_ | De onde vêm extratos, posições e preços, e contra quem a posição é conferida. |
| Extrato | _a definir_ | Ingerido pelo Worker. |
| Fechamento | _a definir_ | Tem apólice, data, versão e status. |
| Versão | _a definir_ | Reprocessar gera versão nova; a antiga fica gravada. |
| Preliminar / oficial / retificado | _a definir_ | Status do fechamento. Preliminar tem pendências nomeadas; retificado é versão nova, com motivo e delta. |
| Pendência | _a definir_ | Informação que falta num fechamento preliminar. Tem nome. |
| Total conferido | _a definir_ | Total da apólice que bateu com a custódia. Só o que bateu conta. |
| Item | `Item` | Registro do módulo de demonstração `example`. Apague quando o módulo sair. |

## Termos da arquitetura (vêm do boilerplate)

| Português | Código | Definição |
|---|---|---|
| Módulo | `src/maud/modules/<módulo>/` | Contexto de negócio. Só importa módulos abaixo dele, e só pelo `api.py`. |
| Fachada | `api.py` | Única parte de um módulo que outros módulos podem importar. Mudar é mudar contrato. |
| Slice / caso de uso | `features/<verbo_substantivo>/` | Um comando ou uma consulta, com handler, schemas, endpoint e teste juntos. |
| Comando / consulta | `<Acao>Command` / `<Acao>Query` | Entrada de uma slice que muda dados / que só lê. |
| Domínio | `domain/` | Regras puras do módulo: sem Django, sem banco, sem relógio. |
| Data-base | `base_date` | Dia a que um número se refere (não confundir com quando foi calculado). |
| Dinheiro | `Money` | Valor + moeda, em Decimal. Moedas diferentes não operam; arredondar é explícito. |
| Cota | `Shares` | Quantidade de cotas, em Decimal com até 8 casas. Excesso de casas é recusado. |
| Outbox | `OutboxEvent` | Fila de eventos para fora, gravada na mesma transação do fato; o Worker entrega. |
| Chave de idempotência | `Idempotency-Key` | Identificador do pedido; repetir não duplica o efeito. |
| Ledger | `append_only(...)` | Tabela de lançamentos só com INSERT. Correção é estorno, nunca UPDATE/DELETE. |
| Estorno | `reversal` | Lançamento que anula outro, referenciando-o. O original nunca é apagado. |
