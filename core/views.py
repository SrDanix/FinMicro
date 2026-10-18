from django.shortcuts import redirect, render

# Create your views here.
import logging

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