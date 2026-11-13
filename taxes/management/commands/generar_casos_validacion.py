"""
X-12: genera la planilla de casos para la validación con la asesoría
contable, con los resultados que entrega hoy el código de FinMicro.

Uso: python manage.py generar_casos_validacion docs/validacion_contable/FinMicro_Casos_validacion_contable.xlsx

Las columnas amarillas las completa el contador. Si discrepa en un caso, se
corrige el cálculo, se agrega una prueba con su valor y se vuelve a generar.
"""
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from finances.services import margen_bruto, punto_equilibrio, ticket_promedio
from taxes.calendario import vencimiento_f22, vencimiento_f29
from taxes.models import Feriado, TasaTributaria
from taxes.services import (
    calcular_honorarios_desde_bruto,
    calcular_honorarios_desde_liquido,
    iva_desde_montos_brutos,
    tasa_vigente,
)

VERDE, AMARILLO = "1B6B4E", "FFF2CC"
BORDE = Border(*(Side(style="thin", color="BFBFBF"),) * 4)
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _hoja(libro, titulo, nota, encabezados, filas, anchos):
    hoja = libro.create_sheet(titulo)
    columnas = list(encabezados) + ["Resultado según asesoría", "¿Conforme? (Sí/No)", "Observaciones"]
    hoja["A1"] = nota
    hoja["A1"].font = Font(size=9, italic=True)
    hoja["A1"].alignment = Alignment(wrap_text=True, vertical="top")
    hoja.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(columnas))
    hoja.row_dimensions[1].height = 54
    for i, texto in enumerate(columnas, 1):
        celda = hoja.cell(3, i, texto)
        celda.font = Font(size=9, bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor=VERDE)
        celda.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
        celda.border = BORDE
    for r, fila in enumerate(filas, 4):
        for i in range(1, len(columnas) + 1):
            valor = fila[i - 1] if i <= len(fila) else None
            if isinstance(valor, Decimal):
                valor = int(valor) if valor == valor.to_integral_value() else float(valor)
            celda = hoja.cell(r, i, valor)
            celda.font = Font(size=9)
            celda.alignment = Alignment(wrap_text=True, vertical="center")
            celda.border = BORDE
            if i > len(encabezados):
                celda.fill = PatternFill("solid", fgColor=AMARILLO)
            elif isinstance(valor, int):
                celda.number_format = "#,##0"
            elif isinstance(valor, date):
                celda.number_format = "dd-mm-yyyy"
    for i, ancho in enumerate(list(anchos) + [20, 12, 34], 1):
        hoja.column_dimensions[chr(64 + i)].width = ancho
    hoja.freeze_panes = "A4"


class Command(BaseCommand):
    help = "Genera la planilla de casos de validación contable (X-12) con los cálculos actuales."

    def add_arguments(self, parser):
        parser.add_argument("destino", help="Ruta del archivo .xlsx a crear.")

    def handle(self, *args, destino, **options):
        libro = Workbook()
        libro.remove(libro.active)
        tasa_iva = tasa_vigente(TasaTributaria.Codigo.IVA, date(2026, 10, 1))

        casos_iva = [
            ("IVA-01", "Solo ventas afectas", 1_190_000, 0, 0),
            ("IVA-02", "Ventas y compras afectas", 1_190_000, 595_000, 0),
            ("IVA-03", "Compras superan a las ventas (remanente)", 119_000, 238_000, 0),
            ("IVA-04", "Con remanente del mes anterior", 595_000, 0, 30_000),
            ("IVA-05", "Redondeo al peso: venta de $1.000", 1_000, 0, 0),
            ("IVA-06", "Redondeo al peso: compra de $999", 0, 999, 0),
            ("IVA-07", "Remanente mayor que el débito del mes", 119_000, 0, 50_000),
        ]
        filas = []
        for codigo, caso, ventas, compras, remanente in casos_iva:
            r = iva_desde_montos_brutos(ventas, compras, tasa_iva, remanente)
            filas.append((codigo, caso, ventas, compras, remanente, r["ventas_netas"], r["iva_debito"],
                          r["compras_netas"], r["iva_credito"], r["iva_a_pagar"], r["remanente_siguiente"]))
        _hoja(libro, "IVA automático", (
            f"RF-22 · Tasa {tasa_iva * 100:.0f} %. Supuestos a confirmar: (1) los montos que registra el "
            "microempresario INCLUYEN IVA (neto = bruto / 1,19); (2) solo generan débito/crédito las categorías y "
            "productos marcados como afectos, y las compras tienen factura; (3) se redondea al peso una vez por "
            "período; (4) el remanente se arrastra sin reajuste por UTM."
        ), ("ID", "Caso", "Ventas afectas (brutas)", "Compras afectas (brutas)", "Remanente anterior", "Ventas netas",
            "Débito fiscal", "Compras netas", "Crédito fiscal", "IVA a pagar", "Remanente siguiente"),
            filas, (8, 32, 13, 13, 12, 12, 12, 12, 12, 12, 13))

        filas = []
        for codigo, modo, monto, anio in [("HON-01", "bruto", 1_000_000, 2026), ("HON-02", "bruto", 500_000, 2027),
                                          ("HON-03", "líquido", 847_500, 2026), ("HON-04", "bruto", 1_000_000, 2028),
                                          ("HON-05", "bruto", 333_333, 2026)]:
            tasa = tasa_vigente(TasaTributaria.Codigo.RETENCION_HONORARIOS, date(anio, 1, 1))
            calculo = calcular_honorarios_desde_bruto if modo == "bruto" else calcular_honorarios_desde_liquido
            r = calculo(Decimal(monto), anio, tasa)
            filas.append((codigo, f"Desde monto {modo}", anio, monto, tasa, r["monto_bruto"], r["retencion"], r["monto_liquido"]))
        _hoja(libro, "Honorarios", (
            "RF-21 y RF-25 · Retención de boletas de honorarios según la tabla de tasas (Ley 21.133). "
            "Bruto → retención redondeada al peso; líquido → bruto = líquido / (1 − tasa), redondeado."
        ), ("ID", "Caso", "Año", "Monto ingresado", "Tasa", "Bruto", "Retención", "Líquido"),
            filas, (8, 22, 7, 14, 8, 13, 13, 13))

        feriados = set(Feriado.objects.values_list("fecha", flat=True))
        casos_cal = [("CAL-01", 2026, 9, False), ("CAL-02", 2026, 9, True), ("CAL-03", 2026, 10, False),
                     ("CAL-04", 2026, 10, True), ("CAL-05", 2026, 11, False), ("CAL-06", 2026, 12, True),
                     ("CAL-07", 2027, 6, False)]
        filas = []
        for codigo, anio, mes, electronico in casos_cal:
            vence = vencimiento_f29(anio, mes, electronico=electronico, feriados=feriados)
            filas.append((codigo, f"F29 período {mes:02d}-{anio}", "Sí" if electronico else "No", vence, DIAS[vence.weekday()]))
        for i, anio in enumerate((2027, 2028), 8):
            vence = vencimiento_f22(anio, feriados)
            filas.append((f"CAL-{i:02d}", f"F22 año tributario {anio}", "—", vence, DIAS[vence.weekday()]))
        _hoja(libro, "Calendario", (
            "RF-23 · Reglas a confirmar: F29 vence el día 12 del mes siguiente, o el 20 si el contribuyente está "
            "afecto a IVA y emite documentos electrónicos; F22 el 30 de abril. Si cae en sábado, domingo o feriado "
            "se corre al día hábil siguiente. Feriados cargados: Chile 2026–2027 (revisar la lista en el administrador). "
            "CAL-09 queda el lunes 1 de mayo de 2028 porque aún no se cargan los feriados de 2028: muestra por qué hay "
            "que mantener esa tabla al día."
        ), ("ID", "Obligación", "Afecto a IVA / electrónico", "Vencimiento calculado", "Día"), filas, (8, 26, 14, 14, 11))

        filas = [(f"TAS-{i:02d}", t.get_codigo_display(), t.vigente_desde, t.vigente_hasta or "sin término", t.valor, t.fuente)
                 for i, t in enumerate(TasaTributaria.objects.order_by("codigo", "vigente_desde"), 1)]
        _hoja(libro, "Tasas", (
            "RF-25 · Tasas cargadas en la tabla editable. Confirmar valor, vigencia y fuente. Las tasas de impuesto "
            "de primera categoría no se usan en ningún cálculo de la app, por eso no están cargadas."
        ), ("ID", "Tasa", "Vigente desde", "Vigente hasta", "Valor", "Fuente"), filas, (8, 30, 13, 13, 9, 30))

        filas = []
        for i, (ventas, variables, fijos, cantidad) in enumerate(
            [(1_000_000, 600_000, 300_000, 40), (800_000, 200_000, 450_000, 25),
             (500_000, 500_000, 100_000, 10), (2_500_000, 1_000_000, 900_000, 130)], 1):
            margen, porcentaje = margen_bruto(ventas, variables)
            equilibrio = punto_equilibrio(ventas, variables, fijos)
            filas.append((f"IND-{i:02d}", ventas, variables, fijos, cantidad, margen, porcentaje,
                          equilibrio if equilibrio is not None else "No existe", ticket_promedio(ventas, cantidad)))
        _hoja(libro, "Indicadores", (
            "RF-17 · Definiciones a confirmar: costo de ventas = gastos variables; margen bruto = ventas − gastos "
            "variables; punto de equilibrio = costos fijos / (1 − variables / ventas); ticket promedio = ventas / "
            "número de ventas, redondeado al peso."
        ), ("ID", "Ventas", "Gastos variables", "Costos fijos", "N.º de ventas", "Margen bruto", "Margen %",
            "Punto de equilibrio", "Ticket promedio"), filas, (8, 12, 12, 12, 10, 12, 9, 14, 12))

        libro.save(destino)
        self.stdout.write(self.style.SUCCESS(f"Planilla creada: {destino}"))
