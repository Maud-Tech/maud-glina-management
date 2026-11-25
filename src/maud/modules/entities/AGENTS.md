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
_(vazia até outro módulo precisar consultar entidades)_

## Slices
_(nenhuma; esta entrega cria somente os models)_

## domain/
_(vazio até a primeira slice; as regras puras serão centralizadas aqui)_
