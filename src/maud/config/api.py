"""Monta a API pública: um router por módulo, autenticação e tradução de erros de domínio."""

from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI
from ninja.operation import Operation

from maud.modules.example import routes as example_routes
from maud.shared.errors import ConflictError, DomainError, NotFoundError
from maud.shared.http import ApiKey


class MaudApi(NinjaAPI):
    def get_openapi_operation_id(self, operation: Operation) -> str:
        """`<módulo>_<função>`, ex.: `example_post_item`.

        O padrão do Ninja usa o caminho Python inteiro, e aí mover uma pasta mudaria o contrato
        (clientes gerados por parceiros quebrariam). Este id só muda se mudar o módulo ou a função.
        """
        parts = operation.view_func.__module__.split(".")
        module = parts[parts.index("modules") + 1] if "modules" in parts else parts[1]
        return f"{module}_{operation.view_func.__name__}"


api = MaudApi(
    title="Maud · Glina · Gestão",
    version="1",
    description=(
        "App de gestão da arquitetura Glina: sabe o que existe e quanto vale. Não conhece cliente."
    ),
    urls_namespace="api-v1",
    auth=ApiKey(),
)

api.add_router("/example", example_routes.router)


def _error(request: HttpRequest, exc: DomainError, status: int) -> HttpResponse:
    return api.create_response(request, {"code": exc.code, "message": exc.message}, status=status)


@api.exception_handler(NotFoundError)
def _not_found(request: HttpRequest, exc: NotFoundError) -> HttpResponse:
    return _error(request, exc, 404)


@api.exception_handler(ConflictError)
def _conflict(request: HttpRequest, exc: ConflictError) -> HttpResponse:
    return _error(request, exc, 409)


@api.exception_handler(DomainError)
def _domain(request: HttpRequest, exc: DomainError) -> HttpResponse:
    return _error(request, exc, 422)
