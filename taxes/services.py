"""
Calculadora de impuestos para microempresarios: IVA y retención de
boletas de honorarios.

Referencia directa en el informe: Sección III (PESTEL, factor
ECONÓMICO) — "Automatización de cálculos de IVA y honorarios" es uno de
los factores que valida el modelo de pricing de FinMicro.

IMPORTANTE (no es asesoría tributaria): estas funciones son una
calculadora de apoyo. Las tasas vigentes se leen de la tabla
`TasaTributaria` (RF-25, editable en el administrador); las constantes
de este archivo son el respaldo legal conocido y se usan solo si la
tabla no tiene una tasa para la fecha. Antes de declarar, el usuario
final debe validar el resultado en sii.cl o con un contador.
"""
import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum

logger = logging.getLogger(__name__)

TASA_IVA = Decimal("0.19")  # 19% — tasa estándar de IVA en Chile, estable hace décadas.

# Retención de 2ª categoría sobre boletas de honorarios (Art. 74 N°2 LIR),
# subiendo gradualmente según la Ley 21.133 hasta el 17% en 2028.
# Fuente: SII (sii.cl/destacados/boletas_honorarios), consultado 2026.
TABLA_RETENCION_HONORARIOS = {
    2025: Decimal("0.145"),
    2026: Decimal("0.1525"),
    2027: Decimal("0.16"),
    2028: Decimal("0.17"),
}
_ULTIMO_ANIO_TABLA = max(TABLA_RETENCION_HONORARIOS)


def _redondear_clp(monto: Decimal) -> Decimal:
    """Los montos en CLP se manejan sin decimales (no existen centavos de peso)."""
    return monto.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def tasa_retencion_honorarios(anio: int) -> Decimal:
    """Tasa vigente para `anio`. Si `anio` es posterior al último año

    conocido en la tabla, se usa la tasa tope (17%) como aproximación,
    ya que la Ley 21.133 no contempla alzas posteriores a 2028.
    """
    if anio in TABLA_RETENCION_HONORARIOS:
        return TABLA_RETENCION_HONORARIOS[anio]
    if anio > _ULTIMO_ANIO_TABLA:
        return TABLA_RETENCION_HONORARIOS[_ULTIMO_ANIO_TABLA]
    # Años anteriores a 2025 no están tabulados; se usa la tasa más antigua
    # disponible como aproximación conservadora.
    return TABLA_RETENCION_HONORARIOS[min(TABLA_RETENCION_HONORARIOS)]


def tasa_vigente(codigo: str, fecha: date) -> Decimal:
    """RF-25: tasa de la tabla `TasaTributaria` aplicable a `fecha`.

    Si dos vigencias se solapan gana la de inicio más reciente, así que
    registrar una tasa nueva no obliga a cerrar a mano la anterior.
    """
    from .models import TasaTributaria

    tasa = (
        TasaTributaria.objects.filter(codigo=codigo, vigente_desde__lte=fecha)
        .filter(Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gte=fecha))
        .order_by("-vigente_desde")
        .first()
    )
    if tasa is None and codigo == TasaTributaria.Codigo.RETENCION_HONORARIOS:
        # Años anteriores a la tabla: la tasa más antigua registrada.
        tasa = TasaTributaria.objects.filter(codigo=codigo).order_by("vigente_desde").first()
    if tasa is not None:
        return tasa.valor
    logger.warning("Sin tasa %s vigente al %s en la tabla; se usa el valor del código.", codigo, fecha)
    if codigo == TasaTributaria.Codigo.IVA:
        return TASA_IVA
    return tasa_retencion_honorarios(fecha.year)


def calcular_iva(ventas_netas: Decimal, compras_netas: Decimal, tasa: Decimal = TASA_IVA) -> dict:
    """IVA a pagar (o remanente a favor) de un período.

    IVA Débito = IVA cobrado en ventas. IVA Crédito = IVA pagado en
    compras/insumos. Si el crédito supera al débito, el resultado es un
    remanente a favor del contribuyente (no un pago).
    """
    ventas_netas = Decimal(ventas_netas)
    compras_netas = Decimal(compras_netas)

    iva_debito = _redondear_clp(ventas_netas * tasa)
    iva_credito = _redondear_clp(compras_netas * tasa)
    diferencia = iva_debito - iva_credito

    return {
        "ventas_netas": ventas_netas,
        "compras_netas": compras_netas,
        "tasa_iva": tasa,
        "iva_debito": iva_debito,
        "iva_credito": iva_credito,
        "resultado": abs(diferencia),
        "a_pagar": diferencia > 0,
        "remanente": diferencia < 0,
    }


def calcular_honorarios_desde_bruto(monto_bruto: Decimal, anio: int, tasa: Decimal | None = None) -> dict:
    """A partir del monto bruto de la boleta, calcula retención y líquido."""
    monto_bruto = Decimal(monto_bruto)
    tasa = tasa if tasa is not None else tasa_retencion_honorarios(anio)
    retencion = _redondear_clp(monto_bruto * tasa)
    liquido = monto_bruto - retencion

    return {
        "anio": anio,
        "tasa": tasa,
        "tasa_porcentaje": tasa * 100,
        "monto_bruto": monto_bruto,
        "retencion": retencion,
        "monto_liquido": liquido,
    }


def calcular_honorarios_desde_liquido(monto_liquido: Decimal, anio: int, tasa: Decimal | None = None) -> dict:
    """Caso inverso: 'necesito recibir $X líquidos, ¿por cuánto emito la boleta?'

    bruto = líquido / (1 - tasa)
    """
    monto_liquido = Decimal(monto_liquido)
    tasa = tasa if tasa is not None else tasa_retencion_honorarios(anio)
    monto_bruto = _redondear_clp(monto_liquido / (Decimal("1") - tasa))
    retencion = monto_bruto - monto_liquido

    return {
        "anio": anio,
        "tasa": tasa,
        "tasa_porcentaje": tasa * 100,
        "monto_bruto": monto_bruto,
        "retencion": retencion,
        "monto_liquido": monto_liquido,
    }

# ---------- RF-22: IVA del mes a partir de los movimientos ----------

def iva_desde_montos_brutos(ventas_brutas, compras_brutas, tasa: Decimal, remanente_anterior=0) -> dict:
    """IVA del período cuando los montos registrados incluyen IVA.

    Supuestos (validar con la asesoría contable, actividad X-12): el
    microempresario registra lo que cobra y lo que paga, es decir, montos
    brutos; solo generan débito las ventas en categorías afectas y solo
    generan crédito las compras afectas (se asume que tienen factura). Se
    redondea una sola vez, sobre el total del período. El remanente de
    meses anteriores se descuenta sin reajuste por UTM.
    """
    ventas_brutas, compras_brutas = Decimal(ventas_brutas), Decimal(compras_brutas)
    remanente_anterior = Decimal(remanente_anterior)
    divisor = Decimal("1") + tasa
    ventas_netas = _redondear_clp(ventas_brutas / divisor)
    compras_netas = _redondear_clp(compras_brutas / divisor)
    debito = ventas_brutas - ventas_netas
    credito = compras_brutas - compras_netas
    saldo = debito - credito - remanente_anterior
    return {
        "tasa": tasa,
        "ventas_brutas": ventas_brutas,
        "compras_brutas": compras_brutas,
        "ventas_netas": ventas_netas,
        "compras_netas": compras_netas,
        "iva_debito": debito,
        "iva_credito": credito,
        "remanente_anterior": remanente_anterior,
        "iva_a_pagar": max(saldo, Decimal("0")),
        "remanente_siguiente": max(-saldo, Decimal("0")),
    }


def _totales_afectos(negocio, mes: date):
    from finances.models import Categoria, Movimiento

    afectos = Movimiento.objects.filter(
        usuario=negocio, fecha__year=mes.year, fecha__month=mes.month, categoria__es_gravable_iva=True
    ).exclude(producto__afecto_iva=False)
    totales = afectos.aggregate(
        ventas=Sum("monto", filter=Q(tipo=Categoria.Tipo.INGRESO)),
        compras=Sum("monto", filter=Q(tipo=Categoria.Tipo.GASTO)),
    )
    return totales["ventas"] or Decimal("0"), totales["compras"] or Decimal("0")


def iva_del_mes(negocio, mes: date, meses_de_arrastre: int = 12) -> dict:
    """IVA de `mes` con el remanente que arrastran los `meses_de_arrastre` anteriores."""
    mes = mes.replace(day=1)
    remanente = Decimal("0")
    for i in range(meses_de_arrastre, 0, -1):
        anterior = mes - relativedelta(months=i)
        ventas, compras = _totales_afectos(negocio, anterior)
        if ventas or compras or remanente:
            remanente = iva_desde_montos_brutos(
                ventas, compras, tasa_vigente("IVA", anterior), remanente
            )["remanente_siguiente"]
    ventas, compras = _totales_afectos(negocio, mes)
    resultado = iva_desde_montos_brutos(ventas, compras, tasa_vigente("IVA", mes), remanente)
    resultado["mes"] = mes
    return resultado
