# assets: cadastro mestre de ativos offshore

Responsável por: identidade, identificadores, listagens, detalhes por família, classificação,
preços e eventos de ativos offshore.
Não faz: clientes, contas de custódia, posições, operações, processamento de carteiras ou
cadastro mestre de pessoas e empresas.

Depende de: `entities` para moedas, países e entidades que exercem papéis no contexto do ativo.

## Invariantes
- Todo ativo possui moeda, tipo de mercado e exatamente um detalhe compatível com sua família.
- Papéis como emissor, gestor e custodiante apontam para `Entity`; a slice valida a natureza.
- Um ticker pertence a uma `AssetListing` e é único dentro da casa de negociação.
- Uma moeda possui no máximo um `CashAsset`; seu ativo usa a mesma moeda.
- Identificadores externos são únicos pela combinação de tipo e valor.
- Instrumento não perpétuo possui vencimento posterior à emissão; lote mínimo, quando informado, é positivo.
- Cálculos de accrual usam o padrão fixo de 252 dias úteis; não há convenção configurável por ativo.
- Cada classe de cotas de fundo é um ativo independente e pode apontar para seu fundo pai.
- Preço é único por ativo, data e tipo (MKT, MD ou CURVE); não há cadastro de fontes.
- Evento é único por ativo, tipo, Data COM e liquidação; `cum_price` é o Preço COM.
- Escrita será feita pelas slices; o admin é somente leitura.

## Fachada (api.py)
_(vazia até outro módulo precisar consultar ativos)_

## Slices
- `list_registrations`: consulta autenticada, busca, filtros e paginação por cadastro.
- `save_registration`: criação/edição transacional e idempotente; formulário separado
  retorna à lista do próprio cadastro. Natureza/família fixa após a criação.
  O formulário de ativo inclui identificadores opcionais, com inclusão, edição e remoção
  conforme permissões próprias, gravados na mesma transação do ativo.

## Telas
`pages.py` expõe lista, novo e detalhe/edição por cadastro, com permissões Django
`view`, `add` e `change`. Vínculos também são acessíveis pelo detalhe do registro pai.
Nenhuma tela faz exclusão física.
Identificadores não aparecem como cadastro independente no menu nem como link de
lista no detalhe do ativo. As rotas anteriores são mantidas por compatibilidade.
Remoção explícita de identificador dentro do ativo exige `delete_assetidentifier`.

## domain/
_(vazio até a primeira slice; as regras puras serão centralizadas aqui)_
