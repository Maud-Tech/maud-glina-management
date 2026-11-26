"""Erros de negócio. A API traduz: NotFound→404, Conflict→409, demais→422 (ver maud.config.api)."""


class DomainError(Exception):
    """Regra de negócio violada. `code` é estável e faz parte do contrato da API."""

    code: str = "domain_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class NotFoundError(DomainError):
    code = "not_found"


class ConflictError(DomainError):
    code = "conflict"
