"""Telas da casca: entrar, sair e o painel."""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


class ShellLoginView(LoginView):
    template_name = "web/login.html"
    redirect_authenticated_user = True


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Painel. Os números entram quando houver apólices; por ora, os primeiros passos."""
    return render(request, "web/dashboard.html")
