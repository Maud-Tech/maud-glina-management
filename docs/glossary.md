# Glossário

Fonte única dos termos. **Todo nome no código é em inglês** (arquivos, classes, funções, variáveis, testes, campos, eventos); **comentários, docs e mensagens podem ser em português** ([ADR 0003](adr/0003-language.md)). A coluna "Código" é o nome que se usa no código. Termo novo entra aqui antes de entrar no código.

## Termos do negócio

Os termos já implementados têm nome em inglês definido. Os demais permanecem a definir com o time antes de entrarem no código.

| Português (negócio) | Código | Definição |
|---|---|---|
| App de gestão | este app (`maud-glina-management`) | Sabe o que existe e quanto vale. Não conhece cliente. |
| Gestora | _a definir_ | Quem usa e opera uma instalação do app (white label). Uma instalação por gestora. |
| Identidade da gestora | `branding` (módulo) | Nome, logotipo, ícone da aba e cor principal que a gestora escolhe. |
| Anexo | _a definir_ | Arquivo enviado pela tela (imagem, PDF). Fica no storage padrão do Django. |
| Apólice | `Policy` | Seguro feito com a seguradora para um produto (1:1 por enquanto). Tem vigência, status (`ACTIVE`, `EXPIRED`) e, mais adiante, fechamento por data e versão e um total conferido. |
| Seguradora | `insurer_entity` | Papel de uma `Entity` jurídica (`entity_kind = COMPANY`) na apólice. Aponta para `Entity`, nunca para `EntityCompany`. |
| Vigência | `effective_from` / `effective_until` | Período em que a apólice (ou a versão do regulamento) vale. O fim é opcional e inclusivo. |
| Produto | `Product` | O que a Glina mostra na vitrine. Tem código, moeda-base (USD por padrão) e status. |
| Status do produto | `DRAFT` · `ACTIVE` · `INACTIVE` · `EXPIRED` · `CLOSED` | Rascunho, ativo, inativo (não recebe entradas), expirado (junto com a apólice) e encerrado (final). |
| Regulamento (apelido: mandato) | `Mandate` | Regras do produto, como um IPS: nível de risco, retorno-alvo, liquidez, prazo médio máximo, classes elegíveis, entrada e saída. Tem versões; versão publicada nunca muda e vale para todos, inclusive quem já comprou. |
| Versão do regulamento | `Mandate.version` | 1, 2, 3… por produto. Um rascunho por vez; publicar dá número e data de vigência. |
| Nível de risco | `risk_level` | Escala de 1 (menor risco) a 5. |
| Retorno-alvo | `target_return_benchmark` + `target_return_spread_pct` | Benchmark (hoje só SOFR) mais um spread em % ao ano. |
| Prazo médio máximo | `max_average_term_years` | Teto, em anos, do prazo médio da carteira da apólice. O prazo médio em si é calculado da carteira. |
| Limite de exposição | `ExposureLimit` | Mínimo e máximo em % do PL por classe de ativo, emissor, ativo único, país ou moeda. Pertence a uma versão do regulamento. |
| Documento do produto | `ProductDocument` | PDF ligado ao produto (e, se for o caso, à apólice): regulamento, lâmina, contrato. Arquivado, nunca apagado. |
| Histórico do produto | `ProductChange` | Linha append-only por alteração em produto, apólice ou documento: quem, quando, antes e depois, motivo. |
| Histórico do regulamento | `MandateChange` | Linha append-only por alteração no regulamento ou nos seus limites, do rascunho à publicação. |
| Conta corrente | _a definir_ | _a definir com o time_ |
| Ativo | `Asset` | Identidade central de qualquer ativo offshore. |
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
| Moeda | `Currency` | Moeda disponível para países e futuros ativos, identificada pelo código ISO 4217. |
| País | `Country` | País identificado pelo código ISO 3166-1 alpha-2 e sua moeda principal. |
| Entidade | `Entity` | Identidade central de uma pessoa física ou jurídica, referenciada pelos demais módulos. |
| Pessoa física | `EntityPerson` | Detalhes exclusivos de uma entidade cuja natureza é `PERSON`. |
| Pessoa jurídica | `EntityCompany` | Detalhes exclusivos de uma entidade cuja natureza é `COMPANY`. |
| Endereço da entidade | `EntityAddress` | Endereço internacional associado a uma entidade. |
| Contato da entidade | `EntityContact` | E-mail ou telefone associado a uma entidade. |
| Ativo | `Asset` | Identidade central de qualquer ativo offshore. |
| Casa de negociação | `TradingVenue` | Mercado ou bolsa em que um ativo pode possuir uma listagem. |
| Listagem do ativo | `AssetListing` | Ticker de um ativo em uma casa de negociação específica. |
| Identificador do ativo | `AssetIdentifier` | Código externo ou interno, como ISIN, CUSIP, SEDOL ou FIGI. |
| Caixa | `CashAsset` | Moeda representada como ativo único e compartilhado. |
| Renda variável | `Equity` | Ação, recibo ou unidade negociável vinculada a um ativo. |
| Instrumento de dívida | `DebtInstrument` | Bond, note ou outro instrumento que representa uma dívida. |
| Fundo | `Fund` | Classe de cotas negociável cadastrada como ativo independente. |
| Ativo genérico | `GenericAsset` | Ativo temporário ainda não normalizado para uma família definitiva. |
| Classificação do ativo | `AssetClassification` | Classe estratégica, subclasse, risco e liquidez de um ativo. |
| Preço do ativo | `AssetPrice` | Preço de um ativo em uma data e tipo (MKT, MD ou CURVE), sem cadastro de fontes. |
| Preço de mercado | `AssetPrice.Type.MKT` | Preço de mercado de referência disponível para o ativo. |
| Última cotação disponível | `AssetPrice.Type.MD` | Última cotação do dia para ativo negociado sem preço médio ANBIMA. |
| Preço de curva | `AssetPrice.Type.CURVE` | Preço de dívida sem marcação a mercado. |
| Evento do ativo | `AssetEvent` | Evento econômico ou societário associado a um ativo, identificado por tipo, Data COM e liquidação. |
| Data COM | `event_date` | Data em que nasce o direito econômico do evento. |
| Preço COM | `cum_price` | Preço do ativo antes do evento, usado no cálculo do fator. |
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
