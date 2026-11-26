"""O operationId do OpenAPI é contrato: não pode depender de onde o arquivo mora."""

from maud.config.api import api


def test_operation_ids_are_module_and_function():
    schema = api.get_openapi_schema()
    ids = {
        operation["operationId"] for path in schema["paths"].values() for operation in path.values()
    }
    assert {"example_post_item", "example_get_items"} <= ids


def test_operation_ids_are_unique():
    schema = api.get_openapi_schema()
    ids = [
        operation["operationId"] for path in schema["paths"].values() for operation in path.values()
    ]
    assert len(ids) == len(set(ids))
