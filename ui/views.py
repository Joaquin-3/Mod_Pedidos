from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils.timezone import localtime
import requests
import datetime


# ===================== HELPERS (SE MANTIENEN) =====================

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
    return requests.post(
        _ensure_slash(_abs(request, path)),
        json=(json or {}),
        timeout=10
    )

def _api_patch(request, path, json=None):
    return requests.patch(
        _ensure_slash(_abs(request, path)),
        json=(json or {}),
        timeout=10
    )


# ===================== UTIL =====================

def _fmt_hhmm(iso_str):
    if not iso_str:
        return "—"
    try:
        dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dt = localtime(dt) if dt.tzinfo else dt
        return dt.strftime("%d/%m %H:%M")
    except Exception:
        return iso_str


# ===================== PLATOS (API EXTERNA) =====================

def load_platos():
    url = "https://web-production-2d3fb.up.railway.app/api/platos/"
    r = requests.get(url, timeout=10)
    r.raise_for_status()

    data = r.json()
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data


def nombre_plato(codigo, platos):
    for p in platos:
        if p.get("codigo") == codigo:
            return p.get("nombre")
    return codigo


# ===================== MESAS (API EXTERNA) =====================

def load_mesas():
    url = "https://sistema-gestion-restaurant.up.railway.app/api/mesas/"
    r = requests.get(url, timeout=10)
    r.raise_for_status()

    data = r.json()
    return [
        m for m in data.get("results", [])
        if m.get("estado") == "disponible"
    ]


# ===================== PEDIDOS =====================

def load_pedidos(request, platos):
    r = _api_get(request, "/api/pedidos/")
    r.raise_for_status()

    data = r.json()
    if isinstance(data, dict) and "results" in data:
        data = data["results"]

    pedidos = []
    for p in data:
        p = dict(p)
        p["plato_nombre"] = nombre_plato(p.get("plato"), platos)
        p["creado_str"] = _fmt_hhmm(p.get("creado_en"))
        pedidos.append(p)

    return pedidos


# ===================== MESERO =====================

def mesero(request):
    try:
        platos = load_platos()
    except Exception as e:
        platos = []
        messages.error(request, f"No se pudieron cargar platos: {e}")

    try:
        mesas = load_mesas()
    except Exception as e:
        mesas = []
        messages.error(request, f"No se pudieron cargar mesas: {e}")

    try:
        pedidos = load_pedidos(request, platos)
    except Exception as e:
        pedidos = []
        messages.error(request, f"No se pudieron cargar pedidos: {e}")

    return render(request, "ui/mesero.html", {
        "platos": platos,
        "mesas": mesas,
        "pedidos": pedidos
    })


@require_http_methods(["POST"])
def crear_pedido(request):
    mesa = request.POST.get("mesa")
    cliente = request.POST.get("cliente")
    plato = request.POST.get("plato")

    body = {
        "mesa": int(mesa),
        "cliente": cliente,
        "plato": plato
    }

    r = _api_post(request, "/api/pedidos/", json=body)

    if r.status_code in (200, 201):
        messages.success(request, "Pedido creado correctamente.")
    else:
        messages.error(request, f"Error al crear pedido (HTTP {r.status_code}).")

    return redirect("ui:mesero")


# ===================== ACCIONES MESERO =====================

def accion_confirmar(request, pedido_id):
    r = _api_post(request, f"/api/pedidos/{pedido_id}/confirmar/")
    if r.status_code == 200:
        messages.success(request, "Pedido confirmado.")
    else:
        messages.error(request, "No se pudo confirmar.")
    return redirect("ui:mesero")


def accion_cancelar(request, pedido_id):
    r = _api_post(request, f"/api/pedidos/{pedido_id}/cancelar/")
    if r.status_code == 200:
        messages.info(request, "Pedido cancelado.")
    else:
        messages.error(request, "No se pudo cancelar.")
    return redirect("ui:mesero")


def accion_entregar(request, pedido_id):
    r = _api_patch(request, f"/api/pedidos/{pedido_id}/entregar/")
    if r.status_code == 200:
        messages.success(request, "Pedido entregado.")
    else:
        messages.error(request, "No se pudo entregar.")
    return redirect("ui:mesero")


def accion_cerrar(request, pedido_id):
    r = _api_patch(request, f"/api/pedidos/{pedido_id}/cerrar/")
    if r.status_code == 200:
        messages.success(request, "Pedido cerrado.")
    else:
        messages.error(request, "No se pudo cerrar.")
    return redirect("ui:mesero")


# ===================== COCINA =====================

def cocina(request):
    platos = load_platos()
    pedidos = load_pedidos(request, platos)
    return render(request, "ui/cocina.html", {"pedidos": pedidos})


def cocina_en_preparacion(request, pedido_id):
    _api_post(request, f"/api/pedidos/{pedido_id}/confirmar/")
    return redirect("ui:cocina")


def cocina_sin_ingredientes(request, pedido_id):
    _api_post(request, f"/api/pedidos/{pedido_id}/cancelar/")
    return redirect("ui:cocina")


def cocina_listo(request, pedido_id):
    _api_post(
        request,
        "/api/webhooks/cocina/pedido-listo/",
        json={"pedido_id": str(pedido_id)}
    )
    return redirect("ui:cocina")


# ===================== STOCK =====================

def stock(request):
    return render(request, "ui/stock.html")
