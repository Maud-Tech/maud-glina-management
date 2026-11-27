# branding: identidade da gestora

Responsável por: nome, cor principal, logotipo e ícone da aba da gestora desta instalação (white label, [ADR 0010](../../../../docs/adr/0010-web-screens-white-label.md)).
Não faz: usuários, permissões, tema claro/escuro (é escolha de cada pessoa, cookie da casca `web/`).

Não depende de nenhum módulo. A casca (`web/`) lê a identidade pelo `api.py`.

## Invariantes
- Uma linha só (`id = 1`, constraint no banco): uma instalação, uma gestora.
- A cor é `#RRGGBB` e tem texto legível em cima (escuro ou branco, contraste mínimo de 4,5:1). A regra está em `domain/brand.py` e é repetida só para a prévia em `web/static/web/app.js`.
- Imagem é conferida pelo conteúdo (Pillow), até 2 MB: logotipo PNG, JPG ou WEBP; ícone PNG ou ICO. O arquivo é gravado com nome novo e a extensão do formato real.
- Imagem trocada ou removida é apagada do storage depois do commit.
- Logotipo e ícone são públicos (aparecem na tela de entrar); são servidos pelo storage, nunca por caminho montado à mão.
- Escrita só pela slice `update_branding`; o admin é somente leitura.

## Fachada (api.py)
- `current_branding() -> BrandingView`: nome (pode ser vazio), `wordmark_name` (o nome; sem nome e sem logotipo, o padrão), iniciais, cor, cor do texto em cima, se tem logotipo e ícone, versão (para a URL das imagens). Sem cadastro, devolve a identidade padrão.

## Slices
- `get_branding`: lê a identidade (ou a padrão).
- `update_branding`: tela de Personalização (`/settings/branding/`, permissão `branding.change_branding`) e o handler que grava.
- `serve_branding_image`: entrega logotipo e ícone (`/branding/logo`, `/branding/favicon`), público.

## domain/
- `brand.py`: nome (opcional, até 120; o logotipo pode já trazer o nome), cor (formato e contraste), iniciais.
