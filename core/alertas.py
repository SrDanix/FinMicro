"""
RF-24: reglas de alertas y su registro.

Las reglas son funciones puras con pruebas unitarias; `registrar` y las
funciones `revisar_*` las aplican sobre la base. Se llaman al registrar
un movimiento (límite del plan, gasto inusual) y una vez al día desde el
comando `generar_alertas` (vencimientos). El panel también actualiza los
vencimientos al abrirse, para no depender solo de la tarea programada.
"""
from datetime import timedelta
from decimal import Decimal
from statistics import median

from django.urls import reverse

from .models import Alerta

DIAS_ANTICIPACION_VENCIMIENTO = 7
UMBRAL_AVISO_PLAN = Decimal("0.8")
FACTOR_GASTO_INUSUAL = Decimal("2")
MINIMO_HISTORIAL_GASTO = 3
HISTORIAL_GASTO = 12


# ---------- Reglas puras ----------

def regla_vencimiento(obligacion, hoy, dias_anticipacion=DIAS_ANTICIPACION_VENCIMIENTO):
    """(severidad, mensaje) si la obligación vence dentro de `dias_anticipacion` días."""
    faltan = (obligacion.vence - hoy).days
    if not 0 <= faltan <= dias_anticipacion:
        return None
    cuando = "hoy" if faltan == 0 else "mañana" if faltan == 1 else f"en {faltan} días"
    severidad = Alerta.Severidad.URGENTE if faltan <= 1 else Alerta.Severidad.AVISO
    return severidad, (
        f"{obligacion.descripcion} de {obligacion.periodo} vence {cuando} "
        f"({obligacion.vence:%d-%m-%Y})."
    )


def regla_limite_plan(cantidad_mes, limite):
    """(sufijo, severidad, mensaje) al 80 % y al 100 % del límite mensual. `limite=None` = sin límite."""
    if not limite:
        return None
    if cantidad_mes >= limite:
        return "100", Alerta.Severidad.URGENTE, (
            f"Llegaste al límite de {limite} movimientos de tu plan este mes. "
            "Sube a Premium para seguir registrando."
        )
    if cantidad_mes >= limite * UMBRAL_AVISO_PLAN:
        return "80", Alerta.Severidad.AVISO, f"Llevas {cantidad_mes} de {limite} movimientos de tu plan este mes."
    return None


def regla_gasto_inusual(monto, historial, categoria=""):
    """Mensaje si `monto` supera el doble de la mediana de los gastos anteriores de la categoría.

    Se usa la mediana y no el promedio para que un único gasto grande
    anterior no vuelva "normales" los gastos altos. Sin al menos tres
    gastos previos no se alerta, para no generar ruido en cuentas nuevas.
    """
    if len(historial) < MINIMO_HISTORIAL_GASTO:
        return None
    habitual = Decimal(median(Decimal(h) for h in historial))
    monto = Decimal(monto)
    if habitual <= 0 or monto <= habitual * FACTOR_GASTO_INUSUAL:
        return None
    veces = (monto / habitual).quantize(Decimal("0.1"))
    donde = f" en {categoria}" if categoria else ""
    return f"Tu gasto{donde} de ${monto:,.0f} es {veces} veces lo habitual.".replace(",", ".")


# ---------- Registro en la base ----------

def registrar(negocio, codigo, severidad, mensaje, enlace=""):
    """Crea la alerta si no existe. Devuelve (alerta, creada)."""
    return Alerta.objects.get_or_create(
        negocio=negocio, codigo=codigo,
        defaults={"severidad": severidad, "mensaje": mensaje, "enlace": enlace},
    )


def revisar_vencimientos(negocio, hoy):
    from taxes.calendario import obligaciones_del_negocio

    nuevas = []
    for obligacion in obligaciones_del_negocio(negocio, hoy, hoy + timedelta(days=DIAS_ANTICIPACION_VENCIMIENTO)):
        resultado = regla_vencimiento(obligacion, hoy)
        if resultado:
            alerta, creada = registrar(
                negocio, f"VENC-{obligacion.codigo}-{obligacion.clave_periodo}", *resultado,
                enlace=reverse("taxes:calendario"),
            )
            if creada:
                nuevas.append(alerta)
    return nuevas


def revisar_limite_plan(negocio, hoy):
    from finances.models import Movimiento

    suscripcion = negocio.suscripcion_activa
    limite = suscripcion.plan.limite_movimientos_mensuales if suscripcion else None
    cantidad = Movimiento.objects.filter(usuario=negocio, fecha__year=hoy.year, fecha__month=hoy.month).count()
    resultado = regla_limite_plan(cantidad, limite)
    if resultado:
        sufijo, severidad, mensaje = resultado
        registrar(negocio, f"PLAN-{sufijo}-{hoy:%Y-%m}", severidad, mensaje, enlace=reverse("subscriptions:planes"))


def revisar_gasto(movimiento):
    from finances.models import Categoria, Movimiento

    if movimiento.tipo != Categoria.Tipo.GASTO:
        return
    historial = list(
        Movimiento.objects.filter(usuario=movimiento.usuario, categoria=movimiento.categoria, tipo=Categoria.Tipo.GASTO)
        .exclude(pk=movimiento.pk)
        .order_by("-fecha", "-creado_en")
        .values_list("monto", flat=True)[:HISTORIAL_GASTO]
    )
    mensaje = regla_gasto_inusual(movimiento.monto, historial, movimiento.categoria.nombre)
    if mensaje:
        registrar(
            movimiento.usuario, f"GASTO-{movimiento.pk}", Alerta.Severidad.INFO, mensaje,
            enlace=reverse("finances:editar_movimiento", args=[movimiento.pk]),
        )


def revisar_movimiento(movimiento, hoy):
    revisar_limite_plan(movimiento.usuario, hoy)
    revisar_gasto(movimiento)
