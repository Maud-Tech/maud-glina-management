# Telas do app de gestão

> Como as telas são feitas e como devem parecer. Decisão em [ADR 0010](adr/0010-web-screens-white-label.md).
> Protótipos de referência (abra no navegador): cadastro [`ui/asset-form.html`](ui/asset-form.html) e painel [`ui/dashboard.html`](ui/dashboard.html). As imagens (`*-dark.png`, `*-light.png`) ficam ao lado.

**Situação:** a casca, a Personalização, os cadastros de `entities` e `assets` e as telas de
`products` existem. Produtos usam detalhe com abas (`.tabs`), números grandes (`.stats`),
etiqueta de status (`.tag`), linha do tempo do histórico (`.timeline`) e confirmação em
`<dialog class="confirm">` aberta por `data-dialog` (protótipo `ui/products-preview.html`).
Cada cadastro separa listagem de formulário: Novo abre a criação; Abrir cadastro exibe
o detalhe/edição; salvar, cancelar e voltar apontam para a lista do respectivo cadastro.
Listas têm busca, filtros e paginação. Endereços/contatos e vínculos de ativos também
são acessíveis no detalhe do registro pai. Consulta exige `view`, criação `add`,
edição `change`; quem só consulta abre o formulário desabilitado.

## 1. O que é

O app é **white label**: cada gestora tem a sua instalação, com o seu nome, logotipo e cor. **Toda a operação é feita por tela**: cadastros, conferência, fechamentos, pendências e a própria personalização. O admin do Django é só leitura.

## 2. Princípios visuais

O estilo vem de [revertai.com.br](https://revertai.com.br/): sóbrio, tipográfico, com muito espaço.

| Faça | Não faça |
|---|---|
| Separar seções com filete fino (1px) | Card com sombra, brilho ou gradiente em volta de tudo |
| Título grosso, uma palavra destacada num bloco de cor | Vários destaques coloridos na mesma tela |
| Rótulo pequeno em caixa alta e espaçado para agrupar | Ícone dentro de quadradinho colorido em todo item |
| Item de menu atual marcado por filete na esquerda | Item de menu em pílula com gradiente |
| Etapas e abas numeradas em pílula (01, 02, 03) | Abas de navegador ou carrossel |
| Erro no próprio campo, dizendo o que fazer | Erro só num alerta no topo |
| Texto corrido fino (Jost 300), números e valores em 400 | Negrito no meio da frase |

**Um destaque por tela.** A cor da gestora aparece no botão principal, na etapa atual, no filete do menu e no destaque do título. O resto é neutro.

## 3. Cores e temas

A gestora escolhe **uma cor** (`--brand`). Tudo o mais é fixo ou derivado dela por CSS (`color-mix`).

| Variável | Escuro | Claro | Uso |
|---|---|---|---|
| `--bg` | `#031011` | `#ffffff` | Fundo |
| `--text` | `#f1ede4` | `#0a161a` | Texto principal |
| `--muted` | `#8fa3a4` | `#5b6d70` | Texto de apoio, rótulos |
| `--faint` | `#557072` | `#93a3a5` | Placeholder, rótulo de seção |
| `--line` / `--line-2` | verde-cinza a 16% / 30% | `#e4eaeb` / `#cdd7d8` | Filetes e bordas de campo |
| `--brand` | da gestora (padrão `#22bec6`) | igual | Destaque |
| `--ok` / `--err` | `#5fd3a7` / `#ff8b7e` | `#138a63` / `#c2412f` | Conferência que passou / erro |

- **Tema:** escuro e claro, cada usuário escolhe.
- **Contraste:** ao salvar a cor na personalização, o app recusa cor que deixa o texto do botão ilegível nos dois temas.

## 4. Tipografia

- **Fonte Jost**, servida pelo próprio app (sem CDN).
- **Título da tela:** 56px, peso 700, com a palavra-chave em `<mark>`. O bloco do destaque tem a altura das letras e não invade a linha de cima quando o título quebra.
- **Logotipo da gestora:** 56px de altura, até 180px de largura, na proporção da imagem (sem o quadrado da cor). Sem logotipo, as iniciais no quadrado da cor.
- **Título de seção:** 19px, peso 500.
- **Texto:** 15px, peso 300. Valores e conteúdo de campo em 400.
- **Rótulo de grupo:** 11px, caixa alta, espaçamento 0,28em.

## 5. Componentes

| Componente | Como é |
|---|---|
| Menu lateral | Marca da gestora no topo, grupos com rótulo em caixa alta, item atual com filete na esquerda, data-base no rodapé |
| Barra de cima | Caminho (Ativos / Novo ativo), busca com filete embaixo, usuário |
| Cabeçalho da tela | Título com destaque e uma linha de explicação |
| Etapas | Pílulas numeradas; a atual preenchida com a cor da gestora |
| Seção de formulário | Filete em cima; à esquerda o nome e a explicação, à direita os campos em duas colunas |
| Campo | Rótulo em cima, campo de 46px com borda fina, mensagem embaixo (ajuda, erro ou conferência) |
| Escolha única pequena | Pílulas com ícone (ex.: família do ativo) |
| Liga e desliga | Chave; ligada na cor da gestora |
| Número grande | Rótulo em caixa alta, número em peso 300, variação colorida embaixo; números lado a lado separados por filete vertical, sem card |
| Lista numerada | Itens com número pequeno (01, 02), nome, explicação e o valor à direita, separados por filete |
| Pendência | Filete vertical na cor do tipo, rótulo em caixa alta, o que falta e o que segura |
| Lista de valores | Etiquetas (ex.: ISIN, CUSIP), com "adicionar" tracejado |
| Anexos | Área tracejada para arrastar arquivo e lista dos enviados |
| Resumo | Coluna à direita com filete vertical, os valores principais e as conferências |
| Barra de ações | Rodapé fixo: etapa à esquerda; Cancelar, Voltar e o botão principal à direita |

## 6. Formulário de cadastro

Preços usam apenas os tipos MKT, MD e CURVE (curva), com um registro por ativo,
data e tipo. Não há campo de fonte nem cadastro de fornecedores de preço.

Casas de negociação e Listagens compartilham o grupo recolhível **Negociação**
do menu lateral, com telas independentes e permissões próprias.

Identificadores (ISIN, CUSIP, etc.) ficam numa seção opcional dentro do formulário
do ativo. São salvos junto dele e não possuem item próprio no menu lateral.

Os grupos do menu lateral são expansíveis/recolhíveis por clique ou teclado
(`details/summary`). A preferência fica no navegador por usuário e por grupo.
Ao navegar, o grupo da tela atual abre automaticamente. Sem JavaScript ou storage,
o controle nativo continua disponível; as permissões seguem sendo conferidas no servidor.

- **Uma etapa por grupo de dados.** Cadastro curto cabe numa tela só, sem etapas.
- **Conferência ao vivo:** a regra do `domain/` roda enquanto a pessoa preenche (htmx) e o erro aparece no campo. A slice confere de novo ao salvar.
- **Resumo sempre à vista**, com o que vai ser gravado.
- **Escolha que muda o formulário** (ex.: família do ativo) vem primeiro e não muda depois de salvo.

## 7. Arquivos enviados

- **Onde ficam:** no storage padrão do Django. Hoje é a pasta `media/` (fora do git, volume no Docker); em produção, um storage de objetos.
- **Acesso:** abrir um arquivo exige login. Só o logotipo da gestora é público.
- **No upload:** o tipo é conferido pelo conteúdo do arquivo e há tamanho máximo.

## 8. Onde fica cada coisa

| Onde | O quê |
|---|---|
| `src/maud/web/` | A casca: layout, menu, login, tema, CSS, htmx, fonte e ícones |
| `src/maud/modules/branding/` | Identidade da gestora: nome, logotipo, ícone da aba, cor |
| `src/maud/modules/<módulo>/features/<slice>/` | A tela da slice (`page.py` + `page.html`), chamando o mesmo `handler` |
| `src/maud/modules/<módulo>/pages.py` | Uma linha por tela do módulo; o `config/urls.py` inclui este arquivo |
| `docs/ui/` | Protótipos em HTML e as imagens deles |

## 9. Tela nova, passo a passo

1. **Protótipo primeiro:** HTML em `docs/ui/`, no padrão deste documento, e uma imagem (PNG) para o time aprovar antes do código.
2. **Slice:** skill `new-feature`. A tela é mais um jeito de chamar o `handler`, como o endpoint.
3. **Tela:** `page.py` e `page.html` na pasta da slice, com `{% extends "web/base.html" %}` e os componentes do `app.css`. Nada de CSS solto na tela. Uma linha no `pages.py` do módulo (e o `include` no `config/urls.py`, se for a primeira tela do módulo). Referência: `modules/branding/features/update_branding/`.
4. **Menu:** item novo em `src/maud/web/navigation.py`, no grupo certo.
5. **Permissão:** quem pode abrir e quem pode gravar.
