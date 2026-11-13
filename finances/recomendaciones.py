"""
RF-38: recomendaciones automáticas a partir de los indicadores del mes.

Son reglas deterministas: mismas cifras, mismas recomendaciones. Cada una
tiene un código para trazarla en las pruebas y en la documentación, y los
umbrales son constantes fáciles de ajustar.
"""
from dataclasses import dataclass
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from .models import Categoria, Movimiento
from .services import indicadores_del_mes

MARGEN_MINIMO = Decimal("20")              # % de las ventas
PESO_MAXIMO_FIJOS = Decimal("0.60")        # costos fijos / ventas
ALZA_GASTO_CATEGORIA = Decimal("1.30")     # +30 % sobre el promedio de los 3 meses anteriores
PESO_MAXIMO_SIN_CLASIFICAR = 30            # % de los gastos


@dataclass(frozen=True)
class Recomendacion:
    codigo: str
    mensaje: str


def _pesos(monto):
    return f"${Decimal(monto):,.0f}".replace(",", ".")


def recomendar(*, ventas, utilidad, margen_porcentaje, costos_fijos, punto_equilibrio,
               porcentaje_sin_clasificar=None, meta_ventas=None, alzas_por_categoria=()):
    """`alzas_por_categoria`: [(categoría, gasto del mes, promedio de los meses anteriores)]."""
    ventas, utilidad, costos_fijos = Decimal(ventas), Decimal(utilidad), Decimal(costos_fijos)
    if ventas == 0:
        return [Recomendacion("R00", "Aún no registras ventas este mes. Regístralas para ver recomendaciones sobre tu negocio.")]
    salida = []
    if utilidad < 0:
        salida.append(Recomendacion("R01", "Este mes gastaste más de lo que vendiste. Revisa tus gastos más altos."))
    if margen_porcentaje is not None and 0 <= margen_porcentaje < MARGEN_MINIMO:
        salida.append(Recomendacion(
            "R02", f"Tu margen es bajo: de cada $100 que vendes te quedan menos de ${MARGEN_MINIMO:.0f}. "
                   "Evalúa tus precios o el costo de tus insumos."))
    if punto_equilibrio is not None and ventas < punto_equilibrio:
        salida.append(Recomendacion(
            "R03", f"Te faltan {_pesos(punto_equilibrio - ventas)} en ventas para cubrir tus costos fijos del mes."))
    if costos_fijos > ventas * PESO_MAXIMO_FIJOS:
        salida.append(Recomendacion(
            "R05", "Tus costos fijos pesan mucho frente a tus ventas. Revisa arriendos, servicios y suscripciones."))
    for categoria, gasto, promedio in alzas_por_categoria:
        salida.append(Recomendacion(
            "R07", f"Tu gasto en {categoria} subió a {_pesos(gasto)}, sobre tu promedio de {_pesos(promedio)}. "
                   "Revisa si es algo puntual."))
    if porcentaje_sin_clasificar is not None and porcentaje_sin_clasificar > PESO_MAXIMO_SIN_CLASIFICAR:
        salida.append(Recomendacion(
            "R08", "Muchos de tus gastos no están clasificados como fijos o variables. "
                   "Usa categorías propias para que tus indicadores sean más precisos."))
    if meta_ventas and ventas >= Decimal(meta_ventas):
        salida.append(Recomendacion("R06", "¡Cumpliste tu meta de ventas del mes!"))
    return salida


def alzas_por_categoria(negocio, mes, meses_previos=3):
    """Categorías de gasto cuyo total del mes supera en 30 % su promedio de los meses anteriores."""
    mes = mes.replace(day=1)
    desde = mes - relativedelta(months=meses_previos)
    gastos = Movimiento.objects.filter(usuario=negocio, tipo=Categoria.Tipo.GASTO, fecha__gte=desde,
                                       fecha__lt=mes + relativedelta(months=1))
    actual, previo = {}, {}
    for nombre, fecha, total in gastos.values_list("categoria__nombre", "fecha__month", "monto"):
        destino = actual if fecha == mes.month else previo
        destino[nombre] = destino.get(nombre, Decimal("0")) + total
    alzas = []
    for nombre, total in sorted(actual.items()):
        promedio = previo.get(nombre, Decimal("0")) / meses_previos
        if promedio > 0 and total > promedio * ALZA_GASTO_CATEGORIA:
            alzas.append((nombre, total, promedio.quantize(Decimal("1"))))
    return alzas


def recomendaciones_del_mes(negocio, mes, indicadores=None):
    datos = indicadores or indicadores_del_mes(negocio, mes)
    return recomendar(
        ventas=datos["ventas"],
        utilidad=datos["utilidad"],
        margen_porcentaje=datos["margen_porcentaje"],
        costos_fijos=datos["costos"].fijos,
        punto_equilibrio=datos["punto_equilibrio"],
        porcentaje_sin_clasificar=datos["costos"].porcentaje_sin_clasificar,
        meta_ventas=negocio.meta_ventas_mensual,
        alzas_por_categoria=alzas_por_categoria(negocio, mes),
    )
