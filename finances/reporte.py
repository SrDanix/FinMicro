"""
RF-30: reporte mensual en PDF con el resumen financiero y tributario.

Se arma con reportlab (Python puro, sin dependencias del sistema), así la
imagen Docker no necesita librerías gráficas adicionales.
"""
import io
from datetime import timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Categoria, Movimiento
from .recomendaciones import recomendaciones_del_mes
from .services import flujo_de_caja, indicadores_del_mes

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
         "Septiembre", "Octubre", "Noviembre", "Diciembre"]
VERDE = colors.HexColor("#1b6b4e")
TINTA = colors.HexColor("#14231c")


def _pesos(monto):
    if monto is None:
        return "—"
    return f"${Decimal(monto):,.0f}".replace(",", ".")


def _tabla(filas, anchos, encabezado=True):
    tabla = Table(filas, colWidths=anchos, hAlign="LEFT")
    estilo = [
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#d9e2dc")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if encabezado:
        estilo += [("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("TEXTCOLOR", (0, 0), (-1, 0), VERDE)]
    tabla.setStyle(TableStyle(estilo))
    return tabla


def generar_reporte_mensual(negocio, mes) -> bytes:
    from taxes.calendario import obligaciones_del_negocio
    from taxes.services import iva_del_mes

    mes = mes.replace(day=1)
    datos = indicadores_del_mes(negocio, mes)
    flujo = flujo_de_caja(negocio, mes)
    gastos_mes = (
        Movimiento.objects.filter(usuario=negocio, tipo=Categoria.Tipo.GASTO, fecha__year=mes.year, fecha__month=mes.month)
        .values("categoria__nombre").annotate(total=Sum("monto")).order_by("-total")
    )

    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle("titulo", parent=estilos["Title"], textColor=TINTA, alignment=0, fontSize=18)
    seccion = ParagraphStyle("seccion", parent=estilos["Heading2"], textColor=VERDE, fontSize=12, spaceBefore=12)
    normal = ParagraphStyle("normal", parent=estilos["Normal"], fontSize=9, leading=12)
    nota = ParagraphStyle("nota", parent=normal, textColor=colors.grey, fontSize=8)

    contenido = [
        Paragraph(f"Reporte mensual · {MESES[mes.month - 1]} {mes.year}", titulo),
        Paragraph(f"{negocio.nombre_negocio} · RUT {negocio.rut} · {negocio.get_regimen_tributario_display()}", normal),
        Spacer(1, 8),
        Paragraph("Resumen del mes", seccion),
        _tabla([
            ["Concepto", "Monto"],
            ["Ingresos (ventas)", _pesos(datos["ventas"])],
            ["Gastos", _pesos(datos["costos"].total)],
            ["Resultado", _pesos(datos["utilidad"])],
        ], [9 * cm, 4 * cm]),
        Paragraph("Indicadores", seccion),
        _tabla([
            ["Indicador", "Valor"],
            ["Margen bruto", f"{_pesos(datos['margen_bruto'])}"
                             + (f" ({datos['margen_porcentaje']} %)" if datos["margen_porcentaje"] is not None else "")],
            ["Punto de equilibrio", _pesos(datos["punto_equilibrio"])],
            ["Ticket promedio", f"{_pesos(datos['ticket_promedio'])} ({datos['cantidad_ventas']} ventas)"],
            ["Gastos fijos", f"{_pesos(datos['costos'].fijos)} ({datos['costos'].porcentaje_fijos or 0} %)"],
            ["Gastos variables", f"{_pesos(datos['costos'].variables)} ({datos['costos'].porcentaje_variables or 0} %)"],
            ["Gastos sin clasificar", _pesos(datos["costos"].sin_clasificar)],
        ], [9 * cm, 6 * cm]),
        Paragraph("Flujo de caja", seccion),
        _tabla([
            ["Concepto", "Monto"],
            ["Saldo inicial", _pesos(flujo.saldo_inicial)],
            ["Entradas", _pesos(flujo.entradas)],
            ["Salidas", _pesos(flujo.salidas)],
            ["Saldo final", _pesos(flujo.saldo_final)],
            ["Entradas proyectadas", _pesos(flujo.proyectado)],
        ], [9 * cm, 4 * cm]),
    ]

    if gastos_mes:
        contenido += [Paragraph("Gastos por categoría", seccion),
                      _tabla([["Categoría", "Total"]] + [[g["categoria__nombre"], _pesos(g["total"])] for g in gastos_mes],
                             [9 * cm, 4 * cm])]

    contenido.append(Paragraph("Impuestos", seccion))
    if negocio.afecto_iva:
        iva = iva_del_mes(negocio, mes)
        contenido.append(_tabla([
            ["IVA estimado (montos con IVA incluido)", "Monto"],
            ["IVA débito", _pesos(iva["iva_debito"])],
            ["IVA crédito", _pesos(iva["iva_credito"])],
            ["Remanente de meses anteriores", _pesos(iva["remanente_anterior"])],
            ["IVA a pagar", _pesos(iva["iva_a_pagar"])],
            ["Remanente para el mes siguiente", _pesos(iva["remanente_siguiente"])],
        ], [9 * cm, 4 * cm]))
    else:
        contenido.append(Paragraph("No estás afecto a IVA según tu configuración.", normal))
    inicio = mes + relativedelta(months=1)
    vencimientos = obligaciones_del_negocio(negocio, inicio, inicio + timedelta(days=60))
    if vencimientos:
        contenido += [Spacer(1, 6), _tabla([["Próximos vencimientos", "Fecha"]]
                                           + [[f"{o.codigo} · {o.periodo}", o.vence.strftime("%d-%m-%Y")] for o in vencimientos],
                                           [9 * cm, 4 * cm])]

    recomendaciones = recomendaciones_del_mes(negocio, mes, datos)
    if recomendaciones:
        contenido.append(Paragraph("Recomendaciones", seccion))
        contenido += [Paragraph(f"• {r.mensaje}", normal) for r in recomendaciones]

    contenido += [
        Spacer(1, 16),
        Paragraph("Generado por FinMicro. Las cifras tributarias son estimaciones de apoyo y no reemplazan la "
                  "asesoría de un contador: valídalas en sii.cl antes de declarar.", nota),
    ]

    buffer = io.BytesIO()
    documento = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                                  topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                                  title=f"FinMicro {MESES[mes.month - 1]} {mes.year}", author="FinMicro")
    documento.build(contenido)
    return buffer.getvalue()
