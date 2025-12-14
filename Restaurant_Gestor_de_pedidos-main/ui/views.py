# ui/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils.timezone import localtime
import requests
import datetime

# ====== Datos de demo (menu + inventario) ======
PLATOS = [
    {"codigo": "HAMB_CARNE",  "nombre": "Hamburguesa de carne",  "ingredientes": ["pan", "carne", "lechuga"]},
    {"codigo": "HAMB_POLLO",  "nombre": "Hamburguesa de pollo",  "ingredientes": ["pan", "pollo", "lechuga"]},
    {"codigo": "FIDEOS_CARNE","nombre": "Fideos con carne",      "ingredientes": ["fideos", "carne"]},
    {"codigo": "FIDEOS_POLLO","nombre": "Fideos con pollo",      "ingredientes": ["fideos", "pollo"]},
    {"codigo": "ENSALADA",    "nombre": "Ensalada clásica",      "ingredientes": ["lechuga"]},
    {"codigo": "HOTDOG",      "nombre": "Hot Dog",               "ingredientes": ["pan"]},
]

INVENTARIO = {
    "pan": 200, "carne": 120, "pollo": 110, "lechuga": 160, "fideos": 180,
    "tomate": 150, "queso": 140, "cebolla": 130, "mayonesa": 100, "ketchup": 100,
    "mostaza": 90, "pepino": 90, "aji": 80, "papas": 200, "arroz": 200,
}

ESTADOS_ACTIVOS = {"CREADO", "EN_PREPARACION", "LISTO", "ENTREGADO"}


# ----------------- Helpers -----------------
def _api_base(request) -> str:
    return request.build_absolute_uri("/").rstrip("/")

def _abs(request, path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return f"{_api_base(request)}{path}"

def _ensure_slash(url: str) -> str:
    return url if url.endswith("/") else url + "/"

def _api_get(request, path):
    return requests.get(_abs(request, path), timeout=10)

def _api_post(request, path, json=None):
    return requests.post(_ensure_slash(_abs(request, path)), json=(json or {}), timeout=10)

def _api_patch(request, path, json=None):
    return requests.patch(_ensure_slash(_abs(request, path)), json=(json or {}), timeout=10)

def _nombre_plato(codigo: str) -> str:
    for p in PLATOS:
        if p["codigo"] == codigo:
            return p["nombre"]
    return codigo or "-"

def _fmt_hhmm(iso_str: str) -> str:
    """
    Espera un ISO 8601 (con zona o naive). Si falla, devuelve tal cual.
    """
    if not iso_str:
        return "—"
    try:
        # Django/DRF suelen devolver ISO con zona: 2025-11-13T22:07:29.141797-03:00
        dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dt = localtime(dt) if dt.tzinfo else dt
        return dt.strftime("%d/%m %H:%M")
    except Exception:
        return iso_str

def _enriquecer_pedido(p):
    """
    Agrega campos listos para la UI: plato legible, fechas formateadas.
    No rompe si el API cambia nombres (usa .get).
    """
    p = dict(p)  # copia
    p["plato_nombre"] = _nombre_plato(p.get("plato"))
    p["creado_str"] = _fmt_hhmm(p.get("creado_en") or p.get("creado"))
    p["actu_str"]    = _fmt_hhmm(p.get("actualizado_en") or p.get("actualizado"))
    return p

def _load_pedidos(request):
    r = _api_get(request, "/api/pedidos/")
    r.raise_for_status()
    data = r.json() or []
    # Si el API devuelve {"results":[...]}, tomar results
    if isinstance(data, dict) and "results" in data:
        data = data["results"]
    return [_enriquecer_pedido(item) for item in data]

def _load_mesas():
    url = "https://sistema-gestion-restaurant.up.railway.app/api/mesas/"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    return [
        m for m in data.get("results", [])
        if m.get("estado") == "disponible"
    ]



# ----------------- MESERO -----------------
def mesero(request):
    try:
        pedidos = _load_pedidos(request)
    except Exception as e:
        pedidos = []
        messages.error(request, f"No se pudieron cargar pedidos: {e}")

    try:
        mesas = _load_mesas()
    except Exception as e:
        mesas = []
        messages.error(request, f"No se pudieron cargar mesas: {e}")

    ctx = {
        "pedidos": pedidos,
        "platos": PLATOS,
        "mesas": mesas,
    }
    return render(request, "ui/mesero.html", ctx)
@require_http_methods(["POST"])
def crear_pedido(request):
    try:
        mesa = int(request.POST.get("mesa"))
    except (TypeError, ValueError):
        messages.error(request, "Mesa inválida.")
        return redirect("ui:mesero")

    cliente = (request.POST.get("cliente") or "").strip()
    plato   = (request.POST.get("plato") or "").strip()

    if not cliente or not plato:
        messages.warning(
            request,
            "Debes ingresar cliente y seleccionar un plato."
        )
        return redirect("ui:mesero")

    try:
        body = {
            "mesa": mesa,          # 🔥 AHORA ES ENTERO
            "cliente": cliente,
            "plato": plato
        }
        r = _api_post(request, "/api/pedidos/", json=body)

        if r.status_code in (200, 201):
            messages.success(
                request,
                f"Pedido para mesa {mesa} creado correctamente."
            )
        else:
            messages.error(
                request,
                f"No se pudo crear el pedido (HTTP {r.status_code})."
            )

    except Exception as e:
        messages.error(request, f"Error al crear pedido: {e}")

    return redirect("ui:mesero")

def accion_confirmar(request, pedido_id):
    try:
        r = _api_post(request, f"/api/pedidos/{pedido_id}/confirmar/")

        if r.status_code == 200:
            messages.success(request, "Pedido confirmado (EN_PREPARACION).")
        else:
            messages.error(request, f"No se pudo confirmar (HTTP {r.status_code}).")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect("ui:mesero")

def accion_cancelar(request, pedido_id):
    try:
        r = _api_post(request, f"/api/pedidos/{pedido_id}/cancelar/")
        if r.status_code == 200:
            messages.info(request, "Pedido cancelado (stock liberado).")
        else:
            messages.error(request, f"No se pudo cancelar (HTTP {r.status_code}).")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect("ui:mesero")

def accion_entregar(request, pedido_id):
    try:
        r = _api_patch(request, f"/api/pedidos/{pedido_id}/entregar/")
        if r.status_code == 200:
            messages.success(request, "Pedido marcado como ENTREGADO.")
        else:
            messages.error(request, f"No se pudo entregar (HTTP {r.status_code}).")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect("ui:mesero")

def accion_cerrar(request, pedido_id):
    try:
        r = _api_patch(request, f"/api/pedidos/{pedido_id}/cerrar/")
        if r.status_code == 200:
            messages.success(request, "Pedido CERRADO.")
        else:
            messages.error(request, f"No se pudo cerrar (HTTP {r.status_code}).")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect("ui:mesero")


# ----------------- COCINA -----------------
def cocina(request):
    try:
        pedidos = _load_pedidos(request)
    except Exception as e:
        pedidos = []
        messages.error(request, f"No se pudieron cargar pedidos: {e}")

    ctx = {"pedidos": pedidos}
    return render(request, "ui/cocina.html", ctx)

def cocina_en_preparacion(request, pedido_id):
    try:
        r = _api_post(request, f"/api/pedidos/{pedido_id}/confirmar")
        if r.status_code == 200:
            messages.success(request, "Pedido EN_PREPARACION.")
        else:
            messages.error(request, f"No se pudo cambiar estado (HTTP {r.status_code}).")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect("ui:cocina")

def cocina_sin_ingredientes(request, pedido_id):
    try:
        r = _api_post(request, f"/api/pedidos/{pedido_id}/cancelar")
        if r.status_code == 200:
            messages.info(request, "Cocina: sin ingredientes, pedido CANCELADO.")
        else:
            messages.error(request, f"No se pudo cancelar (HTTP {r.status_code}).")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect("ui:cocina")

def cocina_listo(request, pedido_id):
    """
    Llama al webhook de cocina para marcar LISTO.
    Este endpoint se publica en /api/webhooks/cocina/pedido-listo/ (mock).
    """
    try:
        body = {"pedido_id": str(pedido_id)}
        r = _api_post(request, "/api/webhooks/cocina/pedido-listo", json=body)
        if r.status_code in (200, 204):
            messages.success(request, "Cocina: pedido LISTO para entregar.")
        else:
            messages.error(request, f"No se pudo marcar listo (HTTP {r.status_code}/{r.status_code}).")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect("ui:cocina")


# ----------------- STOCK (demo) -----------------
def stock(request):
    # Si en el futuro lees stock real desde /api/stock/, puedes adaptarlo aquí.
    ctx = {"inventario": INVENTARIO}
    return render(request, "ui/stock.html", ctx)
