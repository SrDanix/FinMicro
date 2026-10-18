from django.core.management.base import BaseCommand

from subscriptions.services import asegurar_plan_premium
from subscriptions.models import Plan


class Command(BaseCommand):
    help = "Crea (o actualiza) los planes Básico y Premium descritos en la Sección 5.1 del informe."

    def handle(self, *args, **options):
        basico, creado_b = Plan.objects.get_or_create(
            codigo=Plan.Codigo.BASICO,
            defaults={
                "nombre": "Plan Básico",
                "precio_mensual_clp": 0,
                "con_publicidad": True,
                "limite_movimientos_mensuales": 60,
                "descripcion": "Gratis, financiado con publicidad.",
            },
        )
        premium = asegurar_plan_premium()

        self.stdout.write(self.style.SUCCESS(f"Plan Básico: {'creado' if creado_b else 'ya existía'} (id={basico.id})"))
        self.stdout.write(self.style.SUCCESS(f"Plan Premium listo (id={premium.id}, ${premium.precio_mensual_clp} CLP/mes)"))