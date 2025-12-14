import hmac, hashlib, requests
from django.conf import settings

class StockClientM1:
    def __init__(self, base_url=None, timeout=5):
        self.base_url = base_url or settings.M1_BASE_URL
        self.timeout = timeout

    def validar_reservar(self, pedido_id, items):
        url = f"{self.base_url}/stock/validar-reservar"
        payload = {"pedido_id": str(pedido_id), "items": items}
        r = requests.post(url, json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def liberar_reserva(self, reserva_id):
        url = f"{self.base_url}/stock/liberar"
        r = requests.post(url, json={"reserva_id": reserva_id}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def confirmar_descuento(self, reserva_id):
        url = f"{self.base_url}/stock/confirmar"
        r = requests.post(url, json={"reserva_id": reserva_id}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()


class CocinaClientM4:
    def __init__(self, base_url=None, timeout=5):
        self.base_url = base_url or settings.M4_BASE_URL
        self.timeout = timeout

    def enviar_pedido(self, pedido):
        url = f"{self.base_url}/cocina/pedidos"
        payload = {"id": str(pedido.id), "mesa": pedido.mesa, "items": pedido.items}
        r = requests.post(url, json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()


def build_signature(secret: str, body_bytes: bytes) -> str:
    mac = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256)
    return mac.hexdigest()
