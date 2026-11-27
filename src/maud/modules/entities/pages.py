"""Rotas públicas de tela; cada cadastro possui lista, criação e edição separadas."""

from django.urls import path

from maud.modules.entities.features.list_registrations.page import registration_list
from maud.modules.entities.features.save_registration.page import registration_edit
from maud.modules.entities.registrations import REGISTRY

urlpatterns = []
for resource in REGISTRY:
    prefix = "entities/" + resource + "/"
    urlpatterns.extend(
        [
            path(
                prefix,
                registration_list,
                {"resource": resource},
                name="entities_" + resource + "_list",
            ),
            path(
                prefix + "new/",
                registration_edit,
                {"resource": resource},
                name="entities_" + resource + "_new",
            ),
            path(
                prefix + "<str:pk>/",
                registration_edit,
                {"resource": resource},
                name="entities_" + resource + "_edit",
            ),
        ]
    )
