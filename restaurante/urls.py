from django.contrib import admin
from django.urls import path, include

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("ui.urls","ui"), namespace="ui")),
    path("mock/", include("mock.urls")),
    path("api/", include("pedidos.urls")),

    path("api/webhooks/", include(("mock.urls","mock"), namespace="mock")),
]

