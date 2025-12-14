from django.urls import path
from django.shortcuts import redirect
from .views import mesero, cocina, api_root

urlpatterns = [
    path("", lambda r: redirect("ui_mesero"), name="ui_home"),
    path("mesero/", mesero, name="ui_mesero"),
    path("cocina/", cocina, name="ui_cocina"),
    path("api/", api_root, name="ui_api"),
]
