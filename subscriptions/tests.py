"""Pruebas de RF-27 (pagos verificados con la pasarela) y RF-28 (renovación y vencimiento)."""
import hashlib
import hmac
from datetime import date, timedelta
from io import StringIO
from unittest import mock

from dateutil.relativedelta import relativedelta
from django.core import mail
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.legal import registrar_aceptacion
from accounts.models import Usuario
from core.models import Alerta, RegistroAuditoria

from .models import Plan, Suscripcion
from .services import (
    AVISAR,
    GRACIA,
    NINGUNA,
    VENCER,
    EstadoPago,
    ErrorPasarela,
    FlowGateway,
    activar_suscripcion_pagada,
    asegurar_plan_basico,
    asegurar_plan_premium,
    evaluar_renovacion,
)

CLAVE = "UnaClaveSegura.2026"
CREDENCIALES_FLOW = {"PAGOS_MODO_SIMULADO": False, "FLOW_API_KEY": "clave", "FLOW_SECRET_KEY": "secreto"}


class ReglasTests(SimpleTestCase):
    def test_evaluar_renovacion(self):
        hoy = date(2026, 11, 13)
        self.assertEqual(evaluar_renovacion(None, hoy), NINGUNA)
        self.assertEqual(evaluar_renovacion(date(2026, 11, 20), hoy), NINGUNA)
        self.assertEqual(evaluar_renovacion(date(2026, 11, 16), hoy), AVISAR)
        self.assertEqual(evaluar_renovacion(date(2026, 11, 13), hoy), AVISAR)   # el último día sigue cubierto
        self.assertEqual(evaluar_renovacion(date(2026, 11, 10), hoy), GRACIA)
        self.assertEqual(evaluar_renovacion(date(2026, 11, 9), hoy), VENCER)

    def test_firma_de_flow(self):
        # Parámetros ordenados por nombre y concatenados nombre+valor, HMAC-SHA256 con la secretKey.
        esperada = hmac.new(b"secreto", b"amount9990apiKeyclave", hashlib.sha256).hexdigest()
        self.assertEqual(FlowGateway()._firmar({"apiKey": "clave", "amount": 9990}, "secreto"), esperada)


class PagosTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="cliente", email="cliente@example.com", password=CLAVE, rut="11111111-1", nombre_negocio="Tienda"
        )
        asegurar_plan_basico(self.usuario)
        registrar_aceptacion(self.usuario)
        self.premium = asegurar_plan_premium()
        self.client.login(username="cliente", password=CLAVE)

    def _pendiente(self, token="tok-1", metodo="flow"):
        return Suscripcion.objects.create(
            usuario=self.usuario, plan=self.premium, estado=Suscripcion.Estado.PENDIENTE,
            metodo_pago=metodo, referencia_pago=token,
        )

    def _estado(self, suscripcion, pagado=True, monto=9990):
        return EstadoPago(pagado, monto, f"finmicro-{suscripcion.id}-abcd1234")

    @override_settings(**CREDENCIALES_FLOW)
    def test_iniciar_pago_flow_firmado_y_con_retorno_sin_csrf(self):
        respuesta_flow = mock.Mock(json=lambda: {"url": "https://sandbox.flow.cl/app/web/pay.php", "token": "tok-9"})
        with mock.patch("subscriptions.services.requests.post", return_value=respuesta_flow) as post:
            respuesta = self.client.post(reverse("subscriptions:suscribirse", args=["premium"]), {"pasarela": "flow"})
        self.assertEqual(respuesta.url, "https://sandbox.flow.cl/app/web/pay.php?token=tok-9")
        enviado = post.call_args.kwargs["data"]
        self.assertIn("s=", enviado)
        self.assertIn("pago%2Fretorno", enviado)
        self.assertEqual(Suscripcion.objects.get(referencia_pago="tok-9").estado, "pendiente")

    def test_webhook_activa_solo_si_la_pasarela_confirma(self):
        suscripcion = self._pendiente()
        with mock.patch.object(FlowGateway, "consultar_estado", return_value=self._estado(suscripcion)) as consulta:
            respuesta = self.client.post(reverse("subscriptions:webhook_flow"), {"token": "tok-1"})
            self.client.post(reverse("subscriptions:webhook_flow"), {"token": "tok-1"})   # aviso repetido
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(consulta.call_count, 1)                      # el repetido no vuelve a procesar
        suscripcion.refresh_from_db()
        self.assertEqual(suscripcion.estado, "activa")
        self.assertEqual(suscripcion.fecha_fin, suscripcion.fecha_inicio + relativedelta(months=1))
        self.assertTrue(self.usuario.es_premium)
        self.assertTrue(RegistroAuditoria.objects.filter(accion="pago").exists())

    def test_webhook_no_activa_con_monto_distinto_o_pago_rechazado(self):
        suscripcion = self._pendiente()
        for estado in (self._estado(suscripcion, monto=1), self._estado(suscripcion, pagado=False)):
            with mock.patch.object(FlowGateway, "consultar_estado", return_value=estado):
                self.client.post(reverse("subscriptions:webhook_flow"), {"token": "tok-1"})
            suscripcion.refresh_from_db()
            self.assertEqual(suscripcion.estado, "pendiente")

    def test_webhook_de_otra_suscripcion_no_activa(self):
        suscripcion = self._pendiente()
        ajena = EstadoPago(True, 9990, "finmicro-999-abcd")
        with mock.patch.object(FlowGateway, "consultar_estado", return_value=ajena):
            self.client.post(reverse("subscriptions:webhook_flow"), {"token": "tok-1"})
        suscripcion.refresh_from_db()
        self.assertEqual(suscripcion.estado, "pendiente")

    def test_aviso_falsificado_en_modo_simulado_no_activa(self):
        # Sin credenciales no se puede verificar: se responde 502 y no se activa nada.
        suscripcion = self._pendiente()
        respuesta = self.client.post(reverse("subscriptions:webhook_flow"), {"token": "tok-1", "status": "2"})
        self.assertEqual(respuesta.status_code, 502)
        suscripcion.refresh_from_db()
        self.assertEqual(suscripcion.estado, "pendiente")

    def test_webhook_token_desconocido_o_vacio(self):
        self.assertEqual(self.client.post(reverse("subscriptions:webhook_flow"), {"token": "nada"}).status_code, 404)
        self.assertEqual(self.client.post(reverse("subscriptions:webhook_flow"), {}).status_code, 400)
        self.assertEqual(self.client.get(reverse("subscriptions:webhook_flow")).status_code, 405)

    @override_settings(**CREDENCIALES_FLOW)
    def test_consulta_de_estado_flow_firmada(self):
        suscripcion = self._pendiente()
        respuesta = mock.Mock(json=lambda: {"status": 2, "amount": "9990", "commerceOrder": f"finmicro-{suscripcion.id}-x"})
        with mock.patch("subscriptions.services.requests.get", return_value=respuesta) as get:
            estado = FlowGateway().consultar_estado("tok-1")
        self.assertTrue(estado.pagado)
        self.assertIn("s", get.call_args.kwargs["params"])

    @override_settings(**CREDENCIALES_FLOW)
    def test_falla_de_comunicacion_responde_502(self):
        self._pendiente()
        import requests

        with mock.patch("subscriptions.services.requests.get", side_effect=requests.ConnectionError("caída")):
            self.assertEqual(self.client.post(reverse("subscriptions:webhook_flow"), {"token": "tok-1"}).status_code, 502)

    @override_settings(PAGOS_MODO_SIMULADO=False)
    def test_pago_simulado_no_existe_fuera_del_modo_simulado(self):
        suscripcion = self._pendiente(metodo="khipu")
        self.assertEqual(self.client.post(reverse("subscriptions:pago_simulado", args=[suscripcion.id])).status_code, 404)
        suscripcion.refresh_from_db()
        self.assertEqual(suscripcion.estado, "pendiente")

    def test_retorno_de_la_pasarela_sin_csrf(self):
        self.client.handler.enforce_csrf_checks = True
        respuesta = self.client.post(reverse("subscriptions:retorno_pago"), {"token": "x"})
        self.assertRedirects(respuesta, reverse("subscriptions:mi_suscripcion"))

    def test_renovar_suma_el_periodo_al_final_del_vigente(self):
        ahora = timezone.now()
        primera = activar_suscripcion_pagada(self._pendiente("a"), ahora=ahora)
        segunda = activar_suscripcion_pagada(self._pendiente("b"), ahora=ahora)
        # El segundo mes parte donde termina el primero, no hoy.
        self.assertEqual(segunda.fecha_fin, primera.fecha_fin + relativedelta(months=1))
        primera.refresh_from_db()
        self.assertEqual(primera.estado, "cancelada")
        self.assertEqual(Suscripcion.objects.filter(usuario=self.usuario, estado="activa").count(), 1)

    def test_pasarela_invalida(self):
        respuesta = self.client.post(reverse("subscriptions:suscribirse", args=["premium"]), {"pasarela": "otra"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(Suscripcion.objects.filter(estado="pendiente").exists())


class RenovacionTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="cliente", email="cliente@example.com", password=CLAVE, rut="11111111-1", nombre_negocio="Tienda"
        )
        self.premium = asegurar_plan_premium()

    def _premium_hasta(self, dias):
        return Suscripcion.objects.create(
            usuario=self.usuario, plan=self.premium, estado="activa",
            fecha_fin=timezone.now() + timedelta(days=dias),
        )

    def _correr(self):
        call_command("renovar_suscripciones", stdout=StringIO())

    def test_aviso_antes_de_vencer(self):
        self._premium_hasta(2)
        self._correr()
        self._correr()
        self.assertTrue(Alerta.objects.filter(codigo__startswith="SUSC-AVISO").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(self.usuario.es_premium)

    def test_gracia_y_luego_vuelta_al_plan_basico(self):
        suscripcion = self._premium_hasta(-2)
        self._correr()
        self.assertTrue(self.usuario.es_premium)
        Suscripcion.objects.filter(pk=suscripcion.pk).update(fecha_fin=timezone.now() - timedelta(days=5))
        self._correr()
        suscripcion.refresh_from_db()
        self.assertEqual(suscripcion.estado, "vencida")
        self.assertFalse(self.usuario.es_premium)
        self.assertEqual(self.usuario.suscripcion_activa.plan.codigo, Plan.Codigo.BASICO)
        self.assertTrue(Alerta.objects.filter(codigo__startswith="SUSC-VENCIDA").exists())
        self.assertTrue(RegistroAuditoria.objects.filter(accion="vencimiento_plan").exists())
