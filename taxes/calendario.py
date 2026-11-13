"""
RF-23: calendario tributario según el régimen del usuario.

Reglas implementadas (VALIDAR con la asesoría contable, actividad X-12):

- F29 (IVA y pagos provisionales mensuales): vence el día 12 del mes
  siguiente al período, o el día 20 para quien emite documentos
  electrónicos y declara por internet. Se asume que quien está afecto a
  IVA emite documentos electrónicos (obligatorio para todos los
  contribuyentes de IVA desde 2018).
- F22 (Operación Renta): vence el 30 de abril del año tributario.
- Si un vencimiento cae en sábado, domingo o feriado (tabla `Feriado`,
  editable en el administrador), se corre al día hábil siguiente.

Quién declara qué:

- Sin inicio de actividades: ninguna obligación (solo se recomienda
  formalizarse).
- F29: quien está afecto a IVA, y los regímenes Pro Pyme y general aunque
  no lo estén, porque pagan pagos provisionales mensuales (PPM).
- F22: todo contribuyente con inicio de actividades o que emite boletas
  de honorarios.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

DIA_F29_GENERAL = 12
DIA_F29_ELECTRONICO = 20
MES_DIA_F22 = (4, 30)

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


@dataclass(frozen=True)
class Obligacion:
    codigo: str          # F29 | F22
    descripcion: str
    periodo: str         # "octubre 2026" o "Año tributario 2027"
    clave_periodo: str   # "2026-10" o "AT2027" (para identificar alertas)
    vence: date

    def dias_restantes(self, hoy: date) -> int:
        return (self.vence - hoy).days


def siguiente_dia_habil(fecha: date, feriados=()) -> date:
    while fecha.weekday() >= 5 or fecha in feriados:
        fecha += timedelta(days=1)
    return fecha


def vencimiento_f29(anio: int, mes: int, *, electronico: bool, feriados=()) -> date:
    siguiente = date(anio, mes, 1) + relativedelta(months=1)
    dia = DIA_F29_ELECTRONICO if electronico else DIA_F29_GENERAL
    return siguiente_dia_habil(siguiente.replace(day=dia), feriados)


def vencimiento_f22(anio_tributario: int, feriados=()) -> date:
    mes, dia = MES_DIA_F22
    return siguiente_dia_habil(date(anio_tributario, mes, dia), feriados)


def declara_f29(regimen: str, afecto_iva: bool) -> bool:
    return afecto_iva or regimen in ("PP", "PT", "RG")


def declara_f22(regimen: str, emite_boletas_honorarios: bool) -> bool:
    return regimen != "SI" or emite_boletas_honorarios


def obligaciones(*, regimen: str, afecto_iva: bool, emite_boletas_honorarios: bool,
                 desde: date, hasta: date, feriados=()) -> list[Obligacion]:
    """Obligaciones que vencen entre `desde` y `hasta` (ambos incluidos), ordenadas por fecha."""
    salida = []
    if declara_f29(regimen, afecto_iva):
        # Un período vence el mes siguiente: se parte un mes antes de `desde`.
        periodo = desde.replace(day=1) - relativedelta(months=1)
        while periodo <= hasta:
            vence = vencimiento_f29(periodo.year, periodo.month, electronico=afecto_iva, feriados=feriados)
            if desde <= vence <= hasta:
                salida.append(Obligacion(
                    "F29", "Declaración mensual de IVA y PPM (F29)",
                    f"{MESES[periodo.month - 1]} {periodo.year}", f"{periodo:%Y-%m}", vence,
                ))
            periodo += relativedelta(months=1)
    if declara_f22(regimen, emite_boletas_honorarios):
        for anio in range(desde.year, hasta.year + 1):
            vence = vencimiento_f22(anio, feriados)
            if desde <= vence <= hasta:
                salida.append(Obligacion(
                    "F22", "Declaración anual de renta (F22, Operación Renta)",
                    f"Año tributario {anio}", f"AT{anio}", vence,
                ))
    return sorted(salida, key=lambda o: o.vence)


def obligaciones_del_negocio(negocio, desde: date, hasta: date) -> list[Obligacion]:
    from .models import Feriado

    feriados = set(Feriado.objects.filter(fecha__range=(desde, hasta + timedelta(days=15)))
                   .values_list("fecha", flat=True))
    return obligaciones(
        regimen=negocio.regimen_tributario,
        afecto_iva=negocio.afecto_iva,
        emite_boletas_honorarios=negocio.emite_boletas_honorarios,
        desde=desde, hasta=hasta, feriados=feriados,
    )
