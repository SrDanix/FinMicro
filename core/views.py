from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

# Create your views here.
import logging

from .models import Alerta
from .services import BancoCentralService

logger = logging.getLogger(__name__)


def home(request):
    if request.user.is_authenticated:
        return redirect("finances:dashboard")

    indicadores = None
    try:
        datos = BancoCentralService.indicadores_del_dia()
        indicadores = {
            clave: datos[clave]
            for clave in ("uf", "dolar", "utm", "ipc")
            if clave in datos
        }
    except Exception:
        # La landing page no debe romperse si mindicador.cl está caído o
        # no hay salida a internet (p. ej. corriendo en un entorno
        # aislado). Se registra el error y simplemente no se muestra el
        # bloque de indicadores.
        logger.warning("No se pudo obtener indicadores del Banco Central.", exc_info=True)

    return render(request, "core/home.html", {"indicadores": indicadores})


@login_required
def alertas(request):
    return render(request, "core/alertas.html", {"alertas": Alerta.objects.filter(negocio=request.negocio)[:100]})


@login_required
@require_POST
def marcar_alerta_leida(request, pk):
    alerta = get_object_or_404(Alerta, pk=pk, negocio=request.negocio)
    alerta.leida = True
    alerta.save(update_fields=["leida"])
    siguiente = request.POST.get("siguiente", "")
    if not url_has_allowed_host_and_scheme(siguiente, allowed_hosts={request.get_host()}):
        siguiente = "core:alertas"
    return redirect(siguiente)
