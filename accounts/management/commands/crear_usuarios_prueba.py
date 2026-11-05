"""Crea usuarios de prueba para revisar la aplicación desplegada.

Uso (en el servidor):
    docker compose -f docker-compose.prod.yml exec web python manage.py crear_usuarios_prueba

Crea tres cuentas, cada una con su propio negocio:
    prueba_basico   Plan Básico, con 4 meses de movimientos de ejemplo
    prueba_premium  Plan Premium (evaluador de viabilidad), con movimientos
    prueba_nuevo    Plan Básico, sin datos (para probar desde cero)

Si una cuenta ya existe no se toca. Sin --password se genera una clave
aleatoria y se muestra al final.
"""
import secrets
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Usuario, calcular_dv_rut
from finances.models import Categoria, Movimiento
from subscriptions.models import Plan, Suscripcion
from subscriptions.services import asegurar_plan_basico, asegurar_plan_premium

# (usuario, negocio, número de RUT, plan, con datos de ejemplo)
CUENTAS = [
    ("prueba_basico", "Almacén de Prueba", "30000001", Plan.Codigo.BASICO, True),
    ("prueba_premium", "Taller de Prueba", "30000002", Plan.Codigo.PREMIUM, True),
    ("prueba_nuevo", "Negocio Nuevo de Prueba", "30000003", Plan.Codigo.BASICO, False),
]

# (categoría del sistema, tipo, monto base, descripción); se repite cada mes.
MOVIMIENTOS_MES = [
    ("Ventas", Categoria.Tipo.INGRESO, 1_450_000, "Ventas del mes"),
    ("Servicios prestados", Categoria.Tipo.INGRESO, 320_000, "Servicios a clientes"),
    ("Arriendo", Categoria.Tipo.GASTO, 350_000, "Arriendo del local"),
    ("Mercadería / insumos", Categoria.Tipo.GASTO, 610_000, "Compra de insumos"),
    ("Servicios básicos", Categoria.Tipo.GASTO, 85_000, "Luz, agua e internet"),
]
MESES_DE_EJEMPLO = 4


class Command(BaseCommand):
    help = "Crea usuarios de prueba (Básico, Premium y uno vacío) para revisar la app."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            help="Contraseña para todas las cuentas nuevas. Si se omite, se genera una.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        clave = options["password"] or f"Prueba-{secrets.token_urlsafe(9)}"
        creadas = []
        for username, negocio, numero_rut, codigo_plan, con_datos in CUENTAS:
            if Usuario.objects.filter(username=username).exists():
                self.stdout.write(f"{username}: ya existía, no se modificó.")
                continue
            usuario = Usuario.objects.create_user(
                username=username,
                email=f"{username}@finmicro.test",
                password=clave,
                rut=f"{numero_rut}-{calcular_dv_rut(numero_rut)}",
                nombre_negocio=negocio,
            )
            if codigo_plan == Plan.Codigo.PREMIUM:
                Suscripcion.objects.create(
                    usuario=usuario,
                    plan=asegurar_plan_premium(),
                    estado=Suscripcion.Estado.ACTIVA,
                    referencia_pago="usuario-de-prueba",
                )
            else:
                asegurar_plan_basico(usuario)
            if con_datos:
                self._crear_movimientos(usuario)
            creadas.append(username)

        if not creadas:
            self.stdout.write(self.style.WARNING("No se creó ninguna cuenta nueva."))
            return
        self.stdout.write(self.style.SUCCESS(f"Cuentas creadas: {', '.join(creadas)}"))
        self.stdout.write(self.style.SUCCESS(f"Contraseña de las cuentas nuevas: {clave}"))

    def _crear_movimientos(self, usuario):
        categorias = {
            (c.nombre, c.tipo): c for c in Categoria.objects.filter(usuario__isnull=True)
        }
        hoy = date.today()
        for meses_atras in range(MESES_DE_EJEMPLO):
            fecha = (hoy - relativedelta(months=meses_atras)).replace(day=min(hoy.day, 5))
            # Ingresos que crecen un poco cada mes, para que la proyección tenga tendencia.
            factor = Decimal(1) + Decimal("0.06") * (MESES_DE_EJEMPLO - meses_atras)
            for nombre, tipo, monto, descripcion in MOVIMIENTOS_MES:
                if tipo == Categoria.Tipo.INGRESO:
                    monto = Decimal(monto) * factor
                Movimiento.objects.create(
                    usuario=usuario,
                    categoria=categorias[(nombre, tipo)],
                    tipo=tipo,
                    monto=Decimal(monto).quantize(Decimal("1")),
                    fecha=fecha,
                    descripcion=descripcion,
                )
