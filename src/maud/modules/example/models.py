import uuid

from django.db import models
from django.db.models.functions import Lower


class Item(models.Model):
    """Registro de exemplo. Apague o módulo `example` quando o primeiro módulo real existir."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("name"), name="uq_example_item_name_ci"),
        ]

    def __str__(self) -> str:
        return self.name
