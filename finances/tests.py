"""Pruebas de RF-10 (búsqueda), RF-11 (catálogo), RF-16 (flujo de caja), RF-17 y RF-19 (indicadores)."""
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Colaboracion, Usuario
from accounts.negocio import SESION_NEGOCIO
from subscriptions.services import asegurar_plan_basico

from .models import Categoria, Movimiento, Producto
from .services import (
    FlujoCaja,
    clasificar_costos,
    flujo_de_caja,
    indicadores_del_mes,
    margen_bruto,
    normalizar_texto,
    punto_equilibrio,
    ticket_promedio,
)

CLAVE = "UnaClaveSegura.2026"


def crear_usuario(username, rut, **extra):
    usuario = Usuario.objects.create_user(
        username=username, email=f"{username}@example.com", password=CLAVE, rut=rut,
        nombre_negocio=f"Negocio {username}", **extra,
    )
    asegurar_plan_basico(usuario)
    return usuario


def categoria(nombre, tipo="gasto"):
    return Categoria.objects.get(nombre=nombre, tipo=tipo, usuario=None)


def mov(usuario, nombre_categoria, monto, fecha, descripcion="", tipo=None):
    cat = categoria(nombre_categoria, tipo or ("ingreso" if nombre_categoria in ("Ventas", "Servicios prestados", "Otros ingresos") else "gasto"))
    return Movimiento.objects.create(
        usuario=usuario, categoria=cat, tipo=cat.tipo, monto=Decimal(monto), fecha=fecha, descripcion=descripcion
    )


class CalculosTests(SimpleTestCase):
    """Valores calculados a mano (DoD punto 7)."""

    def test_normalizar_texto_ignora_tildes_y_mayusculas(self):
        self.assertEqual(normalizar_texto("  Café CON Leche "), "cafe con leche")
        self.assertEqual(normalizar_texto(None), "")

    def test_margen_bruto(self):
        self.assertEqual(margen_bruto(1_000_000, 400_000), (Decimal("600000"), Decimal("60.0")))
        self.assertEqual(margen_bruto(0, 50_000), (Decimal("-50000"), None))

    def test_punto_equilibrio(self):
        # Contribución = 1 − 400.000/1.000.000 = 0,6 → 300.000 / 0,6 = 500.000.
        self.assertEqual(punto_equilibrio(1_000_000, 400_000, 300_000), Decimal("500000"))
        self.assertIsNone(punto_equilibrio(0, 0, 300_000))
        # Si los gastos variables igualan o superan las ventas no hay equilibrio posible.
        self.assertIsNone(punto_equilibrio(100_000, 100_000, 50_000))

    def test_ticket_promedio_redondea_al_peso(self):
        self.assertEqual(ticket_promedio(100_000, 3), Decimal("33333"))
        self.assertIsNone(ticket_promedio(100_000, 0))

    def test_clasificar_costos_y_porcentajes(self):
        desglose = clasificar_costos([(100, "fijo"), (50, "variable"), (25, "")])
        self.assertEqual((desglose.fijos, desglose.variables, desglose.sin_clasificar), (100, 50, 25))
        # 100/175 = 57,1 % · 50/175 = 28,6 % · 25/175 = 14,3 %
        self.assertEqual(
            (desglose.porcentaje_fijos, desglose.porcentaje_variables, desglose.porcentaje_sin_clasificar),
            (57, 29, 14),
        )
        self.assertIsNone(clasificar_costos([]).porcentaje_fijos)

    def test_flujo_caja_y_diferencia_con_proyeccion(self):
        flujo = FlujoCaja(date(2026, 10, 1), Decimal(400), Decimal(300), Decimal(150), proyectado=Decimal(350))
        self.assertEqual(flujo.flujo_neto, 150)
        self.assertEqual(flujo.saldo_final, 550)
        self.assertEqual(flujo.diferencia_con_proyeccion, -50)
        self.assertEqual(flujo.diferencia_absoluta, 50)


class IndicadoresConsultaTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario("almacen", "11111111-1", saldo_caja_inicial=100_000)
        self.mes = timezone.localdate().replace(day=1)
        anterior = self.mes - relativedelta(months=1)
        mov(self.usuario, "Ventas", 500_000, anterior)
        mov(self.usuario, "Arriendo", 200_000, anterior)
        mov(self.usuario, "Ventas", 200_000, self.mes, "Venta mañana")
        mov(self.usuario, "Ventas", 100_000, self.mes, "Venta tarde")
        mov(self.usuario, "Arriendo", 100_000, self.mes)               # fijo
        mov(self.usuario, "Mercadería / insumos", 50_000, self.mes)   # variable
        mov(self.usuario, "Otros gastos", 25_000, self.mes)           # sin clasificar
        # Otro negocio con datos que no deben mezclarse (RNF-03).
        otro = crear_usuario("otro", "22222222-2")
        mov(otro, "Ventas", 9_999_999, self.mes)

    def test_indicadores_del_mes(self):
        datos = indicadores_del_mes(self.usuario, self.mes)
        self.assertEqual(datos["ventas"], 300_000)
        self.assertEqual(datos["cantidad_ventas"], 2)
        self.assertEqual(datos["ticket_promedio"], 150_000)
        self.assertEqual(datos["margen_bruto"], 250_000)            # 300.000 − 50.000 variables
        # PE = 100.000 / (1 − 50.000/300.000) = 120.000
        self.assertEqual(datos["punto_equilibrio"], 120_000)
        self.assertEqual(datos["costos"].sin_clasificar, 25_000)
        self.assertEqual(datos["utilidad"], 125_000)

    def test_flujo_de_caja_arrastra_saldo_de_meses_anteriores(self):
        flujo = flujo_de_caja(self.usuario, self.mes)
        self.assertEqual(flujo.saldo_inicial, 400_000)              # 100.000 + 500.000 − 200.000
        self.assertEqual(flujo.entradas, 300_000)
        self.assertEqual(flujo.salidas, 175_000)
        self.assertEqual(flujo.saldo_final, 525_000)
        self.assertIsNone(flujo.proyectado)                         # un solo mes previo con ingresos

    def test_flujo_compara_con_proyeccion_cuando_hay_historial(self):
        dos_meses = self.mes - relativedelta(months=2)
        mov(self.usuario, "Ventas", 400_000, dos_meses)
        # Historial 400.000 → 500.000: la tendencia proyecta 600.000 para este mes.
        flujo = flujo_de_caja(self.usuario, self.mes)
        self.assertEqual(flujo.proyectado, 600_000)
        self.assertEqual(flujo.diferencia_con_proyeccion, -300_000)

    def test_pantalla_de_indicadores(self):
        self.client.login(username="almacen", password=CLAVE)
        respuesta = self.client.get(reverse("finances:indicadores"))
        self.assertContains(respuesta, "120.000")                   # punto de equilibrio
        self.assertContains(respuesta, "525.000")                   # saldo final
        self.assertNotContains(respuesta, "9.999.999")
        # Un mes inválido o futuro no rompe la página.
        self.assertEqual(self.client.get(reverse("finances:indicadores") + "?mes=abc").status_code, 200)
        self.assertEqual(self.client.get(reverse("finances:indicadores") + "?mes=2999-01").status_code, 200)


class BusquedaTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario("feria", "11111111-1")
        hoy = timezone.localdate()
        mov(self.usuario, "Ventas", 1000, hoy, "Venta de café en la feria")
        mov(self.usuario, "Arriendo", 2000, hoy, "Puesto de la feria")
        mov(self.usuario, "Transporte", 3000, hoy, "Bencina")
        self.client.login(username="feria", password=CLAVE)

    def _buscar(self, texto, **extra):
        return self.client.get(reverse("finances:listar_movimientos"), {"q": texto, **extra})

    def test_busca_en_descripcion_sin_tildes_ni_mayusculas(self):
        respuesta = self._buscar("CAFE")
        self.assertContains(respuesta, "Venta de café")
        self.assertNotContains(respuesta, "Bencina")

    def test_busca_en_nombre_de_categoria(self):
        respuesta = self._buscar("transpórte")
        self.assertContains(respuesta, "Bencina")
        self.assertNotContains(respuesta, "Puesto de la feria")

    def test_combina_texto_con_tipo(self):
        respuesta = self._buscar("feria", tipo="gasto")
        self.assertContains(respuesta, "Puesto de la feria")
        self.assertNotContains(respuesta, "Venta de café")

    def test_sin_resultados(self):
        self.assertContains(self._buscar("zapatos"), "No hay movimientos")


class CatalogoTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario("panaderia", "11111111-1")
        self.client.login(username="panaderia", password=CLAVE)

    def test_crud_de_producto(self):
        self.client.post(reverse("finances:crear_producto"), {"nombre": "Marraqueta", "precio": "1500", "afecto_iva": "on", "activo": "on"})
        producto = Producto.objects.get(usuario=self.usuario)
        self.assertContains(self.client.get(reverse("finances:listar_productos")), "Marraqueta")

        self.client.post(reverse("finances:editar_producto", args=[producto.pk]), {"nombre": "Marraqueta", "precio": "1600"})
        producto.refresh_from_db()
        self.assertEqual((producto.precio, producto.activo), (1600, False))

        self.client.post(reverse("finances:eliminar_producto", args=[producto.pk]))
        self.assertFalse(Producto.objects.exists())

    def test_nombre_repetido_se_rechaza(self):
        Producto.objects.create(usuario=self.usuario, nombre="Hallulla", precio=1200)
        respuesta = self.client.post(reverse("finances:crear_producto"), {"nombre": "hallulla", "precio": "1300"})
        self.assertContains(respuesta, "Ya tienes un producto con ese nombre")

    def test_venta_desde_producto_calcula_el_monto(self):
        producto = Producto.objects.create(usuario=self.usuario, nombre="Torta", precio=12_500)
        self.client.post(reverse("finances:crear_movimiento"), {
            "tipo": "ingreso", "categoria": categoria("Ventas", "ingreso").pk, "producto": producto.pk,
            "cantidad": "3", "monto": "", "fecha": timezone.localdate().isoformat(), "descripcion": "",
        })
        venta = Movimiento.objects.get()
        self.assertEqual((venta.monto, venta.cantidad, venta.producto), (37_500, 3, producto))
        self.assertEqual(venta.descripcion, "3 × Torta")

    def test_sin_monto_ni_producto_se_rechaza(self):
        respuesta = self.client.post(reverse("finances:crear_movimiento"), {
            "tipo": "ingreso", "categoria": categoria("Ventas", "ingreso").pk, "monto": "",
            "fecha": timezone.localdate().isoformat(),
        })
        self.assertContains(respuesta, "Ingresa el monto o elige un producto")
        self.assertFalse(Movimiento.objects.exists())

    def test_producto_en_un_gasto_se_rechaza(self):
        producto = Producto.objects.create(usuario=self.usuario, nombre="Torta", precio=12_500)
        respuesta = self.client.post(reverse("finances:crear_movimiento"), {
            "tipo": "gasto", "categoria": categoria("Arriendo").pk, "producto": producto.pk,
            "monto": "1000", "fecha": timezone.localdate().isoformat(),
        })
        self.assertContains(respuesta, "Solo las ventas")
        self.assertFalse(Movimiento.objects.exists())

    def test_aislamiento_entre_negocios(self):
        ajeno = Producto.objects.create(usuario=crear_usuario("otro", "22222222-2"), nombre="Secreto", precio=1)
        self.assertNotContains(self.client.get(reverse("finances:listar_productos")), "Secreto")
        self.assertEqual(self.client.get(reverse("finances:editar_producto", args=[ajeno.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("finances:crear_movimiento")), "Secreto")
        respuesta = self.client.post(reverse("finances:crear_movimiento"), {
            "tipo": "ingreso", "categoria": categoria("Ventas", "ingreso").pk, "producto": ajeno.pk,
            "cantidad": "1", "fecha": timezone.localdate().isoformat(),
        })
        self.assertEqual(respuesta.status_code, 200)               # formulario con error, no guarda
        self.assertFalse(Movimiento.objects.exists())

    def test_colaborador_lector_no_edita_el_catalogo(self):
        lector = crear_usuario("contador", "22222222-2")
        Colaboracion.objects.create(propietario=self.usuario, colaborador=lector, email=lector.email,
                                    rol=Colaboracion.Rol.LECTOR, estado=Colaboracion.Estado.ACEPTADA)
        self.client.login(username="contador", password=CLAVE)
        sesion = self.client.session
        sesion[SESION_NEGOCIO] = self.usuario.pk
        sesion.save()
        self.client.post(reverse("finances:crear_producto"), {"nombre": "Intruso", "precio": "1"})
        self.assertFalse(Producto.objects.exists())


class CategoriaNaturalezaTests(TestCase):
    def test_categorias_del_sistema_vienen_clasificadas(self):
        self.assertEqual(categoria("Arriendo").naturaleza, "fijo")
        self.assertEqual(categoria("Mercadería / insumos").naturaleza, "variable")
        self.assertEqual(categoria("Otros gastos").naturaleza, "")

    def test_categoria_propia_de_ingreso_no_guarda_naturaleza(self):
        crear_usuario("taller", "11111111-1")
        self.client.login(username="taller", password=CLAVE)
        self.client.post(reverse("finances:crear_categoria"), {"nombre": "Propinas", "tipo": "ingreso", "naturaleza": "fijo"})
        self.assertEqual(Categoria.objects.get(nombre="Propinas").naturaleza, "")
