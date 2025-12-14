from django.shortcuts import render

def panel_pedidos(request):
    # Vista del mesero/front: ve todos los pedidos y puede crear/confirmar/entregar/cerrar/cancelar
    return render(request, "panel/pedidos.html")

def panel_cocina(request):
    # Vista cocina: ve EN_PREPARACION y puede simular LISTO (webhook)
    return render(request, "panel/cocina.html")
