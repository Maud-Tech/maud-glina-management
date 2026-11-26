"""Todo nome é em inglês; português só em texto livre (ADR 0003).

Confere nomes de arquivos/pastas e identificadores Python (classes, funções, testes, variáveis,
parâmetros, atributos). Cada nome é quebrado em palavras (`snake_case`, `kebab-case`, `CamelCase`)
e nenhuma palavra pode estar na lista de palavras comuns em português abaixo.

É uma rede de segurança, não um dicionário: pega o erro comum (nome de teste ou variável escrito
em português) e deixa passar palavra que não está na lista. Acentos em nomes o ruff já recusa
(regra PLC2401).

Falso positivo (palavra que também é um nome legítimo em inglês)? Adicione em ALLOWED_WORDS
com um comentário explicando.
"""

import ast
import re
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", ".venv", ".cache", "__pycache__", "node_modules", ".claude"}

# Palavras comuns em português que não são palavras em inglês. Sem acento, porque nome com acento
# já é recusado pelo ruff. Evite incluir palavra que exista em inglês (ex.: "data", "no", "do").
PORTUGUESE_WORDS = frozenset(
    """
    agente agentes antes apolice ativo ativos aviso avisos busca buscar cadastra cadastrado
    cadastrar cadastro calcular cambio casas chave cliente clientes codigo com conta contas
    contexto contrato contratos cota cotas criar da das de deve depois diario dinheiro dos em
    entrega entregue enviado enviar erro erros evento eventos excluir falha falhas fonte
    glossario gravar hora idioma inativo inativos invalido lista listar mensagem menos mesma
    mesmo migracao modelo modulo moeda moedas nao nome nomes nova novo obrigatorio ordem ordens
    pais para parceiro pedido pedidos pelo percentual preco processo quando recusa recusada
    recusado regra remover resposta saldo salvar seguradora sem soma somar tabela taxa titular
    um uma unica usuario usuarios valido validar valor valores verificar
    """.split()  # noqa: SIM905 (em bloco de texto a lista fica legível e fácil de estender)
)

ALLOWED_WORDS: frozenset[str] = frozenset()


def words(name: str) -> list[str]:
    """`test_nomeRepetido-x` -> ["test", "nome", "repetido", "x"]."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    return [w.lower() for w in re.split(r"[^A-Za-z0-9]+", spaced) if w]


def project_paths() -> Iterator[Path]:
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if not SKIP_DIRS & set(relative.parts):
            yield relative


def python_names(source: str) -> Iterator[tuple[int, str]]:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            yield node.lineno, node.name
        elif isinstance(node, ast.arg):
            yield node.lineno, node.arg
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            yield node.lineno, node.id
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
            yield node.lineno, node.attr
        elif isinstance(node, ast.keyword) and node.arg:
            yield node.lineno, node.arg


def portuguese_words_in(name: str) -> list[str]:
    return [w for w in words(name) if w in PORTUGUESE_WORDS and w not in ALLOWED_WORDS]


def test_file_and_folder_names_are_in_english() -> None:
    offenses = [
        f"{path.as_posix()}  (palavra: {', '.join(found)})"
        for path in project_paths()
        if (found := portuguese_words_in(path.stem if path.suffix else path.name))
    ]
    assert not offenses, "Nomes de arquivo/pasta em português (ADR 0003):\n" + "\n".join(offenses)


def test_python_identifiers_are_in_english() -> None:
    offenses = []
    for path in project_paths():
        if path.suffix != ".py":
            continue
        source = (ROOT / path).read_text(encoding="utf-8")
        for line, name in sorted(set(python_names(source))):
            if found := portuguese_words_in(name):
                offenses.append(f"{path.as_posix()}:{line}  {name}  (palavra: {', '.join(found)})")
    assert not offenses, "Nomes em português no código (ADR 0003):\n" + "\n".join(offenses)


def test_detects_portuguese_names() -> None:
    """A própria rede precisa pegar os casos que motivaram a regra."""
    assert portuguese_words_in("test_nome_repetido_e_recusado") == ["nome", "recusado"]
    assert portuguese_words_in("calcularTaxa") == ["calcular", "taxa"]
    assert portuguese_words_in("nova-feature") == ["nova"]
    assert portuguese_words_in("test_duplicate_name_is_rejected_with_409") == []
    assert portuguese_words_in("data_no_do_os") == []
