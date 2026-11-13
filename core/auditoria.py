"""RF-32: registro de acciones sensibles (inicio de sesión, cambios de plan, eliminación de datos)."""
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from .models import RegistroAuditoria

Accion = RegistroAuditoria.Accion


def ip_de(request):
    """IP del cliente. Detrás de Nginx llega en X-Forwarded-For (deploy/nginx)."""
    if request is None:
        return None
    reenviada = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return (reenviada.split(",")[0].strip() or request.META.get("REMOTE_ADDR")) or None


def registrar(accion, *, request=None, usuario=None, detalle=""):
    if usuario is None and request is not None and request.user.is_authenticated:
        usuario = request.user
    return RegistroAuditoria.objects.create(
        # Una cuenta recién eliminada ya no tiene pk: se guarda solo el nombre.
        usuario=usuario if getattr(usuario, "pk", None) else None,
        nombre_usuario=getattr(usuario, "username", "") or "",
        accion=accion,
        detalle=detalle[:300],
        ip=ip_de(request),
    )


@receiver(user_logged_in)
def _al_iniciar_sesion(sender, request, user, **kwargs):
    registrar(Accion.INICIO_SESION, request=request, usuario=user)


@receiver(user_logged_out)
def _al_cerrar_sesion(sender, request, user, **kwargs):
    if user is not None:
        registrar(Accion.CIERRE_SESION, request=request, usuario=user)


@receiver(user_login_failed)
def _al_fallar_inicio(sender, credentials, request=None, **kwargs):
    # Nunca se guarda la contraseña: solo el nombre de usuario intentado.
    registrar(Accion.INICIO_FALLIDO, request=request, detalle=f"Usuario intentado: {credentials.get('username', '')}")
