from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Pedido
from .serializers import PedidoSerializer


class PedidoViewSet(ModelViewSet):
    """
    API de Pedidos.

    Endpoints generados automáticamente por el router:
    - GET    /api/pedidos/           -> list
    - POST   /api/pedidos/           -> create
    - GET    /api/pedidos/{id}/      -> retrieve
    - PUT    /api/pedidos/{id}/      -> update
    - PATCH  /api/pedidos/{id}/      -> partial_update
    - DELETE /api/pedidos/{id}/      -> destroy

    Acciones personalizadas:
    - POST   /api/pedidos/{id}/confirmar/
    - POST   /api/pedidos/{id}/cancelar/
    - PATCH  /api/pedidos/{id}/listo/
    - PATCH  /api/pedidos/{id}/entregar/
    - PATCH  /api/pedidos/{id}/cerrar/
    """

    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer

    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        """
        Confirma el pedido: valida stock (Módulo 1) y lo pasa a EN_PREPARACION.
        """
        pedido = self.get_object()
        try:
            pedido.confirmar()  # método del modelo
            serializer = self.get_serializer(pedido)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        """
        Cancela el pedido y libera el stock reservado.
        """
        pedido = self.get_object()
        try:
            pedido.cancelar()  # método del modelo
            serializer = self.get_serializer(pedido)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"])
    def listo(self, request, pk=None):
        """
        Marca el pedido como LISTO desde la cocina.

        Este endpoint lo llama el webhook:
          POST /api/webhooks/cocina/pedido-listo/
        que internamente hace PATCH a:
          /api/pedidos/{id}/listo/
        """
        pedido = self.get_object()
        try:
            pedido.marcar_listo()  # método del modelo
            serializer = self.get_serializer(pedido)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"])
    def entregar(self, request, pk=None):
        """
        Marca el pedido como ENTREGADO al cliente.
        """
        pedido = self.get_object()
        try:
            pedido.entregar()  # método del modelo
            serializer = self.get_serializer(pedido)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"])
    def cerrar(self, request, pk=None):
        """
        Cierra el pedido (venta finalizada).
        """
        pedido = self.get_object()
        try:
            pedido.cerrar()  # método del modelo
            serializer = self.get_serializer(pedido)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def cocina_estado(request):
    """
    Cambia el estado desde la 'pantalla de cocina'.
    body: { "pedido_id": "<uuid>", "estado": "EN_PREPARACION|LISTO|CANCELADO" }
    """
    pid = request.data.get("pedido_id")
    estado = request.data.get("estado")
    if not pid or not estado:
        return Response(
            {"detail": "pedido_id y estado son requeridos."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        p = Pedido.objects.get(pk=pid)
        if estado == "EN_PREPARACION":
            if p.estado != Pedido.Estado.CREADO:
                return Response(
                    {"detail": "Solo desde CREADO."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            p.estado = Pedido.Estado.EN_PREPARACION
            p.full_clean()
            p.save(update_fields=["estado", "actualizado_en"])
        elif estado == "LISTO":
            p.marcar_listo()
        elif estado == "CANCELADO":
            p.cancelar()
        else:
            return Response({"detail": "Estado inválido."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PedidoSerializer(p).data)
    except Pedido.DoesNotExist:
        return Response({"detail": "Pedido no existe."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def cocina_list(request):
    """
    Devuelve pedidos activos para visualizar en la cocina.
    (excluye CANCELADO y CERRADO)
    """
    activos = Pedido.objects.exclude(
        estado__in=[Pedido.Estado.CANCELADO, Pedido.Estado.CERRADO]
    ).order_by("creado_en")
    return Response(PedidoSerializer(activos, many=True).data)
