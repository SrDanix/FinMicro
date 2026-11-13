from decimal import Decimal

from django.test import SimpleTestCase

# Create your tests here.


from .services import (
    calcular_honorarios_desde_bruto,
    calcular_honorarios_desde_liquido,
    calcular_iva,
    tasa_retencion_honorarios,
)


class CalculadoraIVATests(SimpleTestCase):
    def test_iva_a_pagar_cuando_ventas_superan_compras(self):
        resultado = calcular_iva(Decimal("1000000"), Decimal("300000"))
        self.assertEqual(resultado["iva_debito"], Decimal("190000"))
        self.assertEqual(resultado["iva_credito"], Decimal("57000"))
        self.assertEqual(resultado["resultado"], Decimal("133000"))
        self.assertTrue(resultado["a_pagar"])
        self.assertFalse(resultado["remanente"])

    def test_remanente_a_favor_cuando_compras_superan_ventas(self):
        resultado = calcular_iva(Decimal("100000"), Decimal("500000"))
        self.assertTrue(resultado["remanente"])
        self.assertFalse(resultado["a_pagar"])
        self.assertEqual(resultado["resultado"], Decimal("76000"))

    def test_sin_compras(self):
        resultado = calcular_iva(Decimal("50000"), Decimal("0"))
        self.assertEqual(resultado["iva_debito"], Decimal("9500"))
        self.assertEqual(resultado["iva_credito"], Decimal("0"))


class CalculadoraHonorariosTests(SimpleTestCase):
    def test_tasa_2026_es_15_25_por_ciento(self):
        # Ley 21.133 — retención vigente desde el 1 de enero de 2026.
        self.assertEqual(tasa_retencion_honorarios(2026), Decimal("0.1525"))

    def test_tasa_topa_en_17_por_ciento_desde_2028_en_adelante(self):
        self.assertEqual(tasa_retencion_honorarios(2028), Decimal("0.17"))
        self.assertEqual(tasa_retencion_honorarios(2030), Decimal("0.17"))

    def test_calculo_desde_bruto_ejemplo_oficial(self):
        # Ejemplo verificado: boleta de $1.000.000 en 2026 -> retienen $152.500.
        resultado = calcular_honorarios_desde_bruto(Decimal("1000000"), 2026)
        self.assertEqual(resultado["retencion"], Decimal("152500"))
        self.assertEqual(resultado["monto_liquido"], Decimal("847500"))

    def test_ida_y_vuelta_bruto_liquido_es_consistente(self):
        bruto = calcular_honorarios_desde_bruto(Decimal("500000"), 2026)
        liquido = calcular_honorarios_desde_liquido(bruto["monto_liquido"], 2026)
        # Puede diferir en 1 peso por el redondeo independiente de cada
        # sentido del cálculo; nunca más que eso.
        self.assertLessEqual(abs(liquido["monto_bruto"] - bruto["monto_bruto"]), Decimal("1"))

# ---------- RF-25, RF-22 y RF-23 ----------
from datetime import date

from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.legal import registrar_aceptacion
from accounts.models import Usuario
from finances.models import Categoria, Movimiento, Producto
from subscriptions.services import asegurar_plan_basico

from .calendario import obligaciones, siguiente_dia_habil, vencimiento_f22, vencimiento_f29
from .models import TasaTributaria
from .services import iva_del_mes, iva_desde_montos_brutos, tasa_vigente

CLAVE = "UnaClaveSegura.2026"


def _usuario(username="almacen", rut="11111111-1", **extra):
    usuario = Usuario.objects.create_user(
        username=username, email=f"{username}@example.com", password=CLAVE, rut=rut,
        nombre_negocio="Almacén", **extra,
    )
    asegurar_plan_basico(usuario)
    registrar_aceptacion(usuario)
    return usuario


class TasasEditablesTests(TestCase):
    def test_carga_inicial_igual_a_las_tasas_legales(self):
        self.assertEqual(tasa_vigente("IVA", date(2026, 11, 1)), Decimal("0.19"))
        self.assertEqual(tasa_vigente("RET_HON", date(2026, 6, 1)), Decimal("0.1525"))
        self.assertEqual(tasa_vigente("RET_HON", date(2031, 1, 1)), Decimal("0.17"))
        # Antes de la tabla se usa la tasa más antigua registrada.
        self.assertEqual(tasa_vigente("RET_HON", date(2020, 1, 1)), Decimal("0.145"))

    def test_tasa_nueva_reemplaza_desde_su_inicio_sin_cerrar_la_anterior(self):
        TasaTributaria.objects.create(codigo="IVA", valor=Decimal("0.20"), vigente_desde=date(2030, 1, 1), fuente="Prueba")
        self.assertEqual(tasa_vigente("IVA", date(2029, 12, 31)), Decimal("0.19"))
        self.assertEqual(tasa_vigente("IVA", date(2030, 1, 1)), Decimal("0.20"))

    def test_sin_tabla_usa_el_respaldo_del_codigo(self):
        TasaTributaria.objects.all().delete()
        self.assertEqual(tasa_vigente("IVA", date(2026, 1, 1)), Decimal("0.19"))
        self.assertEqual(tasa_vigente("RET_HON", date(2027, 1, 1)), Decimal("0.16"))

    def test_cambiar_la_tasa_en_la_tabla_cambia_la_calculadora(self):
        _usuario()
        self.client.login(username="almacen", password=CLAVE)
        TasaTributaria.objects.filter(codigo="RET_HON", vigente_desde=date(2026, 1, 1)).update(valor=Decimal("0.20"))
        respuesta = self.client.post(
            reverse("taxes:calculadora"),
            {"formulario": "honorarios", "hon-modo": "bruto", "hon-monto": "1000000", "hon-anio": "2026"},
        )
        self.assertContains(respuesta, "800.000")


class IVAAutomaticoTests(TestCase):
    def test_iva_desde_montos_brutos_calculado_a_mano(self):
        r = iva_desde_montos_brutos(119_000, 59_500, Decimal("0.19"))
        self.assertEqual((r["ventas_netas"], r["iva_debito"]), (100_000, 19_000))
        self.assertEqual((r["compras_netas"], r["iva_credito"]), (50_000, 9_500))
        self.assertEqual((r["iva_a_pagar"], r["remanente_siguiente"]), (9_500, 0))

    def test_remanente_cuando_el_credito_supera_al_debito(self):
        r = iva_desde_montos_brutos(0, 119_000, Decimal("0.19"), remanente_anterior=1_000)
        self.assertEqual((r["iva_a_pagar"], r["remanente_siguiente"]), (0, 20_000))

    def test_iva_del_mes_con_movimientos_afectos_y_remanente(self):
        negocio = _usuario(regimen_tributario="PP", afecto_iva=True)
        mes = timezone.localdate().replace(day=1)
        anterior = mes - relativedelta(months=1)

        def mov(nombre, tipo, monto, fecha, producto=None):
            cat = Categoria.objects.get(nombre=nombre, tipo=tipo, usuario=None)
            Movimiento.objects.create(usuario=negocio, categoria=cat, tipo=tipo, monto=monto, fecha=fecha, producto=producto)

        mov("Mercadería / insumos", "gasto", 119_000, anterior)        # crédito 19.000 → remanente
        mov("Ventas", "ingreso", 238_000, mes)                          # débito 38.000
        mov("Arriendo", "gasto", 500_000, mes)                          # categoría no afecta: no cuenta
        exento = Producto.objects.create(usuario=negocio, nombre="Libro", precio=10_000, afecto_iva=False)
        mov("Ventas", "ingreso", 10_000, mes, producto=exento)          # producto exento: no cuenta
        r = iva_del_mes(negocio, mes)
        self.assertEqual(r["remanente_anterior"], 19_000)
        self.assertEqual(r["iva_debito"], 38_000)
        self.assertEqual(r["iva_a_pagar"], 19_000)

        self.client.login(username="almacen", password=CLAVE)
        self.assertContains(self.client.get(reverse("taxes:calculadora")), "238.000")


class CalendarioTributarioTests(TestCase):
    FERIADOS = {date(2026, 10, 12), date(2028, 5, 1)}

    def test_dia_habil_siguiente(self):
        self.assertEqual(siguiente_dia_habil(date(2026, 11, 14)), date(2026, 11, 16))   # sábado → lunes
        self.assertEqual(siguiente_dia_habil(date(2026, 10, 12), self.FERIADOS), date(2026, 10, 13))

    def test_vencimiento_f29(self):
        # Período septiembre 2026: el 12 de octubre es feriado → martes 13.
        self.assertEqual(vencimiento_f29(2026, 9, electronico=False, feriados=self.FERIADOS), date(2026, 10, 13))
        self.assertEqual(vencimiento_f29(2026, 9, electronico=True, feriados=self.FERIADOS), date(2026, 10, 20))
        # Diciembre vence en enero del año siguiente.
        self.assertEqual(vencimiento_f29(2026, 12, electronico=True), date(2027, 1, 20))

    def test_vencimiento_f22(self):
        self.assertEqual(vencimiento_f22(2027), date(2027, 4, 30))                      # viernes
        # 30-04-2028 es domingo y el lunes 1 de mayo es feriado → martes 2.
        self.assertEqual(vencimiento_f22(2028, self.FERIADOS), date(2028, 5, 2))

    def test_obligaciones_segun_regimen(self):
        rango = {"desde": date(2026, 11, 1), "hasta": date(2027, 10, 31)}
        sin_inicio = obligaciones(regimen="SI", afecto_iva=False, emite_boletas_honorarios=False, **rango)
        self.assertEqual(sin_inicio, [])
        presunta = obligaciones(regimen="RP", afecto_iva=False, emite_boletas_honorarios=False, **rango)
        self.assertEqual([o.codigo for o in presunta], ["F22"])
        pro_pyme = obligaciones(regimen="PP", afecto_iva=True, emite_boletas_honorarios=False, **rango)
        self.assertEqual(sum(o.codigo == "F29" for o in pro_pyme), 12)
        self.assertEqual(pro_pyme[0].vence, date(2026, 11, 20))   # F29 de octubre
        self.assertEqual(pro_pyme[0].periodo, "octubre 2026")

    def test_pantalla_del_calendario(self):
        _usuario(regimen_tributario="PP", afecto_iva=True)
        self.client.login(username="almacen", password=CLAVE)
        respuesta = self.client.get(reverse("taxes:calendario"))
        self.assertContains(respuesta, "F29")
        self.assertContains(respuesta, "F22")
