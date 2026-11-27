# Cadastros de entities e assets — proposta para aprovação

Escopo: telas para os models existentes, sem alteração de banco. O documento do MCore
orienta a organização do shell e da navegação; o padrão visual é o de docs/ui.md.
Protótipo: registration-preview.html (parâmetros view=list, person e asset).
Os dados são ilustrativos. As etapas e o botão salvar ainda não persistem dados.

## Navegação e fluxos

- Pessoas e entidades: moedas, países, pessoas físicas e jurídicas. Endereços e contatos
  ficam no detalhe da pessoa, evitando registros sem identidade associada.
- Ativos: cadastro das cinco famílias, casas de negociação, fontes de preço, preços e eventos.
- Identificadores, listagens e classificação ficam no detalhe do ativo.
- Listas: busca, filtros, paginação, criação e edição conforme permissão.
- Moedas, países, casas e fontes: formulário curto, em uma tela.
- Pessoa: identificação, endereços, contatos e conferência.
- Ativo: identificação, detalhes da família, identificadores/listagens e conferência.
- Preços e eventos: lista global com filtro por ativo e acesso pelo detalhe do ativo.
- Permissões Django por model: view para consulta, add para criação e change para edição.
  Arquivamento de pessoa usa change; exclusão física não faz parte desta proposta.
- A escrita passa pelo handler da slice; moeda, país e papéis de entidades são consultados
  por fachada do módulo. Valores financeiros permanecem Decimal.

## Cenários a validar antes da implementação

- test_registration_pages_require_login — telas exigem autenticação.
- test_registration_write_requires_permission — gravação exige permissão no backend.
- test_currency_and_country_can_be_registered — moeda e país ficam disponíveis para seleção.
- test_entity_person_creates_matching_details — pessoa física grava identidade e detalhe juntos.
- test_entity_company_requires_registration — empresa exige país e número de registro.
- test_entity_kind_cannot_change_after_creation — natureza fica fixa após salvar.
- test_entity_registration_preserves_entered_value — registro preserva o formato informado.
- test_duplicate_entity_registration_is_rejected — país e número repetidos são recusados.
- test_primary_contact_and_address_are_unique_per_type — contato/endereço primário é único por tipo.
- test_asset_creates_exactly_one_matching_family_detail — ativo grava um detalhe da família.
- test_asset_family_cannot_change_after_creation — família fica fixa após salvar.
- test_asset_roles_reject_incompatible_entities — papéis respeitam a natureza da entidade.
- test_cash_asset_currency_matches_asset — caixa compartilha a moeda da identidade do ativo.
- test_cash_asset_is_unique_per_currency — não há dois ativos caixa para a mesma moeda.
- test_listing_ticker_is_unique_per_venue — ticker é único por casa de negociação.
- test_identifier_type_and_value_are_unique — identificadores duplicados são recusados.
- test_debt_validates_dates_and_positive_minimum_lot — dívida valida vencimento, perpétuo e lote.
- test_fund_validates_parent_and_nonnegative_fees — fundo valida vínculo com pai e taxas.
- test_price_validates_type_source_and_unique_date — preço respeita tipos e unicidade do model.
- test_event_uses_cum_price_and_com_date — evento apresenta Preço COM e Data COM.
- test_repeated_registration_request_creates_once — repetir a chave de idempotência não duplica.
- test_invalid_form_keeps_values_and_shows_field_errors — recusa preserva dados e sinaliza o campo.
- test_registration_lists_filter_and_paginate — busca e filtros funcionam com paginação.
- test_registration_layout_supports_both_themes_and_mobile — telas operam nos dois temas e no celular.

Implementação será dividida em slices por caso de uso, começando por moedas e países,
depois entidades e por fim ativos e seus vínculos.
