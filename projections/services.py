"""
Dos herramientas separadas, ambas mencionadas explícitamente como
objetivo del informe:

1. `proyectar_ingresos`: proyección de ingresos futuros a partir del
   historial de movimientos del propio usuario (Objetivo específico 2:
   "proyectar las fuentes de ingresos").
2. `evaluar_viabilidad`: calculadora de VAN / TIR / Payback para que el
   propio microempresario evalúe un proyecto o inversión suya (Objetivo
   específico 6 y Sección X del informe — la misma metodología que este
   informe aplicó para evaluar a FinMicro, ofrecida aquí como
   funcionalidad para los usuarios de la plataforma).

Se usa `float` para la aritmética intermedia de regresión/bisección (es
una estimación estadística, no un monto contable exacto) y se convierte
a `Decimal` redondeado solo en el resultado final, para que las cifras
que ve el usuario sean consistentes con el resto de la aplicación.
"""
from decimal import ROUND_HALF_UP, Decimal


def _redondear_clp(monto: float) -> Decimal:
    return Decimal(str(monto)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def regresion_lineal_simple(valores_y: list[float]) -> tuple[float, float]:
    """Ajuste por mínimos cuadrados de y = a + b·x sobre x = 0, 1, 2, ...

    Se implementa a mano (sin numpy) porque son cuatro sumatorias sobre
    pocos meses de datos; no vale la pena una dependencia extra para esto.
    """
    n = len(valores_y)
    if n < 2:
        raise ValueError("Se necesitan al menos 2 meses de historial para proyectar.")

    xs = list(range(n))
    suma_x = sum(xs)
    suma_y = sum(valores_y)
    suma_xy = sum(x * y for x, y in zip(xs, valores_y))
    suma_x2 = sum(x * x for x in xs)

    denominador = n * suma_x2 - suma_x**2
    if denominador == 0:
        b = 0.0
    else:
        b = (n * suma_xy - suma_x * suma_y) / denominador
    a = (suma_y - b * suma_x) / n
    return a, b


def proyectar_ingresos(historial_mensual: list[Decimal], meses_futuros: int = 3) -> list[Decimal]:
    """Proyecta `meses_futuros` valores adicionales a partir del historial.

    Los ingresos proyectados nunca son negativos (se acotan en 0): una
    recta de tendencia puede cruzar el eje X en un escenario de caída
    sostenida, pero un ingreso mensual negativo no tiene sentido de negocio.
    """
    valores = [float(v) for v in historial_mensual]
    a, b = regresion_lineal_simple(valores)
    n = len(valores)

    proyeccion = []
    for i in range(meses_futuros):
        x = n + i
        valor = max(0.0, a + b * x)
        proyeccion.append(_redondear_clp(valor))
    return proyeccion


def calcular_van(tasa_descuento: float, flujos: list[float]) -> float:
    """flujos[0] = inversión inicial (debe ir en negativo); flujos[1:] = flujos futuros."""
    return sum(flujo / (1 + tasa_descuento) ** i for i, flujo in enumerate(flujos))


def calcular_tir(flujos: list[float], tolerancia=1e-6, iteraciones_max=200):
    """TIR por bisección: la tasa r tal que VAN(r) = 0.

    Se usa bisección (no Newton-Raphson) porque es robusta y no requiere
    derivadas ni una buena estimación inicial — a costa de más
    iteraciones, que aquí no importan (son cálculos instantáneos).
    Devuelve None si no hay cambio de signo en el rango explorado (-99%
    a 1000%), lo que ocurre cuando todos los flujos tienen el mismo signo.
    """
    baja, alta = -0.99, 10.0
    van_baja = calcular_van(baja, flujos)
    van_alta = calcular_van(alta, flujos)

    if van_baja == 0:
        return baja
    if van_alta == 0:
        return alta
    if van_baja * van_alta > 0:
        return None

    for _ in range(iteraciones_max):
        medio = (baja + alta) / 2
        van_medio = calcular_van(medio, flujos)
        if abs(van_medio) < tolerancia:
            return medio
        if van_baja * van_medio < 0:
            alta = medio
        else:
            baja = medio
            van_baja = van_medio
    return (baja + alta) / 2


def calcular_payback(flujos: list[float]):
    """Períodos completos + fracción para recuperar la inversión inicial.

    Devuelve None si la inversión nunca se recupera dentro de los
    períodos entregados (mismo criterio que la Tabla 12 del informe:
    limitación explícita del payback simple).
    """
    acumulado = flujos[0]
    if acumulado >= 0:
        return 0.0

    for i, flujo in enumerate(flujos[1:], start=1):
        acumulado_anterior = acumulado
        acumulado += flujo
        if acumulado >= 0:
            fraccion = (-acumulado_anterior / flujo) if flujo else 0.0
            return (i - 1) + fraccion
    return None


def evaluar_viabilidad(inversion_inicial: Decimal, flujos_periodo: list[Decimal], tasa_descuento: Decimal) -> dict:
    """Evalúa un proyecto propio del usuario con la misma metodología

    (VAN / TIR / Payback) usada en la Sección X de este informe para
    evaluar FinMicro.
    """
    flujos = [-abs(float(inversion_inicial))] + [float(f) for f in flujos_periodo]
    tasa = float(tasa_descuento)

    van = calcular_van(tasa, flujos)
    tir = calcular_tir(flujos)
    payback = calcular_payback(flujos)

    van_ingresos = sum(f / (1 + tasa) ** i for i, f in enumerate(flujos) if i > 0 and f > 0)
    van_egresos = abs(flujos[0]) + sum(
        abs(f) / (1 + tasa) ** i for i, f in enumerate(flujos) if i > 0 and f < 0
    )
    beneficio_costo = (van_ingresos / van_egresos) if van_egresos else None

    return {
        "van": _redondear_clp(van),
        "tir_porcentaje": round(tir * 100, 2) if tir is not None else None,
        "payback_periodos": round(payback, 2) if payback is not None else None,
        "beneficio_costo": round(beneficio_costo, 2) if beneficio_costo else None,
        "viable": van > 0,
        "tasa_descuento_porcentaje": round(tasa * 100, 2),
    }