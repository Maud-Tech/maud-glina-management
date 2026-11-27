# web: a casca das telas

Entrypoint das telas (como o `config/` é da API), [ADR 0010](../../../docs/adr/0010-web-screens-white-label.md). Padrão visual: [`docs/ui.md`](../../../docs/ui.md).
Não tem model nem regra de negócio. Lê dos módulos só pelo `api.py` deles.

## Conteúdo
- `templates/web/base.html`: layout de toda tela (menu, barra de cima, avisos). Tela de slice faz `{% extends "web/base.html" %}` e preenche `title`, `crumb` e `content`.
- `templates/web/_sidebar.html`, `_wordmark.html`: menu e marca da gestora.
- `templates/web/login.html`, `dashboard.html`: entrar e painel.
- `navigation.py`: o menu. Tela nova entra aqui, no grupo certo, com a permissão de quem pode abrir.
- `context_processors.py`: toda tela recebe `shell` (identidade da gestora, tema, menu).
- `views.py`, `urls.py`: entrar, sair, painel.
- `static/web/app.css`: todos os componentes. Tela não traz CSS próprio.
- `static/web/app.js`: troca de tema e prévia da cor.
- `static/web/vendor/`: htmx 2.0.4, fonte Jost e ícones Tabler 3.19.0, com as licenças. Nada vem de CDN.

## Invariantes
- Tela grava só pelo handler da slice, nunca direto no model.
- Tema (`dark`/`light`) é escolha de cada pessoa, num cookie; valor desconhecido vira `dark`.
- Toda tela exige login, menos entrar e as imagens da gestora.
- Menu só mostra o que a pessoa pode abrir.

## Onde mora a tela de uma slice
`modules/<módulo>/features/<slice>/page.py` + `page.html` (template `modules/<módulo>/features/<slice>/page.html`) e uma linha no `pages.py` do módulo. O `config/urls.py` inclui o `pages.py` de cada módulo que tem tela.
