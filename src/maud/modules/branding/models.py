"""Identidade da gestora desta instalação. Só este módulo escreve nestas tabelas."""

import uuid
from pathlib import PurePath

from django.db import models
from django.db.models import Q


def branding_upload_path(instance: "Branding", filename: str) -> str:
    """Nome novo e imprevisível para cada imagem; a extensão vem do formato conferido."""
    return f"branding/{uuid.uuid4().hex}{PurePath(filename).suffix.lower()}"


class Branding(models.Model):
    """Uma linha só (id = 1): cada instalação é de uma gestora (ADR 0010)."""

    SINGLETON_ID = 1

    id = models.PositiveSmallIntegerField(primary_key=True, default=SINGLETON_ID, editable=False)
    name = models.CharField(max_length=120)
    brand_color = models.CharField(max_length=7)
    logo = models.ImageField(upload_to=branding_upload_path, blank=True)
    favicon = models.ImageField(upload_to=branding_upload_path, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "identidade da gestora"
        constraints = [
            models.CheckConstraint(condition=Q(id=1), name="ck_branding_single_row"),
        ]

    def __str__(self) -> str:
        return self.name
