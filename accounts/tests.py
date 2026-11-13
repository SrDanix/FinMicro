"""Pruebas del Sprint 1: cuenta, configuración, colaboradores y datos personales."""
import json
from io import StringIO

from django.core import mail
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from finances.models import Categoria, Movimiento
from subscriptions.services import asegurar_plan_basico
from .legal import registrar_aceptacion
from .models import Colaboracion, Usuario, calcular_dv_rut, validar_rut
from .negocio import SESION_NEGOCIO

CLAVE = "UnaClaveSegura.2026"


def crear_usuario(username, email, rut, negocio="Negocio"):
    usuario = Usuario.objects.create_user(
        username=username, email=email, password=CLAVE, rut=rut, nombre_negocio=negocio
    )
    asegurar_plan_basico(usuario)
    registrar_aceptacion(usuario)
    return usuario


class RutTests(SimpleTestCase):
    def test_digito_verificador(self):
        self.assertEqual(calcular_dv_rut("12345678"), "5")
        self.assertEqual(calcular_dv_rut("11111111"), "1")
        self.assertEqual(calcular_dv_rut("10000013"), "K")

    def test_rut_valido_no_lanza_error(self):
        validar_rut("12345678-5")
        validar_rut("10000013-k")  # minúscula se acepta

    def test_rut_con_dv_incorrecto(self):
        with self.assertRaisesMessage(ValidationError, "dígito verificador"):
            validar_rut("12345678-9")

    def test_rut_con_formato_incorrecto(self):
        with self.assertRaises(ValidationError):
            validar_rut("abc")


class RegistroTests(TestCase):
    def _datos(self, **extra):
        datos = {
            "username": "nuevo", "email": "nuevo@example.com", "rut": "12.345.678-5",
            "nombre_negocio": "Almacén", "tipo_negocio": "CO",
            "password1": CLAVE, "password2": CLAVE, "acepta_terminos": "on",
        }
        datos.update(extra)
        return datos

    def test_registro_normaliza_rut_con_puntos(self):
        self.client.post(reverse("accounts:registro"), self._datos())
        self.assertEqual(Usuario.objects.get().rut, "12345678-5")

    def test_registro_rechaza_rut_invalido(self):
        respuesta = self.client.post(reverse("accounts:registro"), self._datos(rut="12345678-9"))
        self.assertContains(respuesta, "dígito verificador")
        self.assertFalse(Usuario.objects.exists())

    def test_registro_rechaza_correo_repetido(self):
        crear_usuario("otro", "nuevo@example.com", "11111111-1")
        respuesta = self.client.post(reverse("accounts:registro"), self._datos())
        self.assertContains(respuesta, "Ya existe una cuenta con este correo")


class ConfiguracionTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario("dueno", "dueno@example.com", "11111111-1")
        self.client.force_login(self.usuario)

    def test_guardar_configuracion_y_meta_en_panel(self):
        self.client.post(
            reverse("accounts:configuracion"),
            {"regimen_tributario": "PP", "afecto_iva": "on", "meta_ventas_mensual": "1000000"},
        )
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.regimen_tributario, "PP")
        self.assertTrue(self.usuario.afecto_iva)
        self.assertContains(self.client.get(reverse("finances:dashboard")), "Meta de ventas del mes")

    def test_sin_inicio_de_actividades_no_puede_ser_afecto_a_iva(self):
        respuesta = self.client.post(
            reverse("accounts:configuracion"), {"regimen_tributario": "SI", "afecto_iva": "on"}
        )
        self.assertContains(respuesta, "Sin inicio de actividades no puedes")
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.afecto_iva)


class ColaboradoresTests(TestCase):
    def setUp(self):
        self.dueno = crear_usuario("dueno", "dueno@example.com", "11111111-1", "Verdulería")
        self.contador = crear_usuario("contador", "contador@example.com", "22222222-2", "Estudio")
        ventas = Categoria.objects.get(nombre="Ventas", usuario=None)
        Movimiento.objects.create(
            usuario=self.dueno, categoria=ventas, tipo="ingreso", monto=50000,
            fecha=timezone.localdate(), descripcion="Venta del dueño",
        )

    def _invitar(self, rol):
        self.client.force_login(self.dueno)
        self.client.post(reverse("accounts:colaboradores"), {"email": "Contador@example.com", "rol": rol})
        return Colaboracion.objects.get()

    def test_invitacion_envia_correo_con_enlace(self):
        invitacion = self._invitar("lector")
        self.assertEqual(invitacion.email, "contador@example.com")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(invitacion.token), mail.outbox[0].body)

    def test_no_se_puede_invitar_a_si_mismo(self):
        self.client.force_login(self.dueno)
        respuesta = self.client.post(
            reverse("accounts:colaboradores"), {"email": "dueno@example.com", "rol": "lector"}
        )
        self.assertContains(respuesta, "No puedes invitarte a ti mismo")

    def test_lector_ve_datos_del_negocio_pero_no_edita(self):
        invitacion = self._invitar("lector")
        self.client.force_login(self.contador)
        self.client.post(reverse("accounts:aceptar_invitacion", args=[invitacion.token]))

        panel = self.client.get(reverse("finances:dashboard"))
        self.assertContains(panel, "Venta del dueño")
        self.assertContains(panel, "modo solo lectura")
        self.assertNotContains(panel, "+ Nuevo movimiento")

        respuesta = self.client.get(reverse("finances:crear_movimiento"))
        self.assertRedirects(respuesta, reverse("finances:dashboard"))

    def test_editor_registra_movimientos_en_el_negocio_del_dueno(self):
        invitacion = self._invitar("editor")
        self.client.force_login(self.contador)
        self.client.post(reverse("accounts:aceptar_invitacion", args=[invitacion.token]))
        ventas = Categoria.objects.get(nombre="Ventas", usuario=None)
        self.client.post(
            reverse("finances:crear_movimiento"),
            {"tipo": "ingreso", "categoria": ventas.pk, "monto": "20000",
             "fecha": timezone.localdate().isoformat(), "descripcion": "Del contador"},
        )
        self.assertTrue(Movimiento.objects.filter(usuario=self.dueno, descripcion="Del contador").exists())
        self.assertFalse(Movimiento.objects.filter(usuario=self.contador).exists())

    def test_otro_correo_no_puede_aceptar(self):
        invitacion = self._invitar("editor")
        intruso = crear_usuario("intruso", "intruso@example.com", "33333333-3")
        self.client.force_login(intruso)
        respuesta = self.client.post(reverse("accounts:aceptar_invitacion", args=[invitacion.token]))
        self.assertContains(respuesta, "Esta invitación es para")
        invitacion.refresh_from_db()
        self.assertEqual(invitacion.estado, Colaboracion.Estado.PENDIENTE)

    def test_revocar_acceso_devuelve_al_negocio_propio(self):
        invitacion = self._invitar("lector")
        self.client.force_login(self.contador)
        self.client.post(reverse("accounts:aceptar_invitacion", args=[invitacion.token]))
        invitacion.delete()  # el dueño quitó el acceso
        panel = self.client.get(reverse("finances:dashboard"))
        self.assertNotContains(panel, "Venta del dueño")
        self.assertNotIn(SESION_NEGOCIO, self.client.session)

    def test_cambiar_negocio_solo_a_uno_permitido(self):
        self.client.force_login(self.contador)
        self.client.post(reverse("accounts:cambiar_negocio"), {"negocio_id": self.dueno.pk})
        self.assertNotIn(SESION_NEGOCIO, self.client.session)


class DatosPersonalesTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario("dueno", "dueno@example.com", "11111111-1")
        propia = Categoria.objects.create(nombre="Propia", tipo="gasto", usuario=self.usuario)
        Movimiento.objects.create(
            usuario=self.usuario, categoria=propia, tipo="gasto", monto=1000, fecha=timezone.localdate()
        )
        self.client.force_login(self.usuario)

    def test_exportar_datos_incluye_movimientos(self):
        respuesta = self.client.get(reverse("accounts:exportar_datos"))
        self.assertIn("attachment", respuesta["Content-Disposition"])
        datos = json.loads(respuesta.content)
        self.assertEqual(datos["perfil"]["rut"], "11111111-1")
        self.assertEqual(len(datos["movimientos"]), 1)

    def test_eliminar_cuenta_exige_contrasena(self):
        self.client.post(reverse("accounts:eliminar_cuenta"), {"password": "incorrecta"})
        self.assertTrue(Usuario.objects.filter(pk=self.usuario.pk).exists())

    def test_eliminar_cuenta_borra_todo(self):
        respuesta = self.client.post(reverse("accounts:eliminar_cuenta"), {"password": CLAVE})
        self.assertRedirects(respuesta, reverse("core:home"), fetch_redirect_response=False)
        self.assertFalse(Usuario.objects.filter(pk=self.usuario.pk).exists())
        self.assertFalse(Movimiento.objects.exists())
        self.assertFalse(Categoria.objects.filter(nombre="Propia").exists())


class RecuperarClaveTests(TestCase):
    def test_envia_correo_con_enlace_y_permite_cambiar_clave(self):
        crear_usuario("dueno", "dueno@example.com", "11111111-1")
        self.client.post(reverse("accounts:password_reset"), {"email": "dueno@example.com"})
        self.assertEqual(len(mail.outbox), 1)
        enlace = next(l for l in mail.outbox[0].body.splitlines() if "/clave/recuperar/" in l)
        ruta = enlace.split("testserver", 1)[1]
        respuesta = self.client.get(ruta, follow=True)
        self.assertContains(respuesta, "Nueva contraseña")
        nueva = "OtraClaveSegura.2027"
        self.client.post(respuesta.redirect_chain[-1][0], {"new_password1": nueva, "new_password2": nueva})
        self.assertTrue(self.client.login(username="dueno", password=nueva))

    def test_pantallas_publicas_cargan(self):
        self.assertContains(self.client.get(reverse("accounts:login")), "¿Olvidaste tu contraseña?")
        self.assertEqual(self.client.get(reverse("accounts:password_reset")).status_code, 200)


class CrearUsuariosPruebaTests(TestCase):
    def test_crea_cuentas_con_planes_y_datos(self):
        call_command("crear_usuarios_prueba", password=CLAVE, stdout=StringIO())
        basico = Usuario.objects.get(username="prueba_basico")
        premium = Usuario.objects.get(username="prueba_premium")
        nuevo = Usuario.objects.get(username="prueba_nuevo")
        self.assertFalse(basico.es_premium)
        self.assertTrue(premium.es_premium)
        self.assertEqual(nuevo.suscripcion_activa.plan.codigo, "basico")
        self.assertTrue(basico.movimientos.exists())
        self.assertFalse(nuevo.movimientos.exists())
        for usuario in (basico, premium, nuevo):
            validar_rut(usuario.rut)
        self.assertTrue(self.client.login(username="prueba_premium", password=CLAVE))
        # RF-29: la persona que use la cuenta de prueba acepta los términos al entrar.
        respuesta = self.client.get(reverse("finances:dashboard"))
        self.assertRedirects(respuesta, reverse("accounts:aceptar_terminos") + "?next=/finanzas/")
        self.client.post(reverse("accounts:aceptar_terminos"), {"acepta": "on", "next": "/finanzas/"})
        self.assertEqual(self.client.get(reverse("finances:dashboard")).status_code, 200)

    def test_no_duplica_si_se_ejecuta_dos_veces(self):
        call_command("crear_usuarios_prueba", password=CLAVE, stdout=StringIO())
        movimientos = Movimiento.objects.count()
        call_command("crear_usuarios_prueba", stdout=StringIO())
        self.assertEqual(Usuario.objects.filter(username__startswith="prueba_").count(), 3)
        self.assertEqual(Movimiento.objects.count(), movimientos)
        self.assertTrue(self.client.login(username="prueba_basico", password=CLAVE))


# ---------- RF-29: consentimiento ----------
from core.models import RegistroAuditoria

from .models import Consentimiento, DocumentoLegal


class ConsentimientoTests(TestCase):
    def _registrar(self, **extra):
        datos = {"username": "nuevo", "email": "nuevo@example.com", "rut": "12.345.678-5",
                 "nombre_negocio": "Almacén", "tipo_negocio": "CO", "password1": CLAVE, "password2": CLAVE}
        datos.update(extra)
        return self.client.post(reverse("accounts:registro"), datos, REMOTE_ADDR="10.1.2.3")

    def test_registro_exige_aceptar_y_guarda_version_fecha_e_ip(self):
        respuesta = self._registrar()
        self.assertContains(respuesta, "Debes aceptar los términos")
        self.assertFalse(Usuario.objects.exists())

        self._registrar(acepta_terminos="on")
        aceptados = Consentimiento.objects.filter(usuario__username="nuevo")
        self.assertEqual(sorted(aceptados.values_list("documento__tipo", flat=True)), ["privacidad", "terminos"])
        self.assertEqual({c.ip for c in aceptados}, {"10.1.2.3"})
        self.assertTrue(RegistroAuditoria.objects.filter(accion="consentimiento").exists())

    def test_version_nueva_se_pide_al_volver_a_entrar(self):
        usuario = crear_usuario("duena", "duena@example.com", "11111111-1")
        self.client.login(username="duena", password=CLAVE)
        self.assertEqual(self.client.get(reverse("finances:dashboard")).status_code, 200)

        nueva = DocumentoLegal.objects.create(tipo="privacidad", version="2.0", contenido="Texto nuevo")
        respuesta = self.client.get(reverse("finances:indicadores"))
        self.assertRedirects(respuesta, reverse("accounts:aceptar_terminos") + "?next=/finanzas/indicadores/")
        # Mientras tanto puede leer los documentos, descargar sus datos o eliminar su cuenta.
        self.assertEqual(self.client.get(reverse("documento_legal", args=["privacidad"])).status_code, 200)
        self.assertEqual(self.client.get(reverse("accounts:exportar_datos")).status_code, 200)

        pantalla = self.client.get(respuesta.url)
        self.assertContains(pantalla, "versión 2.0")
        self.assertNotContains(pantalla, "Términos y condiciones</a>")   # ya aceptó los términos vigentes
        respuesta = self.client.post(reverse("accounts:aceptar_terminos"),
                                     {"acepta": "on", "next": "https://malicioso.example/"})
        self.assertRedirects(respuesta, reverse("finances:dashboard"))
        self.assertTrue(Consentimiento.objects.filter(usuario=usuario, documento=nueva).exists())
        self.assertEqual(self.client.get(reverse("finances:indicadores")).status_code, 200)

    def test_documento_publico_con_huella(self):
        documento = DocumentoLegal.objects.get(tipo="terminos", version="1.0")
        self.assertEqual(len(documento.huella), 64)
        respuesta = self.client.get(reverse("documento_legal", args=["terminos"]))
        self.assertContains(respuesta, documento.huella)
        self.assertEqual(self.client.get(reverse("documento_legal", args=["otro"])).status_code, 404)

    def test_huella_cambia_con_el_contenido(self):
        a = DocumentoLegal.objects.create(tipo="terminos", version="9.0", contenido="A")
        b = DocumentoLegal.objects.create(tipo="terminos", version="9.1", contenido="B")
        self.assertNotEqual(a.huella, b.huella)
