"""Vistas de autenticación, perfil, configuración, colaboradores y datos personales."""
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from subscriptions.services import asegurar_plan_basico
from .forms import ConfiguracionForm, EliminarCuentaForm, InvitacionForm, PerfilForm, RegistroForm
from .models import Colaboracion
from .negocio import SESION_NEGOCIO, negocios_disponibles


def registro(request):
    """Alta de un nuevo microempresario.

    Al registrarse, se le asigna automáticamente el Plan Básico (gratuito)
    definido en la Sección 5.1 del informe, para que el usuario entre
    directamente al dashboard sin pasos intermedios obligatorios.
    """
    if request.user.is_authenticated:
        return redirect("finances:dashboard")

    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            asegurar_plan_basico(usuario)
            login(request, usuario)
            messages.success(
                request,
                f"¡Bienvenido a FinMicro, {usuario.nombre_negocio}! Tu cuenta quedó activa en el Plan Básico.",
            )
            return redirect("finances:dashboard")
    else:
        form = RegistroForm()

    return render(request, "accounts/registro.html", {"form": form})


@login_required
def perfil(request):
    if request.method == "POST":
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Tus datos se actualizaron correctamente.")
            return redirect("accounts:perfil")
    else:
        form = PerfilForm(instance=request.user)

    return render(request, "accounts/perfil.html", {"form": form})


@login_required
def configuracion(request):
    """Régimen tributario, IVA, honorarios y meta de ventas (RF-05)."""
    if request.method == "POST":
        form = ConfiguracionForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuración guardada.")
            return redirect("accounts:configuracion")
    else:
        form = ConfiguracionForm(instance=request.user)
    return render(request, "accounts/configuracion.html", {"form": form})


# --- Colaboradores (RF-06) -------------------------------------------------


@login_required
def colaboradores(request):
    if request.method == "POST":
        form = InvitacionForm(request.POST, propietario=request.user)
        if form.is_valid():
            invitacion = form.save(commit=False)
            invitacion.propietario = request.user
            invitacion.save()
            enlace = request.build_absolute_uri(
                reverse("accounts:aceptar_invitacion", args=[invitacion.token])
            )
            send_mail(
                f"{request.user.nombre_negocio} te invitó a FinMicro",
                f"Te invitaron a colaborar en {request.user.nombre_negocio} "
                f"({invitacion.get_rol_display().lower()}).\n\n"
                f"Crea tu cuenta con este mismo correo y abre el enlace:\n{enlace}",
                settings.DEFAULT_FROM_EMAIL,
                [invitacion.email],
                fail_silently=True,
            )
            messages.success(request, f"Invitación creada para {invitacion.email}.")
            return redirect("accounts:colaboradores")
    else:
        form = InvitacionForm(propietario=request.user)

    otorgadas = request.user.colaboraciones_otorgadas.select_related("colaborador")
    recibidas = Colaboracion.objects.filter(
        email__iexact=request.user.email, estado=Colaboracion.Estado.PENDIENTE
    ).select_related("propietario")
    accesos = Colaboracion.objects.filter(
        colaborador=request.user, estado=Colaboracion.Estado.ACEPTADA
    ).select_related("propietario")
    return render(
        request,
        "accounts/colaboradores.html",
        {"form": form, "otorgadas": otorgadas, "recibidas": recibidas, "accesos": accesos},
    )


@login_required
@require_POST
def revocar_colaborador(request, pk):
    colaboracion = get_object_or_404(Colaboracion, pk=pk, propietario=request.user)
    colaboracion.delete()
    messages.success(request, f"Se quitó el acceso de {colaboracion.email}.")
    return redirect("accounts:colaboradores")


@login_required
@require_POST
def abandonar_negocio(request, pk):
    colaboracion = get_object_or_404(Colaboracion, pk=pk, colaborador=request.user)
    colaboracion.delete()
    messages.success(request, f"Ya no colaboras en {colaboracion.propietario.nombre_negocio}.")
    return redirect("accounts:colaboradores")


@login_required
def aceptar_invitacion(request, token):
    invitacion = get_object_or_404(
        Colaboracion.objects.select_related("propietario"), token=token
    )
    correo_coincide = invitacion.email.lower() == (request.user.email or "").lower()

    if request.method == "POST" and correo_coincide:
        if invitacion.estado == Colaboracion.Estado.PENDIENTE:
            invitacion.colaborador = request.user
            invitacion.estado = Colaboracion.Estado.ACEPTADA
            invitacion.save(update_fields=["colaborador", "estado"])
        request.session[SESION_NEGOCIO] = invitacion.propietario_id
        messages.success(request, f"Ahora colaboras en {invitacion.propietario.nombre_negocio}.")
        return redirect("finances:dashboard")

    return render(
        request,
        "accounts/invitacion.html",
        {"invitacion": invitacion, "correo_coincide": correo_coincide},
    )


@login_required
@require_POST
def cambiar_negocio(request):
    try:
        negocio_id = int(request.POST.get("negocio_id", ""))
    except ValueError:
        negocio_id = request.user.pk
    permitidos = {negocio.pk for negocio, _ in negocios_disponibles(request.user)}
    if negocio_id == request.user.pk or negocio_id not in permitidos:
        request.session.pop(SESION_NEGOCIO, None)
    else:
        request.session[SESION_NEGOCIO] = negocio_id
    return redirect("finances:dashboard")


# --- Datos personales, Ley 19.628 (RF-07) ------------------------------------


@login_required
def exportar_datos(request):
    """Derecho de acceso: descarga en JSON de todos los datos del usuario."""
    u = request.user
    datos = {
        "exportado_en": timezone.now(),
        "perfil": {
            "usuario": u.username,
            "email": u.email,
            "rut": u.rut,
            "nombre_negocio": u.nombre_negocio,
            "rubro": u.get_tipo_negocio_display(),
            "telefono": u.telefono,
            "comuna": u.comuna,
            "regimen_tributario": u.get_regimen_tributario_display(),
            "afecto_iva": u.afecto_iva,
            "emite_boletas_honorarios": u.emite_boletas_honorarios,
            "meta_ventas_mensual": u.meta_ventas_mensual,
            "fecha_registro": u.fecha_registro,
        },
        "categorias_propias": list(u.categorias.values("nombre", "tipo", "es_gravable_iva")),
        "movimientos": list(
            u.movimientos.values("fecha", "tipo", "categoria__nombre", "monto", "descripcion")
        ),
        "suscripciones": list(
            u.suscripciones.values("plan__nombre", "estado", "metodo_pago", "fecha_inicio", "fecha_fin")
        ),
        "colaboradores_invitados": list(
            u.colaboraciones_otorgadas.values("email", "rol", "estado")
        ),
    }
    respuesta = HttpResponse(
        json.dumps(datos, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2),
        content_type="application/json; charset=utf-8",
    )
    nombre = f"finmicro-{u.username}-{timezone.localdate():%Y%m%d}.json"
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
    return respuesta


@login_required
def eliminar_cuenta(request):
    """Derecho de cancelación: borra la cuenta y todos sus datos."""
    if request.method == "POST":
        form = EliminarCuentaForm(request.POST, usuario=request.user)
        if form.is_valid():
            usuario = request.user
            with transaction.atomic():
                # Movimiento.categoria es PROTECT: se borran antes que las categorías.
                usuario.movimientos.all().delete()
                usuario.delete()
            logout(request)
            messages.success(request, "Tu cuenta y todos tus datos fueron eliminados.")
            return redirect("core:home")
    else:
        form = EliminarCuentaForm(usuario=request.user)
    return render(request, "accounts/eliminar_cuenta.html", {"form": form})
