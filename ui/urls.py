from django.urls import path
from . import views

app_name = "ui"

urlpatterns = [
    # Mesero
    path("", views.mesero, name="mesero"),
    path("crear/", views.crear_pedido, name="crear_pedido"),

    path("accion/<uuid:pedido_id>/confirmar/", views.accion_confirmar, name="confirmar"),
    path("accion/<uuid:pedido_id>/cancelar/",  views.accion_cancelar,  name="cancelar"),
    path("accion/<uuid:pedido_id>/entregar/",  views.accion_entregar,  name="entregar"),
    path("accion/<uuid:pedido_id>/cerrar/",    views.accion_cerrar,    name="cerrar"),

    # Cocina
    path("cocina/", views.cocina, name="cocina"),
    path("cocina/<uuid:pedido_id>/en-preparacion/", views.cocina_en_preparacion, name="cocina_en_preparacion"),
    path("cocina/<uuid:pedido_id>/sin-ingredientes/", views.cocina_sin_ingredientes, name="cocina_sin_ingredientes"),
    path("cocina/<uuid:pedido_id>/listo/", views.cocina_listo, name="cocina_listo"),

    # Stock ✅
    path("stock/", views.stock, name="stock"),
]
