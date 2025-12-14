# mock/urls.py
from django.urls import path
from . import views

app_name = "mock"

urlpatterns = [
    path("menu/",                 views.menu,               name="menu"),
    path("stock/estado/",         views.stock_estado,       name="stock_estado"),
    path("validar-reservar/",     views.validar_reservar,   name="validar_reservar"),
    path("liberar/",              views.liberar,            name="liberar"),
    path("cocina/pedido-listo/",  views.cocina_pedido_listo, name="cocina_pedido_listo"),
]
