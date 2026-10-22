"""Prueba de humo: recorre todas las pantallas principales con un usuario real."""
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from finances.models import Categoria, Movimiento


class RecorridoCompletoTests(TestCase):
    def setUp(self):
        respuesta = self.client.post(
            reverse("accounts:registro"),
            {
                "username": "feriante",
                "email": "feriante@example.com",
                "rut": "12345678-5",
                "nombre_negocio": "Verduras Don Pepe",
                "tipo_negocio": "FL",
                "password1": "UnaClaveSegura.2026",
                "password2": "UnaClaveSegura.2026",
            },
        )
        self.assertRedirects(respuesta, reverse("finances:dashboard"))

    @mock.patch("core.views.BancoCentralService.indicadores_del_dia", side_effect=Exception)
    def test_home_publica(self, _):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("core:home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("accounts:login")).status_code, 200)
        self.assertEqual(self.client.get(reverse("accounts:registro")).status_code, 200)

    def test_paginas_autenticadas_cargan(self):
        for nombre in [
            "finances:dashboard",
            "finances:listar_movimientos",
            "finances:crear_movimiento",
            "finances:crear_categoria",
            "taxes:calculadora",
            "projections:proyeccion_ingresos",
            "subscriptions:planes",
            "subscriptions:mi_suscripcion",
            "accounts:perfil",
            "accounts:password_change",
        ]:
            with self.subTest(nombre=nombre):
                self.assertEqual(self.client.get(reverse(nombre)).status_code, 200)

    def test_crud_movimiento(self):
        ventas = Categoria.objects.get(nombre="Ventas", usuario=None)
        respuesta = self.client.post(
            reverse("finances:crear_movimiento"),
            {"tipo": "ingreso", "categoria": ventas.pk, "monto": "150000",
             "fecha": timezone.localdate().isoformat(), "descripcion": "Feria"},
        )
        self.assertRedirects(respuesta, reverse("finances:dashboard"))
        movimiento = Movimiento.objects.get()

        self.assertContains(self.client.get(reverse("finances:dashboard")), "150.000")
        self.assertContains(self.client.get(reverse("finances:listar_movimientos") + "?mes=&anio=&tipo=ingreso"), "Feria")
        self.assertEqual(self.client.get(reverse("finances:editar_movimiento", args=[movimiento.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("finances:eliminar_movimiento", args=[movimiento.pk])).status_code, 200)
        self.client.post(reverse("finances:eliminar_movimiento", args=[movimiento.pk]))
        self.assertFalse(Movimiento.objects.exists())

    def test_calculadora_impuestos(self):
        respuesta = self.client.post(
            reverse("taxes:calculadora"),
            {"formulario": "iva", "iva-ventas_netas": "1000000", "iva-compras_netas": "300000"},
        )
        self.assertContains(respuesta, "133.000")
        respuesta = self.client.post(
            reverse("taxes:calculadora"),
            {"formulario": "honorarios", "hon-modo": "bruto", "hon-monto": "1000000", "hon-anio": "2026"},
        )
        self.assertContains(respuesta, "847.500")

    def test_flujo_premium_y_evaluador(self):
        # Sin Premium, el evaluador redirige a planes.
        self.assertRedirects(
            self.client.get(reverse("projections:evaluador_viabilidad")), reverse("subscriptions:planes")
        )
        self.assertEqual(
            self.client.get(reverse("subscriptions:suscribirse", args=["premium"])).status_code, 200
        )
        respuesta = self.client.post(reverse("subscriptions:suscribirse", args=["premium"]), {"pasarela": "khipu"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(self.client.get(respuesta.url).status_code, 200)
        self.client.post(respuesta.url)

        respuesta = self.client.post(
            reverse("projections:evaluador_viabilidad"),
            {"inversion_inicial": "1000000", "tasa_descuento_pct": "12",
             "flujos_texto": "600000\n600000\n600000"},
        )
        self.assertContains(respuesta, "Viable")
