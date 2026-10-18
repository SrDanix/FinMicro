from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
"""Vistas del módulo de suscripciones (Plan Básico / Premium)."""
import json



from .models import Plan, Suscripcion
from .services import asegurar_plan_premium, obtener_pasarela


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
    """GET solo muestra la página de confirmación (acción seguridad/idempotente).

    Cualquier cambio real de plan —incluyendo el downgrade gratuito a
    Básico— ocurre exclusivamente con POST, para que un simple enlace o
    un crawler no pueda disparar un cambio de suscripción.
    """
    plan = get_object_or_404(Plan, codigo=codigo_plan, activo=True)

    if request.method != "POST":
        return render(request, "subscriptions/confirmar_plan.html", {"plan": plan})

    if plan.codigo == Plan.Codigo.BASICO:
        Suscripcion.objects.filter(usuario=request.user, estado=Suscripcion.Estado.ACTIVA).update(
            estado=Suscripcion.Estado.CANCELADA
        )
        Suscripcion.objects.create(
            usuario=request.user, plan=plan, estado=Suscripcion.Estado.ACTIVA
        )
        messages.success(request, "Cambiaste al Plan Básico.")
        return redirect("subscriptions:mi_suscripcion")

    nombre_pasarela = request.POST.get("pasarela", "khipu")
    suscripcion = Suscripcion.objects.create(
        usuario=request.user, plan=plan, estado=Suscripcion.Estado.PENDIENTE
    )
    pasarela = obtener_pasarela(nombre_pasarela)
    url_pago = pasarela.iniciar_pago(request, suscripcion)
    return redirect(url_pago)


@login_required
def pago_simulado(request, suscripcion_id):
    """Solo disponible cuando PAGOS_MODO_SIMULADO=True (ver services.py).

    Reemplaza a la pantalla real de Khipu/Flow mientras no haya
    credenciales de comercio configuradas, para poder probar el flujo
    completo de alta a Premium en desarrollo.
    """
    suscripcion = get_object_or_404(Suscripcion, id=suscripcion_id, usuario=request.user)

    if request.method == "POST":
        Suscripcion.objects.filter(
            usuario=request.user, estado=Suscripcion.Estado.ACTIVA
        ).exclude(id=suscripcion.id).update(estado=Suscripcion.Estado.CANCELADA)
        suscripcion.activar()
        messages.success(request, f"Pago simulado aprobado. Ya tienes el {suscripcion.plan.nombre}.")
        return redirect("subscriptions:mi_suscripcion")

    return render(request, "subscriptions/pago_simulado.html", {"suscripcion": suscripcion})


@csrf_exempt
def webhook_khipu(request):
    """Notificación de pago de Khipu. Ver KhipuGateway.confirmar_pago."""
    if request.method != "POST":
        return HttpResponse(status=405)

    referencia = request.POST.get("payment_id") or request.POST.get("transaction_id")
    suscripcion = Suscripcion.objects.filter(referencia_pago=referencia).first()
    if not suscripcion:
        return HttpResponse(status=404)

    pasarela = obtener_pasarela("khipu")
    if pasarela.confirmar_pago(request.POST.dict()):
        suscripcion.activar()
    return HttpResponse(status=200)


@csrf_exempt
def webhook_flow(request):
    """Notificación de pago de Flow.cl. Ver FlowGateway.confirmar_pago."""
    if request.method != "POST":
        return HttpResponse(status=405)

    token = request.POST.get("token")
    suscripcion = Suscripcion.objects.filter(referencia_pago=token).first()
    if not suscripcion:
        return HttpResponse(status=404)

    # En una integración real, aquí se llama a payment/getStatus con el
    # token para obtener el estado antes de confirmar (ver services.py).
    pasarela = obtener_pasarela("flow")
    if pasarela.confirmar_pago(json.loads(request.body or "{}")):
        suscripcion.activar()
    return HttpResponse(status=200)


@login_required
def mi_suscripcion(request):
    historial = request.user.suscripciones.select_related("plan").order_by("-creada_en")
    return render(
        request,
        "subscriptions/mi_suscripcion.html",
        {"suscripcion_activa": request.user.suscripcion_activa, "historial": historial},
    )