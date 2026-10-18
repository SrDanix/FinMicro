"""Contexto disponible en todas las plantillas (navbar, avisos de plan)."""


def datos_de_cuenta(request):
    if not request.user.is_authenticated:
        return {}
    suscripcion = request.user.suscripcion_activa
    return {
        "suscripcion_activa": suscripcion,
        "plan_actual": suscripcion.plan if suscripcion else None,
        "es_premium": request.user.es_premium,
    }