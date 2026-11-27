# 0010: Telas no próprio app, em Django, com a identidade de cada gestora

Status: aceito (26/11/2026)

## Contexto
Além de publicar fechamentos para leitura, o app de gestão vai ser vendido como **white label** para gestoras cuidarem das suas apólices. Toda a operação acontece por tela: cadastros, conferência, fechamentos e pendências. Cada gestora quer o app com o seu logotipo e as suas cores. Os cadastros já começaram pelo módulo `assets` (models, sem tela).

## Decisão
- **Uma instalação por gestora**, com banco próprio (o mesmo do ADR 0008). Nada de várias gestoras no mesmo app.
- **As telas moram neste app, em Django:** páginas montadas no servidor, com **htmx** para trocar só o pedaço da tela que mudou. Nada de front separado.
- **Toda escrita feita pela tela passa pela slice** (o mesmo `handler` que a API usaria). A tela não grava direto no model.
- **A API continua só de leitura e interna** (ADR 0008). A tela não abre API de escrita.
- **Todo cadastro tem tela.** O admin do Django continua só leitura.
- **Login e permissões são do Django.** A tela de personalização é só para administrador.
- **White label:** a gestora troca o nome, o logotipo, o ícone da aba e **uma cor principal**. Os tons, o hover e os temas claro e escuro saem dessa cor. A identidade fica no banco, num módulo próprio (`branding`): trocar a gestora não exige novo build.
- **Padrão visual único, descrito em [`docs/ui.md`](../ui.md):** filetes finos no lugar de caixas, fonte Jost, um destaque de cor por tela, temas escuro e claro. Os protótipos ficam em `docs/ui/`.
- **Arquivos enviados (imagens, anexos) vão para o storage padrão do Django.** Hoje é a pasta `media/` (fora do git, volume no Docker). Em produção vai ser um storage de objetos, como o S3, mudando só o `settings.py`. O código nunca monta caminho de arquivo na mão.
- **Arquivo enviado não é público:** abrir exige login. A exceção é o logotipo da gestora.
- **Nada vem de CDN:** htmx, fonte e ícones são servidos pelo próprio app (whitenoise). Pacotes novos aprovados: `htmx` e `Pillow` (validar imagem).

## Consequências
- Um deploy, um banco e um login por gestora. O app continua vendável sozinho.
- Toda slice de cadastro ganha tela, e o padrão visual precisa ser seguido por todo mundo, inclusive pelos agentes de IA.
- Tela que precisa de interação mais rica que o htmx dá vai ter JavaScript pequeno, servido junto.
- Descartado: front separado em React ou Next. Exigiria API de escrita, um segundo deploy e login por token.
- Descartado: várias gestoras na mesma instalação. Exigiria marcar a gestora em toda tabela e filtrar em toda consulta.
