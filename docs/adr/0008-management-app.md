# 0008: Este serviço é o app de gestão da arquitetura Glina e pode ser vendido sozinho

Status: aceito (26/11/2026)

## Contexto
A arquitetura Glina ([desenho](../glina-architecture.svg)) tem três peças, cada uma num repositório:

| Peça | Repositório | Onde roda |
|---|---|---|
| API (porteiro) | `maud-glina-api` | AWS, conta da Maud |
| App de passivo | `maud-glina-liability` | Maud, dentro de casa |
| App de gestão | `maud-glina-management` (este) | Maud, dentro de casa |

O app de gestão pode ser vendido sozinho. Quem comprar não leva o controle de passivo junto, então a gestão não pode depender dele.

## Decisão
- Este serviço **sabe o que existe e quanto vale**. Não conhece cliente.
- Tem API, Backend, Worker e PostgreSQL próprios, no padrão do boilerplate (ADRs 0001 a 0007).
- **Não sabe que o app de passivo existe.** Nunca chama o passivo. Só o passivo chama a gestão, e só para ler.
- **A API é só de leitura e interna:** fechamento por apólice, data e versão; total conferido; pendências.
- **Bancos separados, nenhuma tabela em comum.** Nenhum banco tem rota de fora.
- A gestão confere a posição de cada apólice com a custódia e publica o total conferido. Só o que bateu conta.
- Todo fechamento tem apólice, data, versão e status: preliminar (com pendências nomeadas), oficial, retificado (versão nova, com motivo e delta).
- Reprocessar gera versão nova; a antiga fica gravada. Versão publicada nunca é editada.
- Falta de informação sai como preliminar, nunca como estimativa escondida.

## Consequências
- Nada neste repositório pode citar o app de passivo no código: nem nome, nem endereço, nem tabela.
- O que a gestão publica tem de ser suficiente para um leitor trabalhar sozinho (fechamento, versão, total conferido, pendências), porque ela não avisa ninguém.
- Dois apps para rodar, cada um com o seu banco e o seu backup.
