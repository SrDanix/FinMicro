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