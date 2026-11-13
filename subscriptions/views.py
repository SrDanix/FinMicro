"""Vistas del módulo de suscripciones (Plan Básico / Premium)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.auditoria import Accion, registrar
from .models import Plan, Suscripcion
from .services import (
    ErrorPasarela,
    activar_suscripcion_pagada,
    asegurar_plan_premium,
    cambiar_a_basico,
    obtener_pasarela,
    procesar_notificacion,
)

PASARELAS = ("khipu", "flow")


@login_required
def planes(request):
    asegurar_plan_premium()
    lista_planes = Plan.objects.filter(activo=True)
    return render(
        request,
        "subscriptions/planes.html",
        {"planes": lista_planes, "suscripcion_activa": request.user.suscripcion_activa},
    )


@login_required
def suscribirse(request, codigo_plan):
    """GET solo muestra la página de confirmación (acción segura e idempotente).

    Cualquier cambio real de plan —incluyendo el downgrade gratuito a
    Básico— ocurre exclusivamente con POST, para que un simple enlace o
    un crawler no pueda disparar un cambio de suscripción.
    """
    plan = get_object_or_404(Plan, codigo=codigo_plan, activo=True)

    if request.method != "POST":
        return render(request, "subscriptions/confirmar_plan.html", {"plan": plan})

    if plan.codigo == Plan.Codigo.BASICO:
        cambiar_a_basico(request.user, request=request)
        messages.success(request, "Cambiaste al Plan Básico.")
        return redirect("subscriptions:mi_suscripcion")

    nombre_pasarela = request.POST.get("pasarela", "khipu")
    if nombre_pasarela not in PASARELAS:
        messages.error(request, "Elige un medio de pago válido.")
        return redirect("subscriptions:suscribirse", codigo_plan=plan.codigo)
    suscripcion = Suscripcion.objects.create(
        usuario=request.user, plan=plan, estado=Suscripcion.Estado.PENDIENTE
    )
    registrar(Accion.CAMBIO_PLAN, request=request, detalle=f"Inicia pago de {plan.nombre} con {nombre_pasarela}")
    url_pago = obtener_pasarela(nombre_pasarela).iniciar_pago(request, suscripcion)
    return redirect(url_pago)


@login_required
def pago_simulado(request, suscripcion_id):
    """Solo disponible cuando PAGOS_MODO_SIMULADO=True (ver services.py).

    Reemplaza a la pantalla real de Khipu/Flow mientras no haya
    credenciales de comercio configuradas, para poder probar el flujo
    completo de alta a Premium en desarrollo.
    """
    suscripcion = get_object_or_404(
        Suscripcion, id=suscripcion_id, usuario=request.user, estado=Suscripcion.Estado.PENDIENTE
    )
    if not obtener_pasarela(suscripcion.metodo_pago or "khipu")._modo_simulado():
        return HttpResponse(status=404)

    if request.method == "POST":
        activar_suscripcion_pagada(suscripcion)
        messages.success(request, f"Pago simulado aprobado. Ya tienes el {suscripcion.plan.nombre}.")
        return redirect("subscriptions:mi_suscripcion")

    return render(request, "subscriptions/pago_simulado.html", {"suscripcion": suscripcion})


def _webhook(request, nombre_pasarela, referencia):
    """RF-27: el aviso solo dice "revisa este pago"; el estado se consulta a la pasarela."""
    if not referencia:
        return HttpResponse(status=400)
    try:
        suscripcion = procesar_notificacion(nombre_pasarela, referencia)
    except ErrorPasarela:
        # 502: la pasarela reintentará el aviso más tarde.
        return HttpResponse(status=502)
    return HttpResponse(status=200 if suscripcion else 404)


@csrf_exempt
@require_POST
def webhook_khipu(request):
    return _webhook(request, "khipu", request.POST.get("payment_id", ""))


@csrf_exempt
@require_POST
def webhook_flow(request):
    return _webhook(request, "flow", request.POST.get("token", ""))


@csrf_exempt
def retorno_pago(request):
    """Flow devuelve al usuario con un POST. No activa nada: solo informa y redirige."""
    messages.info(request, "Estamos confirmando tu pago con la pasarela. Si fue aprobado, tu plan se activa en unos segundos.")
    return redirect("subscriptions:mi_suscripcion")


@login_required
def mi_suscripcion(request):
    historial = request.user.suscripciones.select_related("plan").order_by("-creada_en")
    return render(
        request,
        "subscriptions/mi_suscripcion.html",
        {"suscripcion_activa": request.user.suscripcion_activa, "historial": historial},
    )
