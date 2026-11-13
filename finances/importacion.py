"""
RF-12: importación de movimientos desde Excel (.xlsx) o CSV.

Flujo: leer → validar fila por fila → vista previa con filas aceptadas,
duplicadas y con error → el usuario confirma → se guardan las aceptadas
en una sola transacción. Si alguna fila tiene error o se supera el
límite del plan no se importa nada (HU-12: sin importaciones parciales).
"""
import csv
import io
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

MAX_FILAS = 1000
MAX_BYTES = 2 * 1024 * 1024
COLUMNAS_PLANTILLA = ("fecha", "tipo", "monto", "categoria", "descripcion")
_SINONIMOS = {
    "fecha": "fecha", "dia": "fecha",
    "tipo": "tipo", "movimiento": "tipo",
    "monto": "monto", "valor": "monto", "importe": "monto", "total": "monto",
    "categoria": "categoria", "rubro": "categoria",
    "descripcion": "descripcion", "detalle": "descripcion", "glosa": "descripcion",
}
_TIPOS = {
    "ingreso": "ingreso", "venta": "ingreso", "ingresos": "ingreso",
    "gasto": "gasto", "egreso": "gasto", "compra": "gasto", "gastos": "gasto",
}
_FORMATOS_FECHA = ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y")


class ArchivoInvalido(ValueError):
    """El archivo no se puede leer o no trae las columnas mínimas."""


@dataclass(frozen=True)
class FilaValida:
    numero: int
    fecha: date
    tipo: str
    monto: Decimal
    categoria: str
    descripcion: str

    @property
    def clave(self):
        return (self.fecha, self.tipo, self.monto, self.categoria.casefold(), self.descripcion.casefold())

    def a_dict(self):
        """Para guardar la vista previa en la sesión."""
        return {"numero": self.numero, "fecha": self.fecha.isoformat(), "tipo": self.tipo,
                "monto": str(self.monto), "categoria": self.categoria, "descripcion": self.descripcion}

    @classmethod
    def desde_dict(cls, datos):
        return cls(datos["numero"], date.fromisoformat(datos["fecha"]), datos["tipo"],
                   Decimal(datos["monto"]), datos["categoria"], datos["descripcion"])


@dataclass
class ResultadoImportacion:
    aceptadas: list = field(default_factory=list)
    duplicadas: list = field(default_factory=list)
    rechazadas: list = field(default_factory=list)   # [(número de fila, [errores])]
    errores_generales: list = field(default_factory=list)

    @property
    def se_puede_importar(self):
        return bool(self.aceptadas) and not self.rechazadas and not self.errores_generales


def _normalizar(texto) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return texto.strip().casefold()


def _mapear_encabezados(encabezados):
    mapa = {}
    for i, encabezado in enumerate(encabezados):
        campo = _SINONIMOS.get(_normalizar(encabezado))
        if campo and campo not in mapa.values():
            mapa[i] = campo
    faltan = [c for c in ("fecha", "tipo", "monto", "categoria") if c not in mapa.values()]
    if faltan:
        raise ArchivoInvalido("Faltan columnas obligatorias: " + ", ".join(faltan) + ".")
    return mapa


def _filas_a_dicts(filas):
    filas = [f for f in filas if any(c not in (None, "") for c in f)]
    if not filas:
        raise ArchivoInvalido("El archivo está vacío.")
    mapa = _mapear_encabezados(filas[0])
    if len(filas) - 1 > MAX_FILAS:
        raise ArchivoInvalido(f"El archivo supera el máximo de {MAX_FILAS} filas.")
    return [
        (numero, {campo: (fila[i] if i < len(fila) else None) for i, campo in mapa.items()})
        for numero, fila in enumerate(filas[1:], start=2)   # la fila 1 son los encabezados
    ]


def leer_csv(contenido: bytes):
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = contenido.decode("latin-1")
    try:
        dialecto = csv.Sniffer().sniff(texto[:2048], delimiters=";,\t")
        delimitador = dialecto.delimiter
    except csv.Error:
        delimitador = ";"
    return _filas_a_dicts([list(f) for f in csv.reader(io.StringIO(texto), delimiter=delimitador)])


def leer_xlsx(contenido: bytes):
    from openpyxl import load_workbook

    try:
        libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    except Exception as exc:   # archivo dañado o que no es .xlsx
        raise ArchivoInvalido("No se pudo abrir el archivo Excel.") from exc
    return _filas_a_dicts([list(f) for f in libro.worksheets[0].iter_rows(values_only=True)])


def leer_archivo(nombre: str, contenido: bytes):
    if len(contenido) > MAX_BYTES:
        raise ArchivoInvalido("El archivo pesa más de 2 MB.")
    nombre = nombre.lower()
    if nombre.endswith(".xlsx"):
        return leer_xlsx(contenido)
    if nombre.endswith(".csv") or nombre.endswith(".txt"):
        return leer_csv(contenido)
    raise ArchivoInvalido("Sube un archivo .xlsx o .csv.")


def leer_fecha(valor):
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor or "").strip()
    for formato in _FORMATOS_FECHA:
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


def leer_monto(valor):
    """Acepta 12500, 12500.0, "12.500" y "$ 12.500". Pesos sin decimales."""
    if isinstance(valor, bool) or valor in (None, ""):
        return None
    if isinstance(valor, (int, float, Decimal)):
        numero = Decimal(str(valor))
    else:
        texto = str(valor).replace("$", "").replace(" ", "").replace(" ", "")
        if "," in texto:                                    # 1.234,00 → coma decimal
            texto = texto.replace(".", "").replace(",", ".")
        elif "." in texto and all(len(p) == 3 for p in texto.split(".")[1:]):
            texto = texto.replace(".", "")                  # 12.500 → separador de miles
        try:
            numero = Decimal(texto)
        except InvalidOperation:
            return None
    if not numero.is_finite() or numero != numero.to_integral_value():
        return None
    return numero.to_integral_value()


def validar_filas(filas, *, categorias_por_tipo, claves_existentes=(), hoy=None):
    """Separa aceptadas, duplicadas y rechazadas.

    `categorias_por_tipo`: {"ingreso": ["Ventas", ...], "gasto": [...]}.
    `claves_existentes`: claves (FilaValida.clave) de los movimientos que el
    negocio ya tiene, para no importarlos dos veces.
    """
    hoy = hoy or date.today()
    vistas = set(claves_existentes)
    catalogo = {t: {_normalizar(c): c for c in cs} for t, cs in categorias_por_tipo.items()}
    resultado = ResultadoImportacion()

    for numero, crudo in filas:
        errores = []
        fecha = leer_fecha(crudo.get("fecha"))
        if fecha is None:
            errores.append("Fecha no reconocida (usa dd/mm/aaaa).")
        elif fecha > hoy:
            errores.append("La fecha es futura.")

        tipo = _TIPOS.get(_normalizar(crudo.get("tipo")))
        if tipo is None:
            errores.append("El tipo debe ser ingreso o gasto.")

        monto = leer_monto(crudo.get("monto"))
        if monto is None:
            errores.append("Monto no válido (pesos sin decimales).")
        elif monto < 1:
            errores.append("El monto debe ser de al menos $1.")

        categoria = str(crudo.get("categoria") or "").strip()
        if tipo:
            real = catalogo.get(tipo, {}).get(_normalizar(categoria))
            if real is None:
                errores.append(f'La categoría "{categoria}" no existe para {tipo}s.')
            else:
                categoria = real

        if errores:
            resultado.rechazadas.append((numero, errores))
            continue
        fila = FilaValida(numero, fecha, tipo, monto, categoria, str(crudo.get("descripcion") or "").strip()[:255])
        if fila.clave in vistas:
            resultado.duplicadas.append(fila)
        else:
            vistas.add(fila.clave)
            resultado.aceptadas.append(fila)
    return resultado


def meses_sobre_el_limite(aceptadas, existentes_por_mes, limite):
    """RN-05: meses (aaaa-mm) en que lo importado más lo ya registrado supera el límite del plan."""
    if not limite:
        return []
    nuevas = Counter(f.fecha.strftime("%Y-%m") for f in aceptadas)
    return sorted(mes for mes, cantidad in nuevas.items() if existentes_por_mes.get(mes, 0) + cantidad > limite)
