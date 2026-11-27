# Diário do projeto

Uma entrada por entrega (uma slice, um ajuste, uma decisão pequena). **Mais nova em cima.** Quem escreve é quem entregou, normalmente pedindo à IA no fim da tarefa.
Decisão que vale para o projeto inteiro vira ADR em `docs/adr/`; aqui fica só o link.

Modelo:

```
## AAAA-MM-DD · <módulo> · <o que foi entregue, em poucas palavras>
- **O que mudou:** 1–2 linhas, em linguagem de negócio.
- **Por quê:** o motivo ou o pedido de origem.
- **Pendente / atenção:** o que ficou para depois, riscos, quem precisa olhar.
- **Autor:** nome (+ IA, se usou)
```

---

## 2026-11-27 · shared · ledger aceita TRUNCATE só no banco de teste
- **O que mudou:** o trigger dos ledgers (`maud_forbid_mutation`) deixa passar o TRUNCATE quando a chave `maud.allow_test_truncate` está ligada, e só o `conftest.py` da raiz a liga, no banco de teste. UPDATE e DELETE continuam recusados em qualquer banco. Teste novo em `shared/tests/test_db.py`.
- **Por quê:** os primeiros ledgers de verdade (`ProductChange`, `MandateChange`) quebraram os testes de transação real (outbox e concorrência): o Django limpa o banco com TRUNCATE entre eles e o trigger recusava.
- **Pendente / atenção:** mexe em `shared/` e no `conftest.py` da raiz: avisar o time. Quem já tem banco local recria a função no próximo `migrate` (post_migrate).
- **Autor:** Victor (+ IA)

## 2026-11-27 · projeto · banco local em 127.0.0.1, não localhost
- **O que mudou:** `POSTGRES_HOST` do `.env.example` (e o padrão do `settings.py`) passou de `localhost` para `127.0.0.1`.
- **Por quê:** o banco só escuta no IPv4 da própria máquina. No Windows com Docker Desktop, `localhost` tenta o IPv6 (`::1`) primeiro e a conexão fica pendurada: os testes travavam já no primeiro teste com banco. Com `127.0.0.1`, os 126 testes rodaram contra Postgres em cerca de 1 minuto (primeira rodada com banco real, pendente desde a entrega das telas).
- **Pendente / atenção:** quem já tem `.env` com `POSTGRES_HOST=localhost` e usa Windows deve trocar para `127.0.0.1`. O CI (Linux) não é afetado.
- **Autor:** Victor (+ IA)

## 2026-11-27 · projeto · banco local em 127.0.0.1, não localhost
- **O que mudou:** `POSTGRES_HOST` do `.env.example` (e o padrão do `settings.py`) passou de `localhost` para `127.0.0.1`.
- **Por quê:** o banco só escuta no IPv4 da própria máquina. No Windows com Docker Desktop, `localhost` tenta o IPv6 (`::1`) primeiro e a conexão fica pendurada: os testes travavam já no primeiro teste com banco. Com `127.0.0.1`, os 126 testes rodaram contra Postgres em cerca de 1 minuto (primeira rodada com banco real, pendente desde a entrega das telas).
- **Pendente / atenção:** quem já tem `.env` com `POSTGRES_HOST=localhost` e usa Windows deve trocar para `127.0.0.1`. O CI (Linux) não é afetado.
- **Autor:** Victor (+ IA)

## 2026-11-27 · assets · preços sem cadastro de fontes
- **O que mudou:** removidos o model PriceSource, a FK AssetPrice.source e o cadastro
  de fontes no menu, formulários e admin. Preço passa a ser único por ativo/data/tipo,
  preservando os tipos MKT, MD e CURVE.
- **Por quê:** iniciar a precificação como no MCore, sem distinção por fornecedor.
- **Testes:** cenários de aceitação existentes atualizados com autorização explícita
  do usuário no chat: remoção do cadastro de fontes e criação de preço sem source.
- **Pendente / atenção:** humano deve gerar/aplicar migration para excluir a FK e a
  tabela e substituir a constraint. Banco local conferido antes da alteração: zero
  fontes e zero preços; outros ambientes devem conferir duplicatas antes da migration.
- **Autor:** Felipe Linhares + Codex

## 2026-11-27 · web · menu de negociação
- **O que mudou:** Casas de negociação e Listagens ficam juntas no grupo recolhível
  Negociação, com suas próprias telas e permissões.
- **Por quê:** reunir os cadastros relacionados à negociação no mesmo menu.
- **Pendente / atenção:** sem mudança de model ou migration.
- **Autor:** Felipe Linhares + Codex

## 2026-11-27 · assets · identificadores dentro do ativo
- **O que mudou:** formulário do ativo passa a incluir identificadores opcionais,
  com múltiplos itens, edição e remoção. Item independente sai do menu lateral
  e dos links de vínculos no detalhe; gravação é atômica com o ativo.
- **Por quê:** manter a identificação do ativo no mesmo fluxo de cadastro.
- **Pendente / atenção:** sem mudança de model ou migration; permissões específicas
  e unicidade de códigos/principais continuam validadas no servidor.
- **Autor:** Felipe Linhares + Codex

## 2026-11-27 · web · grupos do menu recolhíveis
- **O que mudou:** grupos do menu abrem e fecham independentemente, com indicador,
  suporte nativo a teclado e preferência salva no navegador por usuário.
  O grupo da tela atual abre automaticamente ao navegar.
- **Por quê:** reduzir a altura do menu e facilitar a navegação entre cadastros.
- **Pendente / atenção:** nenhuma alteração de permissão, model ou migration.
- **Autor:** Felipe Linhares + Codex

## 2026-11-27 · entities · cadastro conjunto com vínculos opcionais
- **O que mudou:** casas decimais sai do formulário de moeda (default 2); setor de PJ
  vira lista fechada dos 12 setores acordados. Pessoa física/jurídica permite adicionar,
  editar e remover endereços e contatos na mesma tela, com gravação atômica.
- **Por quê:** simplificar o cadastro sem obrigar o preenchimento de endereço/contato.
  Item vazio é ignorado; item iniciado deve ter os campos necessários válidos.
- **Pendente / atenção:** sem alteração de models/migrations. Permissões dos vínculos
  continuam sendo conferidas; exclusão inline exige permissão de exclusão do item.
- **Autor:** Felipe Linhares + Codex

## 2026-11-27 · entities, assets · telas de cadastro e listas independentes
- **O que mudou:** listagem, criação e edição para moedas, países, pessoas, endereços,
  contatos, ativos das cinco famílias, casas, fontes, identificadores, listagens,
  classificações, preços e eventos. Salvar/cancelar retorna à lista do próprio cadastro.
- **Por quê:** disponibilizar os models já acordados pela operação, com navegação
  inspirada no MCore e padrão visual white label do Glina; protótipo aprovado no chat.
- **Pendente / atenção:** sem alteração de models nem migrations. Banco local precisa
  estar preparado pelo humano conforme ADR 0009. Revisar a nova fachada de consultas
  de entities e as permissões por cadastro com o time. Cadastros não publicam fatos externos.
- **Autor:** Felipe Linhares + Codex

## 2026-11-27 · projeto, web, branding · portas no .env, logotipo maior, nome opcional
- **O que mudou:** o `docker-compose.yml` não tem mais porta escrita: Postgres e API escutam nas portas do `.env` (`POSTGRES_PORT`, `API_PORT`), iguais dentro e fora do container; usuário, senha e banco também vêm do `.env`. API passou para a porta 8080. O banco só aceita conexão da própria máquina. Na tela: logotipo na proporção da imagem (56px de altura), destaque do título sem invadir a linha de cima, nome da gestora opcional (só o logotipo, ou o nome padrão se também não houver logotipo).
- **Por quê:** vai rodar na máquina que já tem mcore (5433) e fidccopobras (5431); ajustes pedidos pelo Walter ao ver as telas rodando.
- **Pendente / atenção:** `.env` de quem já tinha precisa de `API_PORT=8080`. No servidor, colocar o nome ou IP de acesso em `DJANGO_ALLOWED_HOSTS` e, se o acesso for por https via proxy, o endereço em `DJANGO_CSRF_TRUSTED_ORIGINS` (variável nova).
- **Autor:** Walter (+ IA)

## 2026-11-26 · web, branding · casca das telas e Personalização
- **O que mudou:** criada a casca das telas (`src/maud/web/`): layout do protótipo aprovado, menu por permissão, entrar e sair, painel com os primeiros passos, tema claro e escuro por pessoa. Criado o módulo `branding` com a tela de Personalização (nome, cor, logotipo, ícone da aba), que muda todas as telas, inclusive a de entrar. Arquivos enviados vão para o storage padrão (pasta `media/`, volume no Docker). htmx, fonte Jost e ícones servidos pelo próprio app. Pacote novo: `pillow`.
- **Por quê:** ADR 0010: app white label, toda a operação por tela.
- **Pendente / atenção:** **gerar e aplicar a migration do `branding`** (`makemigrations branding` + `migrate`) antes de abrir as telas. Testes com banco não rodaram na máquina de quem entregou (sem Postgres); conferir no CI. Limites escolhidos sem combinar: imagem até 2 MB, contraste mínimo 4,5:1 (padrão WCAG AA). Painel ainda sem números: entram com apólices.
- **Autor:** Walter (+ IA)

## 2026-11-26 · projeto · telas white label: decisão, padrão visual e protótipo
- **O que mudou:** decidido que o app é white label, uma instalação por gestora, com toda a operação por tela em Django + htmx ([ADR 0010](adr/0010-web-screens-white-label.md)). Padrão visual em `docs/ui.md`; protótipos do cadastro de ativo (`docs/ui/asset-form.html`, aprovado) e do painel (`docs/ui/dashboard.html`).
- **Por quê:** pedido do Walter: gestoras vão operar as apólices pelo app, com o logotipo e as cores delas, e todo cadastro tem de ser feito pela tela.
- **Pendente / atenção:** a casca (`src/maud/web/`), o módulo `branding` e o storage (`media/`) ainda não existem. As telas de cadastro dependem das slices de `entities` e `assets`. Escolha da biblioteca de gráficos fica para a primeira tela com gráfico.
- **Autor:** Walter (+ IA)

## 2026-11-26 · projeto · whitenoise serve os arquivos estáticos
- **O que mudou:** o `whitenoise` (middleware logo depois do `SecurityMiddleware`) serve o `staticfiles/` que o `collectstatic` gera no build, comprimido. O admin abre com CSS em produção, sem nginx.
- **Por quê:** o gunicorn não serve arquivo estático.
- **Pendente / atenção:** armazenamento `CompressedStaticFilesStorage`, sem manifesto (o com manifesto quebra página que usa `{% static %}` quando o `collectstatic` não rodou, como nos testes).
- **Autor:** Walter (+ IA)

## 2026-11-26 · projeto · build leva as migrations e roda migrate e collectstatic
- **O que mudou:** a imagem leva as migrations da pasta do projeto (fora do git) e o build falha se algum model mudou sem migration gerada. O `collectstatic` roda no build. Novo serviço `migrate` no `docker-compose.yml`, que aplica as migrations antes da API e do Worker. Novo `.dockerignore`: `.env`, `.git` e `.venv` não entram mais na imagem.
- **Por quê:** cada ambiente tem o próprio banco e as próprias migrations; a imagem precisa levar exatamente as da pasta de quem faz o build, para o histórico do banco não se perder quando um model muda.
- **Pendente / atenção:** no servidor, o build é sempre na mesma pasta (clone novo não tem as migrations já aplicadas no banco de lá). O admin em produção precisa de quem sirva o `staticfiles/` (gunicorn não serve). Build não testado na máquina de quem entregou (sem Docker).
- **Autor:** Walter (+ IA)

## 2026-11-26 · projeto · migrations fora do git
- **O que mudou:** migration não vai mais para o git. O `.gitignore` ignora os arquivos de `migrations/` (menos o `__init__.py`); o hook `pre-commit`, o `scripts/check.py` e o CI recusam migration; as que estavam no repositório saíram do git. Os testes montam as tabelas direto dos models. A proteção dos ledgers saiu da migration 0002 e passou para o `post_migrate`, com `@append_only` no model. O hook `pre-push` ganhou permissão de execução (sem ela o git o ignorava).
- **Por quê:** combinado do time: migration nunca sobe, e o agente nunca roda `makemigrations` nem `migrate` ([ADR 0009](adr/0009-migrations-out-of-git.md)).
- **Pendente / atenção:** no próximo `git pull`, as migrations que estavam no git somem da sua pasta; o banco local não muda. Para os hooks rodarem: `git config core.hooksPath .githooks`, uma vez por clone. `pytest` não rodou na máquina de quem entregou (sem Postgres); conferir no CI.
- **Autor:** Walter (+ IA)

## 2026-11-26 · assets · ativo genérico sem código de origem
- **O que mudou:** removido `original_code` do ativo genérico.
- **Por quê:** sem uma origem associada, o código externo ficaria ambíguo entre fornecedores.
- **Pendente / atenção:** `raw_data` permanece para preservar o conteúdo recebido durante a normalização.
- **Autor:** Felipe Linhares (+ IA)

## 2026-11-26 · assets · cadastro de fundos simplificado
- **O que mudou:** removidos início, término, frequência de negociação e lockup do cadastro de fundo; o vínculo com o fundo pai foi preservado.
- **Por quê:** manter no cadastro mestre somente dados próprios do veículo e deixar regras operacionais para aplicação e resgate.
- **Pendente / atenção:** `parent_fund` continua sendo a ligação entre share classes do mesmo fundo.
- **Autor:** Felipe Linhares (+ IA)

## 2026-11-26 · assets · cadastro de equity simplificado
- **O que mudou:** removidos indústria, direito a voto, frequência de dividendos, ativo subjacente, depositary ratio e ações em circulação.
- **Por quê:** manter no MVP somente tipo e setor como detalhes próprios de equity.
- **Pendente / atenção:** relações de recibos depositários e demais dados podem voltar quando houver um caso de uso concreto.
- **Autor:** Felipe Linhares (+ IA)

## 2026-11-26 · assets · cadastro de dívida simplificado
- **O que mudou:** removidos valor de face original, frequência de cupom, spread, indicador de default e valores de emissão e resgate do cadastro de dívida.
- **Por quê:** manter no MVP somente os dados necessários ao uso atual dos instrumentos.
- **Pendente / atenção:** cálculos futuros usarão o padrão fixo de accrual em 252 dias úteis, sem configuração por instrumento.
- **Autor:** Felipe Linhares (+ IA)

## 2026-11-26 · assets · tipos de preço do MVP
- **O que mudou:** preços passaram a aceitar somente `MKT`, `MD` e `CURVE`; o horário intradiário `as_of` foi removido.
- **Por quê:** representar preço de mercado, última cotação disponível sem média ANBIMA e preço de curva para dívida sem marcação.
- **Pendente / atenção:** a escolha automática do tipo de preço será implementada nas futuras slices de precificação.
- **Autor:** Felipe Linhares (+ IA)

## 2026-11-26 · assets · eventos de mercado alinhados à Data COM
- **O que mudou:** eventos passaram a registrar Data COM, liquidação, taxa, valor pago, Preço COM (`cum_price`), fator e estado padronizado.
- **Por quê:** refletir a semântica operacional já utilizada no processamento e evitar o nome incorreto “Preço Ex”.
- **Pendente / atenção:** cálculo de fator, provisionamento e liquidação entrarão em slices próprias.
- **Autor:** Felipe Linhares (+ IA)

## 2026-11-26 · assets · modelo cadastral de ativos offshore
- **O que mudou:** criado o módulo `assets` com identidade, listagens, identificadores, detalhes por família, classificação, preços e eventos.
- **Por quê:** estabelecer o cadastro mestre de ativos que será usado posteriormente por operações, posições e custódia.
- **Pendente / atenção:** slices, endpoints, telas e migrations definitivas serão criados depois; regras que cruzam tabelas serão aplicadas nelas.
- **Autor:** Felipe Linhares (+ IA)

## 2026-11-26 · entities · modelo cadastral de pessoas e empresas
- **O que mudou:** criado o módulo `entities` com moedas, países, identidade central, detalhes de pessoa física e jurídica, endereços e contatos.
- **Por quê:** estabelecer o cadastro mestre referenciado pelo módulo de ativos do app de gestão.
- **Pendente / atenção:** slices, endpoints, telas e migrations definitivas serão criados depois.
- **Autor:** Felipe Linhares (+ IA)

## 2026-11-26 · projeto · app de gestão da arquitetura Glina
- **O que mudou:** repositório criado a partir do `maud-boilerplate` como o "App de gestão" do desenho da arquitetura Glina. Nome, banco (`maud_glina_management`) e portas próprias (API 8002, Postgres 5435); `docs/context.md`, glossário e README escritos a partir do desenho. Nenhum módulo de negócio ainda.
- **Por quê:** a arquitetura fechada com o time tem três repositórios (porteiro, app de passivo, app de gestão). A gestão é separada do passivo desde o começo porque pode ser vendida sozinha ([ADR 0008](adr/0008-management-app.md)).
- **Pendente / atenção:** escolher os nomes em inglês dos termos do glossário; criar o primeiro módulo (skill `new-module`) e depois remover o `example`.
- **Autor:** Walter (+ IA)

## 2026-11-25 · projeto · nomes em inglês e integration sem banco
- **O que mudou:** todo nome passou a ser em inglês: nomes de teste, arquivos de `docs/` (`journal.md`, `architecture.md`, `glossary.md`, `contracts/`, ADRs) e skills (`new-feature`, `new-migration`, `new-module`). Comentários, docs e mensagens continuam em português. A `integration` deixou de ser app Django (sem migrations, models, domain e api vazios).
- **Por quê:** misturar idiomas nos nomes confunde busca, revisão e agentes de IA ([ADR 0003](adr/0003-language.md)). A `integration` só fala com parceiros, não guarda dados.
- **Pendente / atenção:** o `check.py` agora recusa nome com acento (ruff `PLC2401`) e nome com palavras comuns em português (`tests/architecture/test_english_names.py`). Palavra fora da lista passa: revise nomes novos.
- **Autor:** boilerplate (+ IA)

## 2026-11-24 · projeto · criado a partir do maud-boilerplate
- **O que mudou:** estrutura base (monolito modular, `shared/`, `integration/`, `jobs/`, módulo de demonstração `example`), checagens, instruções e skills dos agentes de IA.
- **Por quê:** começar no padrão da Maud, sem reinventar a arquitetura.
- **Pendente / atenção:** seguir o "Primeiros passos" do `README.md` (nome do projeto, `docs/context.md`, glossário, primeiro módulo real e remoção do `example`).
- **Autor:** boilerplate
