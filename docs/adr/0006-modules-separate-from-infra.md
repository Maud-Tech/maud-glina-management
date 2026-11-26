# 0006: Módulos de negócio em `modules/`, separados da infraestrutura

Status: aceito (24/11/2026)

## Contexto
Com módulos de negócio lado a lado com `config`, `jobs`, `shared` e `integration`, não dá para ver ao abrir a pasta o que é negócio e o que é encanamento. Isso vale para quem chega no projeto e para a IA decidir onde colocar código novo.

## Decisão
```
src/maud/
  config/  jobs/  shared/  integration/   # infraestrutura: entrypoints, núcleo comum, bordas
  modules/                                 # só negócio
    example/  <módulo>/ ...
```
- `integration` fica **fora** de `modules/`: é a porta para terceiros, não regra de negócio. Ela chama os módulos pelo `api.py`; nenhum módulo chama a integração.
- O `label` de cada app Django é o nome curto do módulo. Tabelas e migrations usam esse nome.
- Não há mais níveis (`core/`, `infra/`...): pasta nova só quando trouxer regra nova.

## Consequências
- Regra prática: regra de negócio nova vai em `src/maud/modules/<módulo>/`.
- Imports ficam mais longos (`from maud.modules.<módulo>.api import ...`); o formatador quebra a linha quando precisa.
