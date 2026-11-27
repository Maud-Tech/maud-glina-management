# entities: cadastro mestre de entidades

Responsável por: países, moedas e identidade cadastral de pessoas físicas e jurídicas,
incluindo endereços, contatos e arquivamento.
Não faz: papéis exercidos em outros domínios, KYC/AML, contas bancárias, custódia,
estrutura societária, documentos ou arquivos cadastrais.

## Invariantes
- Toda referência de outro módulo aponta para `Entity`, nunca diretamente para seus detalhes.
- `Entity.entity_kind` coincide com exatamente um detalhe: `EntityPerson` ou `EntityCompany`.
- País e número de registro são preenchidos juntos; empresa exige ambos.
- Uma entidade arquivada preserva identidade e vínculos históricos.
- Existe no máximo um endereço primário por tipo e um contato primário por tipo.
- Escrita será feita pelas slices; o admin é somente leitura.

## Fachada (api.py)
- `reference_queryset(kind)`: consulta pública de moedas, países e identidades de
  entidades para seleção nos formulários de ativos; não expõe detalhes de pessoa/empresa.

## Slices
- `list_registrations`: consulta autenticada, busca, filtros e paginação por cadastro.
- `save_registration`: criação/edição transacional e idempotente; formulário separado
  retorna à lista do próprio cadastro. Natureza/família fixa após a criação.
  Pessoa inclui formsets opcionais de endereços/contatos, com permissões próprias;
  itens preenchidos são validados e gravados na mesma transação. PJ usa os 12
  setores definidos em `COMPANY_SECTORS`; moeda omite casas decimais e usa o default 2.

## Telas
`pages.py` expõe lista, novo e detalhe/edição por cadastro, com permissões Django
`view`, `add` e `change`. Vínculos também são acessíveis pelo detalhe do registro pai.
Nenhuma tela faz exclusão física.

## domain/
_(vazio até a primeira slice; as regras puras serão centralizadas aqui)_
