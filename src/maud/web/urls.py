from django.contrib.auth.views import LogoutView
from django.urls import path

from maud.web.views import ShellLoginView, dashboard

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("login/", ShellLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
