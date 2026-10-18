"""
Calculadora de impuestos para microempresarios: IVA y retención de
boletas de honorarios.

Referencia directa en el informe: Sección III (PESTEL, factor
ECONÓMICO) — "Automatización de cálculos de IVA y honorarios" es uno de
los factores que valida el modelo de pricing de FinMicro.

IMPORTANTE (no es asesoría tributaria): estas funciones son una
calculadora de apoyo con las tasas vigentes conocidas al momento de
escribir este código. Las tasas del SII cambian por ley (ver
TABLA_RETENCION_HONORARIOS) — antes de declarar, el usuario final de la
plataforma debe validar el resultado en sii.cl o con un contador.
"""
from decimal import ROUND_HALF_UP, Decimal

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


def calcular_iva(ventas_netas: Decimal, compras_netas: Decimal) -> dict:
    """IVA a pagar (o remanente a favor) de un período.

    IVA Débito = IVA cobrado en ventas. IVA Crédito = IVA pagado en
    compras/insumos. Si el crédito supera al débito, el resultado es un
    remanente a favor del contribuyente (no un pago).
    """
    ventas_netas = Decimal(ventas_netas)
    compras_netas = Decimal(compras_netas)

    iva_debito = _redondear_clp(ventas_netas * TASA_IVA)
    iva_credito = _redondear_clp(compras_netas * TASA_IVA)
    diferencia = iva_debito - iva_credito

    return {
        "ventas_netas": ventas_netas,
        "compras_netas": compras_netas,
        "tasa_iva": TASA_IVA,
        "iva_debito": iva_debito,
        "iva_credito": iva_credito,
        "resultado": abs(diferencia),
        "a_pagar": diferencia > 0,
        "remanente": diferencia < 0,
    }


def calcular_honorarios_desde_bruto(monto_bruto: Decimal, anio: int) -> dict:
    """A partir del monto bruto de la boleta, calcula retención y líquido."""
    monto_bruto = Decimal(monto_bruto)
    tasa = tasa_retencion_honorarios(anio)
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


def calcular_honorarios_desde_liquido(monto_liquido: Decimal, anio: int) -> dict:
    """Caso inverso: 'necesito recibir $X líquidos, ¿por cuánto emito la boleta?'

    bruto = líquido / (1 - tasa)
    """
    monto_liquido = Decimal(monto_liquido)
    tasa = tasa_retencion_honorarios(anio)
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