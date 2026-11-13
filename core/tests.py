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
                "acepta_terminos": "on",
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


# ---------- RF-24: alertas ----------
from datetime import date

from django.core import mail
from django.core.management import call_command

from accounts.legal import registrar_aceptacion
from accounts.models import Usuario
from subscriptions.services import asegurar_plan_basico
from taxes.calendario import Obligacion

from .alertas import regla_gasto_inusual, regla_limite_plan, regla_vencimiento
from .models import Alerta


class ReglasDeAlertaTests(TestCase):
    def test_vencimiento(self):
        ob = Obligacion("F29", "F29", "octubre 2026", "2026-10", date(2026, 11, 20))
        self.assertEqual(regla_vencimiento(ob, date(2026, 11, 20))[0], "urgente")
        self.assertIn("mañana", regla_vencimiento(ob, date(2026, 11, 19))[1])
        self.assertEqual(regla_vencimiento(ob, date(2026, 11, 15))[0], "aviso")
        self.assertIsNone(regla_vencimiento(ob, date(2026, 11, 12)))     # faltan 8 días
        self.assertIsNone(regla_vencimiento(ob, date(2026, 11, 21)))     # ya venció

    def test_limite_de_plan(self):
        self.assertEqual(regla_limite_plan(48, 60)[0], "80")
        self.assertEqual(regla_limite_plan(60, 60)[0], "100")
        self.assertIsNone(regla_limite_plan(47, 60))
        self.assertIsNone(regla_limite_plan(500, None))

    def test_gasto_inusual_usa_la_mediana(self):
        self.assertIn("5.0 veces", regla_gasto_inusual(500, [100, 100, 120]))
        self.assertIsNone(regla_gasto_inusual(150, [100, 100, 100]))
        self.assertIsNone(regla_gasto_inusual(500, [100, 100]))           # historial insuficiente
        # Un único gasto alto anterior no vuelve normal un gasto alto.
        self.assertIsNotNone(regla_gasto_inusual(400, [100, 100, 100, 5000]))


class AlertasIntegracionTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="taller", email="taller@example.com", password="UnaClaveSegura.2026",
            rut="11111111-1", nombre_negocio="Taller", regimen_tributario="PP", afecto_iva=True,
        )
        asegurar_plan_basico(self.usuario)
        registrar_aceptacion(self.usuario)
        self.client.login(username="taller", password="UnaClaveSegura.2026")
        self.transporte = Categoria.objects.get(nombre="Transporte", usuario=None)

    def _gasto(self, monto):
        self.client.post(reverse("finances:crear_movimiento"), {
            "tipo": "gasto", "categoria": self.transporte.pk, "monto": str(monto),
            "fecha": timezone.localdate().isoformat(),
        })

    def test_gasto_inusual_genera_alerta_en_el_panel(self):
        for monto in (10_000, 12_000, 11_000):
            self._gasto(monto)
        self.assertFalse(Alerta.objects.filter(codigo__startswith="GASTO").exists())
        self._gasto(50_000)
        alerta = Alerta.objects.get(codigo__startswith="GASTO")
        self.assertContains(self.client.get(reverse("finances:dashboard")), "4.5 veces")

        self.client.post(reverse("core:marcar_alerta_leida", args=[alerta.pk]), {"siguiente": "https://malicioso.example"})
        alerta.refresh_from_db()
        self.assertTrue(alerta.leida)
        self.assertNotContains(self.client.get(reverse("finances:dashboard")), "4.5 veces")

    def test_otro_negocio_no_ve_ni_marca_mis_alertas(self):
        alerta = Alerta.objects.create(negocio=self.usuario, codigo="X", mensaje="Privada")
        otro = Usuario.objects.create_user(username="otro", email="o@example.com", password="UnaClaveSegura.2026",
                                           rut="22222222-2", nombre_negocio="Otro")
        registrar_aceptacion(otro)
        self.client.login(username="otro", password="UnaClaveSegura.2026")
        self.assertNotContains(self.client.get(reverse("core:alertas")), "Privada")
        self.assertEqual(self.client.post(reverse("core:marcar_alerta_leida", args=[alerta.pk])).status_code, 404)

    def test_comando_diario_crea_alertas_de_vencimiento_y_avisa_por_correo(self):
        with mock.patch("core.management.commands.generar_alertas.timezone.localdate", return_value=date(2026, 11, 15)):
            call_command("generar_alertas", stdout=mock.MagicMock())
            call_command("generar_alertas", stdout=mock.MagicMock())    # idempotente
        alerta = Alerta.objects.get(negocio=self.usuario)
        self.assertEqual(alerta.codigo, "VENC-F29-2026-10")
        self.assertIn("20-11-2026", alerta.mensaje)
        self.assertEqual(len(mail.outbox), 1)


# ---------- RF-32: auditoría ----------
from django.contrib.admin.sites import site
from django.test import RequestFactory

from .models import RegistroAuditoria


class AuditoriaTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="duena", email="duena@example.com", password="UnaClaveSegura.2026",
            rut="11111111-1", nombre_negocio="Tienda",
        )
        asegurar_plan_basico(self.usuario)
        registrar_aceptacion(self.usuario)

    def test_registra_inicio_fallo_y_cierre_de_sesion_sin_guardar_claves(self):
        self.client.post(reverse("accounts:login"), {"username": "duena", "password": "mala"})
        self.client.post(reverse("accounts:login"), {"username": "duena", "password": "UnaClaveSegura.2026"},
                         REMOTE_ADDR="10.0.0.7")
        self.client.post(reverse("accounts:logout"))
        acciones = list(RegistroAuditoria.objects.exclude(accion="consentimiento")
                        .order_by("creado_en").values_list("accion", flat=True))
        self.assertEqual(acciones, ["login_fallido", "login", "logout"])
        self.assertEqual(RegistroAuditoria.objects.get(accion="login").ip, "10.0.0.7")
        self.assertFalse(RegistroAuditoria.objects.filter(detalle__contains="mala").exists())

    def test_eliminar_movimiento_y_cuenta_quedan_registrados(self):
        self.client.login(username="duena", password="UnaClaveSegura.2026")
        ventas = Categoria.objects.get(nombre="Ventas", usuario=None)
        movimiento = Movimiento.objects.create(usuario=self.usuario, categoria=ventas, tipo="ingreso",
                                               monto=1000, fecha=timezone.localdate())
        self.client.post(reverse("finances:eliminar_movimiento", args=[movimiento.pk]))
        self.client.post(reverse("accounts:eliminar_cuenta"), {"password": "UnaClaveSegura.2026"})
        self.assertTrue(RegistroAuditoria.objects.filter(accion="eliminar_movimiento").exists())
        # El registro sobrevive a la cuenta eliminada, con el nombre como texto.
        registro = RegistroAuditoria.objects.get(accion="eliminar_cuenta")
        self.assertIsNone(registro.usuario)
        self.assertEqual(registro.nombre_usuario, "duena")

    def test_el_administrador_no_puede_editar_ni_borrar_registros(self):
        admin_auditoria = site._registry[RegistroAuditoria]
        request = RequestFactory().get("/")
        request.user = Usuario.objects.create_superuser("root", "r@example.com", "UnaClaveSegura.2026",
                                                        rut="22222222-2", nombre_negocio="Admin")
        self.assertFalse(admin_auditoria.has_add_permission(request))
        self.assertFalse(admin_auditoria.has_change_permission(request))
        self.assertFalse(admin_auditoria.has_delete_permission(request))


# ---------- RF-37: asistente ----------
from types import SimpleNamespace

import anthropic
from django.test import override_settings

from subscriptions.models import Suscripcion
from subscriptions.services import asegurar_plan_premium

from .models import ConsultaAsistente


def _respuesta(texto="Este mes vendiste $300.000.", stop_reason="end_turn"):
    return SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=texto)])


class AsistenteTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="premium", email="p@example.com", password="UnaClaveSegura.2026",
            rut="11111111-1", nombre_negocio="Panadería Sol",
        )
        Suscripcion.objects.create(usuario=self.usuario, plan=asegurar_plan_premium(), estado="activa")
        registrar_aceptacion(self.usuario)
        ventas = Categoria.objects.get(nombre="Ventas", usuario=None)
        Movimiento.objects.create(usuario=self.usuario, categoria=ventas, tipo="ingreso", monto=300_000,
                                  fecha=timezone.localdate())
        otro = Usuario.objects.create_user(username="otro", email="o@example.com", password="x",
                                           rut="22222222-2", nombre_negocio="Negocio Ajeno Secreto")
        Movimiento.objects.create(usuario=otro, categoria=ventas, tipo="ingreso", monto=7_777_777,
                                  fecha=timezone.localdate())
        self.client.login(username="premium", password="UnaClaveSegura.2026")

    def _preguntar(self, cliente, texto="¿Cuánto vendí?"):
        with mock.patch("core.asistente.anthropic.Anthropic", return_value=cliente):
            return self.client.post(reverse("core:asistente"), {"pregunta": texto})

    def test_sin_clave_queda_apagado(self):
        self.assertContains(self.client.get(reverse("core:asistente")), "aún no está activo")

    def test_solo_premium(self):
        Suscripcion.objects.filter(usuario=self.usuario).update(estado="cancelada")
        self.assertRedirects(self.client.get(reverse("core:asistente")), reverse("subscriptions:planes"))

    @override_settings(ANTHROPIC_API_KEY="clave-de-prueba")
    def test_responde_con_datos_solo_del_negocio_activo(self):
        cliente = mock.MagicMock()
        cliente.beta.messages.create.return_value = _respuesta()
        respuesta = self._preguntar(cliente)
        self.assertContains(respuesta, "Este mes vendiste $300.000.")
        argumentos = cliente.beta.messages.create.call_args.kwargs
        self.assertEqual(argumentos["model"], "claude-opus-5-5")
        self.assertEqual(argumentos["fallbacks"], "default")
        enviado = argumentos["messages"][0]["content"]
        self.assertIn("Panadería Sol", enviado)
        self.assertIn("$300.000", enviado)
        self.assertNotIn("Ajeno", enviado)
        self.assertNotIn("7.777.777", enviado)
        self.assertEqual(ConsultaAsistente.objects.get().pregunta, "¿Cuánto vendí?")

    @override_settings(ANTHROPIC_API_KEY="clave-de-prueba", ASISTENTE_PREGUNTAS_POR_DIA=1)
    def test_tope_diario(self):
        cliente = mock.MagicMock()
        cliente.beta.messages.create.return_value = _respuesta()
        self._preguntar(cliente)
        respuesta = self._preguntar(cliente)
        self.assertContains(respuesta, "máximo de preguntas de hoy")
        self.assertEqual(cliente.beta.messages.create.call_count, 1)

    @override_settings(ANTHROPIC_API_KEY="clave-de-prueba")
    def test_rechazo_del_modelo(self):
        cliente = mock.MagicMock()
        cliente.beta.messages.create.return_value = _respuesta("", stop_reason="refusal")
        self.assertContains(self._preguntar(cliente), "No puedo ayudarte con esa pregunta")

    @override_settings(ANTHROPIC_API_KEY="clave-de-prueba")
    def test_falla_de_la_api_no_guarda_nada(self):
        cliente = mock.MagicMock()
        cliente.beta.messages.create.side_effect = anthropic.APIConnectionError(request=mock.MagicMock())
        self.assertContains(self._preguntar(cliente), "no pudo responder ahora")
        self.assertFalse(ConsultaAsistente.objects.exists())
