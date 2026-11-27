# Telas de produtos: proposta para aprovação

> **Aprovado em 27/11/2026 (Victor) e implementado.** Respostas às perguntas do fim: 1) grupo
> próprio **Produtos** no menu; 2) permissões padrão (publicar e expirar com `change`);
> 3) regulamento em 4 etapas; 4) limites de emissor e ativo pelos cadastros existentes;
> 5) produto expirado só pode ser encerrado (renovar continua em aberto com o time).
> Ajuste pedido na aprovação: a visão geral não mostra o bloco "Próxima versão"; o que muda na
> versão seguinte aparece marcado no perfil.

O escopo são as telas para o módulo `products`, que já tem models e as 14 slices. Nenhum banco muda.
O protótipo é o `products-preview.html` (abra servindo a raiz do repositório, por exemplo
`python -m http.server 8091`, e acesse `/docs/ui/products-preview.html`). O padrão visual segue o `docs/ui.md` e
usa o `app.css` do app. Os dados são ilustrativos e nada é gravado.

Imagens: `products-list.png`, `products-new.png`, `products-detail.png`, `products-history.png`,
`products-mandate.png`, `products-mandate-limits.png` e `products-policy.png`.

## Navegação

- Grupo novo **Produtos** no menu, com o item **Cadastro de produtos**. A apólice, o regulamento e os documentos
  ficam dentro do produto: são 1:1 e não existem sem ele, então não ganham item próprio.
- A lista fica em `/products/`. "Novo produto" abre `/products/new/`, e "Abrir produto" abre o detalhe em
  `/products/<id>/`, com cinco abas.

| Tela | Parâmetro no protótipo | Slice |
|---|---|---|
| Lista com busca, filtro de status e paginação | `?view=list` | `list_products` |
| Produto novo (uma tela, sem etapas) | `?view=new` | `create_product` |
| Editar produto | `?view=edit` | `update_product` |
| Detalhe · 01 Visão geral | `?view=detail` (`&product=draft` ou `expired` para os outros casos) | `get_product` |
| Detalhe · 02 Regulamento: versões | `&tab=mandate` | `get_product`, `start_mandate_draft` |
| Detalhe · 03 Apólice, com botão de expirar | `&tab=policy` | `expire_policy` |
| Detalhe · 04 Documentos: enviar e arquivar | `&tab=documents` | `attach_product_document`, `archive_product_document` |
| Detalhe · 05 Histórico com filtro | `&tab=history` | `list_product_history` |
| Ativar, inativar, encerrar (confirmação) | botões do detalhe | `change_product_status` |
| Apólice nova e editar apólice | `?view=policy` e `?view=policy&mode=edit` | `register_policy`, `update_policy` |
| Regulamento em rascunho, em 4 etapas | `?view=mandate&step=profile, flows, limits, publish` | `update_mandate_draft`, `publish_mandate` |

## Regras que a tela mostra (quem decide é a slice)

- **Ativar.** O botão aparece no rascunho e no inativo. Se faltar apólice vigente ou regulamento publicado em
  vigor, a confirmação diz o que falta. Na visão geral do rascunho, a lista "Antes de ativar" leva direto a cada
  pendência.
- **Código e moeda base** ficam desabilitados fora do rascunho, com o motivo embaixo do campo.
- **Expirar a apólice** tem confirmação em vermelho, que avisa que o produto expira junto e depois só pode ser
  encerrado. No produto expirado só sobra o botão "Encerrar".
- **Encerrar** é definitivo e a confirmação diz isso.
- **Regulamento.**
  - Versão publicada é só leitura. "Nova versão" abre um rascunho copiado da última publicada.
  - Cada campo diferente da versão anterior mostra o valor antigo riscado ("Na v2: ~~2~~").
  - O resumo ao lado lista o que falta para publicar.
  - Limite de classe fora das classes elegíveis aparece com erro no próprio campo.
- **Publicar.**
  - A vigência precisa ser depois da versão anterior, e o motivo é obrigatório da v2 em diante.
  - A etapa 04 mostra o que muda em relação à versão anterior.
  - A confirmação lembra que a versão vale para todos os clientes, inclusive quem já comprou.
- **Documentos.** Só PDF, até 20 MB. Documento não é apagado, é arquivado, e o arquivado aparece apagado na lista.
- **Histórico.** Mostra o antes e o depois de cada campo, quem alterou, quando e o motivo, misturando produto,
  apólice, documentos, regulamento e limites. O filtro escolhe o tipo.
- **Motivo opcional** em editar, inativar, encerrar, expirar e arquivar. Ele vai para o histórico.

## Permissões

Seguem o padrão Django por model, como nos outros cadastros:
- consultar exige `products.view_product`;
- criar exige `add_product`;
- editar, mudar status e anexar documento exigem `change_product`;
- cadastrar e editar a apólice exigem `add_policy` e `change_policy`;
- editar e publicar o regulamento exigem `change_mandate`.

Quem só consulta abre os formulários desabilitados e não vê os botões de ação. Publicar o regulamento e expirar a
apólice podem ganhar permissão própria; veja a pergunta 2.

## Cenários a validar antes da implementação

- test_product_pages_require_login: as telas exigem login.
- test_product_write_requires_permission: gravar exige permissão no backend, não só esconder o botão.
- test_product_list_filters_by_status_and_search_and_paginates
- test_new_product_starts_as_draft_in_usd
- test_code_and_currency_are_locked_after_draft: na edição, o campo vem desabilitado e o servidor recusa.
- test_activation_shows_what_is_missing: sem apólice vigente ou regulamento em vigor, a confirmação lista o que falta.
- test_expire_policy_asks_confirmation_and_expires_product
- test_expired_product_only_offers_close
- test_new_mandate_version_copies_last_published
- test_mandate_draft_marks_changes_against_previous_version
- test_limit_outside_eligible_classes_shows_field_error
- test_publish_requires_reason_from_second_version
- test_published_mandate_is_read_only
- test_document_upload_accepts_pdf_only_up_to_20mb
- test_archived_document_stays_listed_as_archived
- test_history_shows_before_after_author_and_reason
- test_invalid_form_keeps_values_and_shows_field_errors
- test_product_pages_support_both_themes_and_mobile

## Perguntas para aprovar junto

1. Menu: o grupo próprio **Produtos** fica entre Carteira e Pessoas e entidades? A alternativa é um item dentro de
   Carteira.
2. Publicar o regulamento e expirar a apólice ficam com quem tem `change` ou ganham permissão própria (por exemplo,
   só o comitê publica)?
3. O regulamento tem 4 etapas (perfil e retorno, entrada e saída, limites, publicação). Prefere tudo numa tela só?
4. Os limites de emissor e de ativo usam a busca de entidades e de ativos já cadastrados. Ok?
5. Continua em aberto: produto expirado pode ser renovado? A tela hoje só oferece "Encerrar".

Depois da aprovação, as telas entram por slice: lista e produto primeiro, depois apólice, regulamento, documentos
e histórico.
