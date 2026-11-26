# example: módulo de demonstração

Mostra a forma de um módulo e das duas slices de referência. **Não tem regra de negócio de verdade.**
Copie a forma, não o conteúdo. Apague o módulo (skill `new-module`, seção "Remover o example") quando o primeiro módulo real tiver as próprias slices de referência.

Responsável por: cadastro e consulta de `Item` (nome + ativo/inativo).
Não faz: nada além disso.

## Invariantes
- Nome do item é único, sem diferenciar maiúsculas (constraint no banco + checagem no handler).
- Escrita só pelas slices (validação + evento no outbox). Admin é só leitura.

## Fachada (api.py)
_(vazia: preencher conforme outros módulos precisarem de algo daqui)_

## Slices
- `create_item/`: cadastrar item. **REFERÊNCIA DE COMANDO** (idempotência + outbox + erro de domínio)
- `list_items/`: listar itens com filtros. **REFERÊNCIA DE CONSULTA** (só leitura)

## domain/
- `item.py`: `validate_new_item` (valida o cadastro), `normalize_name` (usada pelo cadastro e pela busca)
