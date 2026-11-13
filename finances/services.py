"""
Cálculos financieros del negocio: búsqueda (RF-10), costos fijos y
variables (RF-19), margen, punto de equilibrio y ticket promedio (RF-17)
y flujo de caja mensual (RF-16).

Las funciones puras (sin base de datos) van primero y tienen pruebas
unitarias con valores calculados a mano; las consultas a la base quedan
al final y siempre filtran por el negocio que reciben (RNF-03).
"""
import unicodedata
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Count, Q, Sum

from .models import Categoria, Movimiento

CERO = Decimal("0")


def _redondear_clp(monto) -> Decimal:
    return Decimal(monto).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


# ---------- RF-10: búsqueda por texto ----------

def normalizar_texto(texto) -> str:
    """Minúsculas y sin tildes: "Café" y "cafe" se consideran iguales."""
    sin_tildes = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return sin_tildes.casefold().strip()


def buscar_por_texto(movimientos, texto):
    """Filtra `movimientos` por `texto` en la descripción o la categoría.

    SQLite no tiene una forma portable de comparar sin tildes, así que la
    comparación se hace en Python sobre los movimientos ya filtrados por
    negocio: un microempresario tiene a lo más algunos miles de registros.
    """
    buscado = normalizar_texto(texto)
    if not buscado:
        return movimientos
    ids = [
        pk
        for pk, descripcion, categoria in movimientos.values_list("pk", "descripcion", "categoria__nombre")
        if buscado in normalizar_texto(descripcion) or buscado in normalizar_texto(categoria)
    ]
    return movimientos.filter(pk__in=ids)


# ---------- RF-19: costos fijos y variables ----------

@dataclass(frozen=True)
class DesgloseCostos:
    fijos: Decimal
    variables: Decimal
    sin_clasificar: Decimal

    @property
    def total(self) -> Decimal:
        return self.fijos + self.variables + self.sin_clasificar

    def porcentaje(self, monto) -> int | None:
        if not self.total:
            return None
        return int(_redondear_clp(Decimal(monto) * 100 / self.total))

    @property
    def porcentaje_fijos(self):
        return self.porcentaje(self.fijos)

    @property
    def porcentaje_variables(self):
        return self.porcentaje(self.variables)

    @property
    def porcentaje_sin_clasificar(self):
        return self.porcentaje(self.sin_clasificar)


def clasificar_costos(gastos) -> DesgloseCostos:
    """`gastos` = pares (monto, naturaleza) con naturaleza "fijo", "variable" o vacía."""
    fijos = variables = otros = CERO
    for monto, naturaleza in gastos:
        monto = Decimal(monto)
        if naturaleza == Categoria.Naturaleza.FIJO:
            fijos += monto
        elif naturaleza == Categoria.Naturaleza.VARIABLE:
            variables += monto
        else:
            otros += monto
    return DesgloseCostos(fijos, variables, otros)


# ---------- RF-17: margen, punto de equilibrio y ticket promedio ----------

def margen_bruto(ventas, costo_ventas):
    """(margen en pesos, margen como porcentaje de las ventas o None si no hay ventas).

    El costo de ventas es el gasto variable del período: lo que cuesta
    producir o comprar lo que se vendió (supuesto a validar con la asesoría
    contable, actividad X-12).
    """
    ventas, costo_ventas = Decimal(ventas), Decimal(costo_ventas)
    margen = ventas - costo_ventas
    porcentaje = None if not ventas else (margen * 100 / ventas).quantize(Decimal("0.1"), ROUND_HALF_UP)
    return margen, porcentaje


def punto_equilibrio(ventas, costos_variables, costos_fijos):
    """Ventas necesarias para cubrir los costos fijos del período.

    PE = costos fijos / (1 − costos variables / ventas). Devuelve None
    cuando no hay ventas o el margen de contribución no es positivo: en
    ese caso ningún nivel de ventas alcanza el equilibrio.
    """
    ventas = Decimal(ventas)
    if ventas <= 0:
        return None
    contribucion = Decimal("1") - Decimal(costos_variables) / ventas
    if contribucion <= 0:
        return None
    return _redondear_clp(Decimal(costos_fijos) / contribucion)


def ticket_promedio(ventas, cantidad_ventas):
    if not cantidad_ventas:
        return None
    return _redondear_clp(Decimal(ventas) / cantidad_ventas)


# ---------- RF-16: flujo de caja ----------

@dataclass(frozen=True)
class FlujoCaja:
    mes: date
    saldo_inicial: Decimal
    entradas: Decimal
    salidas: Decimal
    proyectado: Decimal | None = None

    @property
    def flujo_neto(self) -> Decimal:
        return self.entradas - self.salidas

    @property
    def saldo_final(self) -> Decimal:
        return self.saldo_inicial + self.flujo_neto

    @property
    def diferencia_con_proyeccion(self) -> Decimal | None:
        """Entradas reales menos las proyectadas (positivo = vendiste más de lo esperado)."""
        return None if self.proyectado is None else self.entradas - self.proyectado

    @property
    def diferencia_absoluta(self) -> Decimal | None:
        diferencia = self.diferencia_con_proyeccion
        return None if diferencia is None else abs(diferencia)


# ---------- Consultas a la base ----------

def _totales(qs):
    fila = qs.aggregate(
        ingresos=Sum("monto", filter=Q(tipo=Categoria.Tipo.INGRESO)),
        gastos=Sum("monto", filter=Q(tipo=Categoria.Tipo.GASTO)),
    )
    return fila["ingresos"] or CERO, fila["gastos"] or CERO


def movimientos_del_mes(negocio, mes: date):
    return Movimiento.objects.filter(usuario=negocio, fecha__year=mes.year, fecha__month=mes.month)


def desglose_costos_del_mes(negocio, mes: date) -> DesgloseCostos:
    gastos = (
        movimientos_del_mes(negocio, mes)
        .filter(tipo=Categoria.Tipo.GASTO)
        .values_list("monto", "categoria__naturaleza")
    )
    return clasificar_costos(gastos)


def indicadores_del_mes(negocio, mes: date) -> dict:
    """RF-17 y RF-19 para el mes de `mes`."""
    movimientos = movimientos_del_mes(negocio, mes)
    ventas = movimientos.filter(tipo=Categoria.Tipo.INGRESO).aggregate(
        total=Sum("monto"), cantidad=Count("id")
    )
    total_ventas = ventas["total"] or CERO
    costos = desglose_costos_del_mes(negocio, mes)
    margen, margen_pct = margen_bruto(total_ventas, costos.variables)
    return {
        "ventas": total_ventas,
        "cantidad_ventas": ventas["cantidad"],
        "costos": costos,
        "margen_bruto": margen,
        "margen_porcentaje": margen_pct,
        "punto_equilibrio": punto_equilibrio(total_ventas, costos.variables, costos.fijos),
        "ticket_promedio": ticket_promedio(total_ventas, ventas["cantidad"]),
        "utilidad": total_ventas - costos.total,
    }


def flujo_de_caja(negocio, mes: date, con_proyeccion=True) -> FlujoCaja:
    """Saldo inicial = caja declarada al empezar + todo lo registrado antes de `mes`."""
    from projections.historial import ingreso_proyectado

    mes = mes.replace(day=1)
    anteriores = Movimiento.objects.filter(usuario=negocio, fecha__lt=mes)
    ingresos_previos, gastos_previos = _totales(anteriores)
    entradas, salidas = _totales(movimientos_del_mes(negocio, mes))
    return FlujoCaja(
        mes=mes,
        saldo_inicial=Decimal(negocio.saldo_caja_inicial) + ingresos_previos - gastos_previos,
        entradas=entradas,
        salidas=salidas,
        proyectado=ingreso_proyectado(negocio, mes) if con_proyeccion else None,
    )


def flujo_de_caja_ultimos_meses(negocio, hasta: date, meses=6) -> list[FlujoCaja]:
    """Los últimos `meses` (incluido `hasta`), del más antiguo al más reciente."""
    hasta = hasta.replace(day=1)
    return [flujo_de_caja(negocio, hasta - relativedelta(months=i)) for i in range(meses - 1, -1, -1)]
