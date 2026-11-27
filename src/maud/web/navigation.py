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
    # Telas sem item próprio que marcam este item (ex.: "products_" cobre detalhe e formulários)
    covers_prefix: str | None = None

    def is_current(self, current: str | None) -> bool:
        if current is None:
            return False
        return self.url_name == current or (
            self.covers_prefix is not None and current.startswith(self.covers_prefix)
        )


@dataclass(frozen=True)
class MenuGroup:
    label: str
    items: tuple[MenuItem, ...]


MENU = (
    MenuGroup("Carteira", (MenuItem("Painel", "dashboard"),)),
    MenuGroup(
        "Produtos",
        (
            MenuItem(
                "Cadastro de produtos",
                "products_list",
                "products.view_product",
                covers_prefix="products_",
            ),
        ),
    ),
    MenuGroup(
        "Pessoas e entidades",
        (
            MenuItem("Moedas", "entities_currencies_list", "entities.view_currency"),
            MenuItem("Países", "entities_countries_list", "entities.view_country"),
            MenuItem("Pessoas físicas e jurídicas", "entities_people_list", "entities.view_entity"),
            MenuItem("Endereços", "entities_addresses_list", "entities.view_entityaddress"),
            MenuItem("Contatos", "entities_contacts_list", "entities.view_entitycontact"),
        ),
    ),
    MenuGroup(
        "Ativos",
        (
            MenuItem("Cadastro de ativos", "assets_assets_list", "assets.view_asset"),
            MenuItem(
                "Classificações", "assets_classifications_list", "assets.view_assetclassification"
            ),
            MenuItem("Preços", "assets_prices_list", "assets.view_assetprice"),
            MenuItem("Eventos de mercado", "assets_events_list", "assets.view_assetevent"),
        ),
    ),
    MenuGroup(
        "Negociação",
        (
            MenuItem("Casas de negociação", "assets_venues_list", "assets.view_tradingvenue"),
            MenuItem("Listagens", "assets_listings_list", "assets.view_assetlisting"),
        ),
    ),
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

    @property
    def active(self) -> bool:
        return any(item.active for item in self.items)


def menu_for(request: HttpRequest) -> tuple[VisibleGroup, ...]:
    user = request.user
    current = request.resolver_match.url_name if request.resolver_match else None
    if current and current.endswith(("_new", "_edit")):
        current = current.rsplit("_", 1)[0] + "_list"
    groups = []
    for group in MENU:
        items = tuple(
            VisibleItem(item.label, item.url_name, active=item.is_current(current))
            for item in group.items
            if item.permission is None or user.has_perm(item.permission)
        )
        if items:
            groups.append(VisibleGroup(group.label, items))
    return tuple(groups)
