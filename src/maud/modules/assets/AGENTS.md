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
- Instrumento não perpétuo possui vencimento posterior à emissão; valores nominais são positivos.
- Cada classe de cotas de fundo é um ativo independente.
- Preço é único por ativo, data, tipo e fonte.
- Escrita será feita pelas slices; o admin é somente leitura.

## Fachada (api.py)
_(vazia até outro módulo precisar consultar ativos)_

## Slices
_(nenhuma; esta entrega cria somente os models)_

## domain/
_(vazio até a primeira slice; as regras puras serão centralizadas aqui)_
