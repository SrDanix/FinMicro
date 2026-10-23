"""
Negocio activo de cada request (RF-06, colaboradores).

Todas las vistas de datos (finanzas, impuestos, proyecciones) trabajan
sobre `request.negocio` en vez de `request.user`. Normalmente son el
mismo usuario; cuando un colaborador elige el negocio de otra persona,
`request.negocio` es el dueño de ese negocio y `request.rol_negocio`
indica qué puede hacer ahí.
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import Colaboracion

SESION_NEGOCIO = "negocio_id"
ROL_PROPIETARIO = "propietario"


def negocios_disponibles(usuario):
    """[(usuario_dueño, rol)] que el usuario puede abrir, partiendo por el propio."""
    propios = [(usuario, ROL_PROPIETARIO)]
    ajenos = [
        (c.propietario, c.rol)
        for c in Colaboracion.objects.filter(
            colaborador=usuario, estado=Colaboracion.Estado.ACEPTADA
        ).select_related("propietario")
    ]
    return propios + ajenos


class NegocioActivoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.negocio = None
        request.rol_negocio = None
        if request.user.is_authenticated:
            request.negocio = request.user
            request.rol_negocio = ROL_PROPIETARIO
            negocio_id = request.session.get(SESION_NEGOCIO)
            if negocio_id and negocio_id != request.user.pk:
                colaboracion = (
                    Colaboracion.objects.select_related("propietario")
                    .filter(
                        colaborador=request.user,
                        propietario_id=negocio_id,
                        estado=Colaboracion.Estado.ACEPTADA,
                    )
                    .first()
                )
                if colaboracion:
                    request.negocio = colaboracion.propietario
                    request.rol_negocio = colaboracion.rol
                else:
                    # El acceso fue revocado: se vuelve al negocio propio.
                    request.session.pop(SESION_NEGOCIO, None)
        return self.get_response(request)


def puede_editar(request) -> bool:
    return request.rol_negocio in (ROL_PROPIETARIO, Colaboracion.Rol.EDITOR)


def requiere_edicion(vista):
    """Bloquea a colaboradores de solo lectura en vistas que modifican datos."""

    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not puede_editar(request):
            messages.error(request, "Tu acceso a este negocio es de solo lectura.")
            return redirect("finances:dashboard")
        return vista(request, *args, **kwargs)

    return envoltura
