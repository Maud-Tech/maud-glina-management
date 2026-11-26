from django.apps import AppConfig
from django.db.models.signals import post_migrate


class SharedConfig(AppConfig):
    name = "maud.shared"
    label = "shared"
    verbose_name = "Infraestrutura compartilhada"

    def ready(self) -> None:
        from maud.shared.db import apply_protections

        # A cada `migrate` (e no banco de teste): função e triggers dos ledgers.
        post_migrate.connect(apply_protections, sender=self, dispatch_uid="maud.shared.db")
