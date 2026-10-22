"""Contexto disponible en todas las plantillas (navbar, avisos de plan)."""
from accounts.models import Colaboracion
from accounts.negocio import ROL_PROPIETARIO, negocios_disponibles, puede_editar


def datos_de_cuenta(request):
    if not request.user.is_authenticated:
        return {}
    # Plan y permisos se evalúan sobre el negocio activo (puede ser el de
    # otra persona si el usuario entró como colaborador).
    negocio = getattr(request, "negocio", None) or request.user
    suscripcion = negocio.suscripcion_activa
    return {
        "negocio": negocio,
        "rol_negocio": getattr(request, "rol_negocio", ROL_PROPIETARIO),
        "es_negocio_propio": negocio.pk == request.user.pk,
        "puede_editar": puede_editar(request) if hasattr(request, "rol_negocio") else True,
        "negocios_disponibles": negocios_disponibles(request.user),
        "invitaciones_pendientes": Colaboracion.objects.filter(
            email__iexact=request.user.email, estado=Colaboracion.Estado.PENDIENTE
        ).count(),
        "suscripcion_activa": suscripcion,
        "plan_actual": suscripcion.plan if suscripcion else None,
        "es_premium": negocio.es_premium,
    }
