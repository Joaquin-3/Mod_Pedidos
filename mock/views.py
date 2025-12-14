# mock/views.py
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# --- inventario demo ---
INVENTARIO = {
    "pan": 100, "lechuga": 120, "tomate": 120, "cebolla": 100,
    "carne": 80, "pollo": 80, "queso": 90, "papas": 150,
    "fideos": 100, "salsa_pomodoro": 80, "aceite": 200, "sal": 200,
    "azucar": 80, "arroz": 100, "mayonesa": 80,
}

MENU = [
    {"id": "HAMB_CARNE",  "nombre": "Hamburguesa de carne",
     "ingredientes": {"pan":1, "carne":1, "lechuga":1}},
    {"id": "HAMB_POLLO",  "nombre": "Hamburguesa de pollo",
     "ingredientes": {"pan":1, "pollo":1, "lechuga":1}},
    {"id": "FIDEOS_CARNE","nombre": "Fideos con carne",
     "ingredientes": {"fideos":1, "carne":1}},
    {"id": "FIDEOS_POLLO","nombre": "Fideos con pollo",
     "ingredientes": {"fideos":1, "pollo":1}},
    {"id": "ENSALADA",    "nombre": "Ensalada clásica",
     "ingredientes": {"lechuga":1}},
    {"id": "HOTDOG",      "nombre": "Hot Dog",
     "ingredientes": {"pan":1}},
]

def _buscar_plato(pid):
    for p in MENU:
        if p["id"] == pid:
            return p
    return None

def _api_base(request) -> str:
    return request.build_absolute_uri("/").rstrip("/")

def _abs(request, path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return f"{_api_base(request)}{path}"

def _ensure_slash(url: str) -> str:
    return url if url.endswith("/") else url + "/"

# --------- endpoints demo ----------
def menu(request):
    return JsonResponse({"platos": [{"codigo": p["id"], "nombre": p["nombre"]} for p in MENU]})

def stock_estado(request):
    return JsonResponse({"inventario": INVENTARIO})

@csrf_exempt
def validar_reservar(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"detail": "JSON inválido"}, status=400)

    plato_id = data.get("plato_id")
    p = _buscar_plato(plato_id)
    if not p:
        return JsonResponse({"detail": "Plato no existe"}, status=404)

    for ing, cant in p["ingredientes"].items():
        if INVENTARIO.get(ing, 0) < cant:
            return JsonResponse({"ok": False, "detail": f"Sin stock de {ing}"}, status=409)

    for ing, cant in p["ingredientes"].items():
        INVENTARIO[ing] -= cant

    return JsonResponse({"ok": True})

@csrf_exempt
def liberar(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"detail": "JSON inválido"}, status=400)

    plato_id = data.get("plato_id")
    p = _buscar_plato(plato_id)
    if not p:
        return JsonResponse({"detail": "Plato no existe"}, status=404)

    for ing, cant in p["ingredientes"].items():
        INVENTARIO[ing] = INVENTARIO.get(ing, 0) + cant

    return JsonResponse({"ok": True})

@csrf_exempt
def cocina_pedido_listo(request):
    """
    Webhook que marca un pedido como LISTO en la API real.
    Se llama desde UI: POST /api/webhooks/cocina/pedido-listo/
    Body JSON: {"pedido_id": "<uuid>"}
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"detail": "JSON inválido"}, status=400)

    pid = data.get("pedido_id")
    if not pid:
        return JsonResponse({"detail": "pedido_id requerido"}, status=400)

    # Opción A: tu API tiene acción /api/pedidos/<id>/listo/
    url = _ensure_slash(_abs(request, f"/api/pedidos/{pid}/listo"))
    try:
        resp = requests.patch(url, timeout=10)
        # Si tu API no tiene /listo/, puedes cambiar a:
        # resp = requests.patch(_ensure_slash(_abs(request, f"/api/pedidos/{pid}")),
        #                      json={"estado": "LISTO"}, timeout=10)
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)

    if resp.status_code in (200, 204):
        return JsonResponse({"ok": True}, status=204)
    return JsonResponse({"detail": "backend responded", "status": resp.status_code}, status=resp.status_code)
