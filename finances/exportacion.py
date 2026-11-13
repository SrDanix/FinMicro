"""
RF-31: exportación de movimientos a Excel (.xlsx) y CSV.

Un texto que empieza con = + - @ se antepone con comilla simple para que
Excel no lo interprete como fórmula (inyección de fórmulas en CSV).
"""
import csv
import io
from datetime import date
from decimal import Decimal

COLUMNAS = ("Fecha", "Tipo", "Categoría", "Producto", "Cantidad", "Monto", "Descripción")
_PELIGROSOS = ("=", "+", "-", "@", "\t", "\r")


def neutralizar(valor):
    if isinstance(valor, str) and valor.startswith(_PELIGROSOS):
        return "'" + valor
    return valor


def filas_de(movimientos):
    for m in movimientos.select_related("categoria", "producto").order_by("fecha", "pk"):
        yield (m.fecha, m.get_tipo_display(), m.categoria.nombre, m.producto.nombre if m.producto else "",
               m.cantidad, m.monto, m.descripcion)


def a_csv(filas) -> bytes:
    """CSV separado por ';' con BOM UTF-8, que Excel en español abre directamente."""
    salida = io.StringIO()
    escritor = csv.writer(salida, delimiter=";", lineterminator="\r\n")
    escritor.writerow(COLUMNAS)
    for fila in filas:
        escritor.writerow([_celda_csv(v) for v in fila])
    return ("﻿" + salida.getvalue()).encode("utf-8")


def _celda_csv(valor):
    if valor is None:
        return ""
    if isinstance(valor, date):
        return valor.strftime("%d-%m-%Y")
    if isinstance(valor, Decimal):
        return str(int(valor)) if valor == valor.to_integral_value() else str(valor)
    return str(neutralizar(valor))


def a_xlsx(filas, titulo="Movimientos") -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    libro = Workbook()
    hoja = libro.active
    hoja.title = titulo[:31]
    hoja.append(COLUMNAS)
    for celda in hoja[1]:
        celda.font = Font(bold=True)
    for fila in filas:
        valores = []
        for valor in fila:
            if isinstance(valor, Decimal):
                valor = int(valor) if valor == valor.to_integral_value() else float(valor)
            valores.append(neutralizar(valor))
        hoja.append(valores)
    for celda in hoja["A"][1:]:
        celda.number_format = "DD-MM-YYYY"
    for celda in hoja["F"][1:]:
        celda.number_format = "#,##0"
    for columna, ancho in zip("ABCDEFG", (12, 10, 24, 22, 10, 14, 40)):
        hoja.column_dimensions[columna].width = ancho
    hoja.freeze_panes = "A2"
    buffer = io.BytesIO()
    libro.save(buffer)
    return buffer.getvalue()


def plantilla_csv() -> bytes:
    filas = [("fecha", "tipo", "monto", "categoria", "descripcion"),
             ("05/11/2026", "ingreso", "15000", "Ventas", "Venta del día"),
             ("06/11/2026", "gasto", "8500", "Mercadería / insumos", "Compra de harina")]
    salida = io.StringIO()
    csv.writer(salida, delimiter=";", lineterminator="\r\n").writerows(filas)
    return ("﻿" + salida.getvalue()).encode("utf-8")
