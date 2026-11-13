"""RF-24: tarea diaria (cron) que genera alertas de vencimiento y avisa por correo.

Uso: python manage.py generar_alertas
En el servidor, ver deploy/crontab.txt.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Usuario
from core.alertas import revisar_vencimientos


class Command(BaseCommand):
    help = "Genera las alertas de vencimientos tributarios de todos los negocios y avisa por correo."

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        total = 0
        for negocio in Usuario.objects.filter(is_active=True).exclude(regimen_tributario="SI", emite_boletas_honorarios=False):
            nuevas = revisar_vencimientos(negocio, hoy)
            total += len(nuevas)
            if nuevas and negocio.email:
                send_mail(
                    "FinMicro: tienes vencimientos tributarios próximos",
                    "\n".join(a.mensaje for a in nuevas)
                    + "\n\nRevisa tu calendario tributario en FinMicro. Valida siempre en sii.cl.",
                    settings.DEFAULT_FROM_EMAIL,
                    [negocio.email],
                    fail_silently=True,
                )
        self.stdout.write(self.style.SUCCESS(f"Alertas nuevas: {total}"))
