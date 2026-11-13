from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

# Create your views here.
import logging

from . import asistente
from .models import Alerta, ConsultaAsistente
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



@login_required
def asistente_financiero(request):
    """RF-37 (Premium): preguntas en lenguaje natural sobre el negocio activo."""
    negocio = request.negocio
    if not negocio.es_premium:
        messages.info(request, "El asistente financiero es una funcionalidad del Plan Premium.")
        return redirect("subscriptions:planes")

    respuesta = None
    pregunta = ""
    if request.method == "POST":
        pregunta = request.POST.get("pregunta", "").strip()
        if not pregunta:
            messages.error(request, "Escribe una pregunta.")
        elif not asistente.preguntas_restantes(negocio):
            messages.error(request, "Llegaste al máximo de preguntas de hoy. Vuelve mañana.")
        else:
            try:
                respuesta = asistente.responder(negocio, pregunta)
            except asistente.AsistenteNoDisponible as error:
                messages.error(request, str(error))
            else:
                ConsultaAsistente.objects.create(negocio=negocio, pregunta=pregunta[:500], respuesta=respuesta)
                pregunta = ""

    return render(request, "core/asistente.html", {
        "configurado": asistente.esta_configurado(),
        "respuesta": respuesta,
        "pregunta": pregunta,
        "restantes": asistente.preguntas_restantes(negocio),
        "historial": ConsultaAsistente.objects.filter(negocio=negocio)[:10],
    })
