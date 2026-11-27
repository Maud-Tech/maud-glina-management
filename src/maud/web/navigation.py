"""O menu lateral. Tela nova entra aqui, no grupo certo (docs/ui.md, passo 4).

Só aparece o que a pessoa pode abrir; grupo sem item visível some.
"""

from dataclasses import dataclass

from django.http import HttpRequest


@dataclass(frozen=True)
class MenuItem:
    label: str
    url_name: str
    permission: str | None = None


@dataclass(frozen=True)
class MenuGroup:
    label: str
    items: tuple[MenuItem, ...]


MENU = (
    MenuGroup("Carteira", (MenuItem("Painel", "dashboard"),)),
    MenuGroup(
        "Administração",
        (MenuItem("Personalização", "branding_settings", "branding.change_branding"),),
    ),
)


@dataclass(frozen=True)
class VisibleItem:
    label: str
    url_name: str
    active: bool


@dataclass(frozen=True)
class VisibleGroup:
    label: str
    items: tuple[VisibleItem, ...]


def menu_for(request: HttpRequest) -> tuple[VisibleGroup, ...]:
    user = request.user
    current = request.resolver_match.url_name if request.resolver_match else None
    groups = []
    for group in MENU:
        items = tuple(
            VisibleItem(item.label, item.url_name, active=item.url_name == current)
            for item in group.items
            if item.permission is None or user.has_perm(item.permission)
        )
        if items:
            groups.append(VisibleGroup(group.label, items))
    return tuple(groups)
