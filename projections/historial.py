"""Consultas del historial de ingresos que usan la proyección (RF-34) y el flujo de caja (RF-16)."""
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django.utils import timezone

from finances.models import Categoria, Movimiento

from .services import proyectar_ingresos


def historial_ingresos_mensuales(usuario, meses=6, mes_referencia=None, tipo=Categoria.Tipo.INGRESO):
    """Totales de `tipo` (ingresos por defecto) de los `meses` anteriores a `mes_referencia`, del más antiguo al más reciente.

    Se recorre mes a mes (en vez de agrupar con TruncMonth) para poder
    incluir explícitamente los meses sin ningún ingreso registrado como
    $0 — la regresión lineal necesita una serie continua, no solo los
    meses que tuvieron movimientos.

    Solo se usan meses completos (termina en el mes anterior a
    `mes_referencia`, por defecto el mes en curso): el mes en curso tiene
    datos parciales y arrastraría la tendencia hacia abajo.
    """
    mes_referencia = (mes_referencia or timezone.localdate()).replace(day=1)
    meses_ref, valores = [], []
    for i in range(meses, 0, -1):
        mes_ref = mes_referencia - relativedelta(months=i)
        total = Movimiento.objects.filter(
            usuario=usuario,
            tipo=tipo,
            fecha__year=mes_ref.year,
            fecha__month=mes_ref.month,
        ).aggregate(t=Sum("monto"))["t"] or 0
        meses_ref.append(mes_ref)
        valores.append(total)
    return meses_ref, valores


def recortar_inicio(historial):
    """RN-12: los meses en $0 antes del primer ingreso son meses en que el

    usuario aún no usaba FinMicro, no meses sin ventas. Devuelve None si no
    hay al menos dos meses con ingresos.
    """
    if sum(1 for v in historial if v > 0) < 2:
        return None
    inicio = next(i for i, v in enumerate(historial) if v > 0)
    return historial[inicio:]


def ingreso_proyectado(usuario, mes):
    """Ingreso que la proyección esperaba para `mes`, con los datos anteriores a ese mes.

    Devuelve None cuando no hay historial suficiente para proyectar.
    """
    _, historial = historial_ingresos_mensuales(usuario, meses=6, mes_referencia=mes)
    serie = recortar_inicio(historial)
    if serie is None:
        return None
    return proyectar_ingresos(serie, meses_futuros=1)[0]
