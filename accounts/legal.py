"""RF-29: documentos legales vigentes y registro de su aceptación."""

from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from core.auditoria import Accion, ip_de, registrar

from .models import Consentimiento, DocumentoLegal

SESION_CONSENTIMIENTO = "consentimiento_vigente"


def documentos_vigentes():
    """El documento más reciente ya vigente de cada tipo."""
    vigentes = {}
    for documento in DocumentoLegal.objects.filter(vigente_desde__lte=timezone.now()).order_by("-vigente_desde"):
        vigentes.setdefault(documento.tipo, documento)
    return list(vigentes.values())


def pendientes(usuario):
    aceptados = set(Consentimiento.objects.filter(usuario=usuario).values_list("documento_id", flat=True))
    return [d for d in documentos_vigentes() if d.pk not in aceptados]


def registrar_aceptacion(usuario, request=None):
    """Registra que `usuario` aceptó todos los documentos vigentes (con fecha e IP)."""
    documentos = pendientes(usuario)
    for documento in documentos:
        Consentimiento.objects.get_or_create(usuario=usuario, documento=documento, defaults={"ip": ip_de(request)})
    if documentos:
        registrar(Accion.CONSENTIMIENTO, request=request, usuario=usuario,
                  detalle=", ".join(str(d) for d in documentos))
    if request is not None:
        request.session.pop(SESION_CONSENTIMIENTO, None)


class ConsentimientoMiddleware:
    """Pide aceptar los documentos vigentes antes de seguir usando la app.

    Quedan libres las páginas necesarias para aceptar, leer los documentos,
    cerrar sesión o ejercer los derechos de la Ley 19.628 (descargar los
    datos y eliminar la cuenta), además del administrador.
    """

    RUTAS_LIBRES = ("/static/", "/admin/", "/legal/")
    VISTAS_LIBRES = {
        "accounts:aceptar_terminos", "accounts:logout", "accounts:exportar_datos", "accounts:eliminar_cuenta",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.path.startswith(self.RUTAS_LIBRES):
            vigentes = sorted(d.pk for d in documentos_vigentes())
            if request.session.get(SESION_CONSENTIMIENTO) != vigentes:
                if pendientes(request.user):
                    if not self._vista_libre(request):
                        return redirect(f"{reverse('accounts:aceptar_terminos')}?next={request.get_full_path()}")
                else:
                    request.session[SESION_CONSENTIMIENTO] = vigentes
        return self.get_response(request)

    def _vista_libre(self, request):
        from django.urls import Resolver404, resolve

        try:
            return resolve(request.path_info).view_name in self.VISTAS_LIBRES
        except Resolver404:
            return True
