"""O que toda tela recebe: a identidade da gestora, o tema escolhido e o menu."""

from dataclasses import dataclass

from django.http import HttpRequest

from maud.modules.branding.api import BrandingView, current_branding
from maud.web.navigation import VisibleGroup, menu_for

THEME_COOKIE = "theme"
THEMES = ("dark", "light")


@dataclass(frozen=True)
class Shell:
    branding: BrandingView
    theme: str
    menu: tuple[VisibleGroup, ...]


def shell(request: HttpRequest) -> dict[str, Shell]:
    theme = request.COOKIES.get(THEME_COOKIE, THEMES[0])
    menu = menu_for(request) if request.user.is_authenticated else ()
    return {
        "shell": Shell(
            branding=current_branding(),
            theme=theme if theme in THEMES else THEMES[0],
            menu=menu,
        )
    }
