# products: produtos, regulamentos e apólices

Responsável por: o produto que a Glina mostra na vitrine, o regulamento dele (apelido: mandato,
`Mandate`) com versões e limites de exposição, a apólice feita com a seguradora, os documentos
(PDF) e o histórico de tudo isso.
Não faz: cliente, pedaço, reserva ou venda (app de passivo); contas, posições, prazo médio
calculado e fechamentos da apólice (entregas futuras); cadastro de moedas e entidades (`entities`).

Depende de: `entities` (moeda, país, seguradora e emissor, pela fachada `reference_queryset`) e
`assets` (classes de ativo, pelas fachadas `asset_class_codes` e `asset_class_choices`).

## Invariantes
- Produto nasce `DRAFT`. Código e moeda-base só mudam no rascunho; a moeda, só sem apólice.
- Status: `DRAFT → ACTIVE | CLOSED`, `ACTIVE ↔ INACTIVE`, `ACTIVE | INACTIVE → CLOSED`.
  `EXPIRED` só chega com a apólice (`expire_policy`) e só vai para `CLOSED`. `CLOSED` é final e nada
  do produto muda depois.
- Ativar exige regulamento publicado e apólice `ACTIVE` vigente hoje.
- Um produto, uma apólice (constraint `uq_policy_one_per_product`; remover para vários).
- A seguradora aponta para `Entity` (regra do `entities`) e a slice exige `entity_kind = COMPANY`.
- Apólice usa a moeda-base do produto. Apólice expirada não muda.
- Regulamento: um rascunho por produto; versão publicada nunca muda e vale para todos, inclusive
  quem já comprou, a partir de `effective_from`. A versão nova começa depois da anterior e, da
  versão 2 em diante, exige motivo.
- Limites: 0 ≤ mínimo ≤ máximo ≤ 100, um por dimensão e alvo; classe de ativo só se elegível;
  país, moeda e emissor existem no `entities`; ativo único tem alvo vazio.
- Documento é só PDF (conferido pelo conteúdo), até 20 MB, no storage padrão. Nunca é apagado:
  é arquivado.
- Toda escrita grava histórico na mesma transação: produto, apólice e documentos em
  `ProductChange`; regulamento e limites em `MandateChange` (limite pelo id, sem chave
  estrangeira, para sobreviver à remoção). As duas tabelas são `@append_only`.
- Escrita só pelas slices; o admin é somente leitura. Sem evento no outbox (ADR 0008).

## Fachada (api.py)
_(vazia até outro módulo precisar de produtos; a leitura do app de passivo será pela API de leitura)_

## Slices
- `create_product`: cadastra em rascunho (USD por padrão).
- `update_product`: altera dados; código e moeda só no rascunho.
- `change_product_status`: ativa, inativa ou encerra.
- `register_policy`: cadastra a apólice (seguradora jurídica, moeda do produto).
- `update_policy`: altera número, seguradora e vigência.
- `expire_policy`: expira a apólice e, com ela, o produto ativo ou inativo.
- `start_mandate_draft`: abre o rascunho da versão seguinte, copiando a última publicada.
- `update_mandate_draft`: grava termos e limites do rascunho (diferença no histórico).
- `publish_mandate`: publica o rascunho com data de vigência (e motivo, da v2 em diante).
- `attach_product_document`: anexa PDF ao produto (e à apólice, se for o caso).
- `archive_product_document`: arquiva o documento.
- `list_products`: lista com busca, status, a versão vigente do regulamento e a apólice.
- `get_product`: produto com apólice, regulamento vigente, próximo, rascunho, versões e documentos.
- `list_product_history`: linha do tempo dos dois históricos, do mais novo ao mais antigo.
- `open_product_document`: entrega o PDF de um documento do produto (só com login).

## Telas
Protótipo aprovado: `docs/ui/products-preview.html` (cenários em `docs/ui/products-scenarios.md`).
Rotas em `pages.py`; cada tela é `page.py` + `page.html` na slice e grava só pelo handler.
- Lista `/products/` (`list_products`), novo (`create_product`), editar (`update_product`).
- Detalhe `/products/<id>/?tab=` com 5 abas (`get_product`): visão geral, regulamento,
  apólice, documentos e histórico. Botões de status e de expirar abrem confirmação.
- Ações sem tela própria (POST e volta ao detalhe): `change_product_status`, `expire_policy`,
  `start_mandate_draft`, `attach_product_document`, `archive_product_document`.
- Apólice nova e editar (`register_policy`, `update_policy`, mesmo template).
- Regulamento `/products/<id>/mandates/<id>/?step=` (`update_mandate_draft`): rascunho em 3
  etapas, com o valor da versão anterior riscado; versão publicada abre só leitura. A etapa 04
  é `publish_mandate`.
- Permissões: ver `view_product`; criar `add_product`; editar, status e documentos
  `change_product`; apólice `add_policy`/`change_policy`; regulamento `change_mandate`.
- Apoio comum: `screens.py` (campos, erros no campo, 404) e `display.py` (rótulos e formatação
  brasileira); pedaços de template `_field.html`, `_form_errors.html`, `_mandate_*.html`.

## Fora das slices
- `queries.py`: leituras repetidas e conferências nos cadastros de outros módulos.
- `history.py`: retratos dos registros e gravação das linhas de histórico.
- `responses.py`: formatos de saída comuns às slices.

## domain/
- `product.py`: status e mudanças permitidas, validação do cadastro, expiração junto com a apólice.
- `policy.py`: número e vigência; apólice vigente num dia.
- `mandate.py`: termos e limites do regulamento, o que falta para publicar, vigência e motivo.
- `changes.py`: diferença entre dois retratos (antes e depois por campo).
