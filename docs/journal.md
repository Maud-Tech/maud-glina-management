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

## 2026-11-26 · assets · cadastro de dívida simplificado
- **O que mudou:** removidos valor de face original, frequência de cupom e spread em pontos-base do cadastro de dívida.
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
