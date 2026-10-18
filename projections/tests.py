from decimal import Decimal

from django.test import SimpleTestCase

# Create your tests here.

from .services import (
    calcular_payback,
    calcular_tir,
    calcular_van,
    evaluar_viabilidad,
    proyectar_ingresos,
    regresion_lineal_simple,
)


class RegresionYProyeccionTests(SimpleTestCase):
    def test_regresion_recta_perfecta(self):
        # y = 100 + 100x -> en x=0,1,2,3 da 100,200,300,400
        a, b = regresion_lineal_simple([100, 200, 300, 400])
        self.assertAlmostEqual(a, 100, places=6)
        self.assertAlmostEqual(b, 100, places=6)

    def test_proyeccion_continua_la_tendencia(self):
        proyeccion = proyectar_ingresos([Decimal("100"), Decimal("200"), Decimal("300"), Decimal("400")], meses_futuros=2)
        self.assertEqual(proyeccion, [Decimal("500"), Decimal("600")])

    def test_proyeccion_nunca_es_negativa(self):
        # Tendencia claramente decreciente y sostenida en el tiempo.
        proyeccion = proyectar_ingresos([Decimal("300"), Decimal("200"), Decimal("100"), Decimal("0")], meses_futuros=3)
        self.assertTrue(all(v >= 0 for v in proyeccion))

    def test_menos_de_dos_meses_lanza_error(self):
        with self.assertRaises(ValueError):
            proyectar_ingresos([Decimal("100")], meses_futuros=1)


class VANTIRPaybackTests(SimpleTestCase):
    def test_van_con_tasa_cero_es_la_suma_de_flujos(self):
        # Sin descuento, el VAN es simplemente la suma algebraica de los flujos.
        self.assertAlmostEqual(calcular_van(0.0, [-100, 40, 40, 40]), 20.0, places=6)

    def test_van_caso_exacto_un_periodo(self):
        # -1000 hoy, +1100 en un año, tasa 10% -> VAN = -1000 + 1100/1.1 = 0
        self.assertAlmostEqual(calcular_van(0.10, [-1000, 1100]), 0.0, places=6)

    def test_tir_recupera_la_tasa_que_hace_van_cero(self):
        flujos = [-1000, 500, 500, 500]
        tir = calcular_tir(flujos)
        self.assertIsNotNone(tir)
        self.assertAlmostEqual(calcular_van(tir, flujos), 0.0, places=4)

    def test_tir_es_none_si_todos_los_flujos_tienen_el_mismo_signo(self):
        self.assertIsNone(calcular_tir([100, 100, 100]))

    def test_payback_exacto_al_final_del_segundo_periodo(self):
        # -1000, +500, +500 -> se recupera justo al cierre del período 2.
        self.assertAlmostEqual(calcular_payback([-1000, 500, 500]), 2.0, places=6)

    def test_payback_none_si_nunca_se_recupera(self):
        self.assertIsNone(calcular_payback([-1000, 100, 100]))

    def test_evaluar_viabilidad_proyecto_claramente_rentable(self):
        resultado = evaluar_viabilidad(
            Decimal("1000000"), [Decimal("600000"), Decimal("600000"), Decimal("600000")], Decimal("0.12")
        )
        self.assertTrue(resultado["viable"])
        self.assertGreater(resultado["van"], 0)
        self.assertGreater(resultado["tir_porcentaje"], 12)

    def test_evaluar_viabilidad_proyecto_claramente_no_rentable(self):
        resultado = evaluar_viabilidad(
            Decimal("1000000"), [Decimal("50000"), Decimal("50000")], Decimal("0.12")
        )
        self.assertFalse(resultado["viable"])
        self.assertLess(resultado["van"], 0)