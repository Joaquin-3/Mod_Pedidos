import json
from django.urls import reverse
from rest_framework.test import APITestCase
from pedidos.models import Pedido

class FlujoPedidoTest(APITestCase):
    def setUp(self):
        self.p = Pedido.objects.create(mesa="Z9", cliente="Test")

    def test_crear_listar(self):
        url_list = reverse("pedidos-list")
        res = self.client.get(url_list)
        self.assertEqual(res.status_code, 200)

    def test_confirmar_entregar_cerrar(self):
        # confirmar
        url_conf = reverse("pedidos-confirmar", args=[self.p.id])
        r1 = self.client.post(url_conf)
        self.assertIn(r1.status_code, [200, 409])  # 409 si mock simula sin stock

        # webhook LISTO
        url_webhook = reverse("webhook-cocina-pedido-listo")
        r2 = self.client.post(
            url_webhook,
            data=json.dumps({"pedido_id": str(self.p.id), "estado": "LISTO"}),
            content_type="application/json",
        )
        self.assertIn(r2.status_code, [200, 204])

        # entregar
        url_ent = reverse("pedidos-entregar", args=[self.p.id])
        r3 = self.client.patch(url_ent)
        self.assertEqual(r3.status_code, 200)

        # cerrar
        url_cer = reverse("pedidos-cerrar", args=[self.p.id])
        r4 = self.client.patch(url_cer)
        self.assertEqual(r4.status_code, 200)
