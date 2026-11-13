"""RF-28: tarea diaria (cron) de renovación y vencimiento de suscripciones.

- Faltan 3 días o menos: avisa (alerta en el panel y correo) que debe renovar.
- Venció hace 3 días o menos: período de gracia, sigue en Premium con aviso urgente.
- Venció hace más: la suscripción queda vencida y el usuario vuelve al Plan Básico.

Uso: python manage.py renovar_suscripciones   (ver deploy/crontab.txt)
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils import timezone

from core.alertas import registrar as registrar_alerta
from core.models import Alerta
from subscriptions.models import Suscripcion
from subscriptions.services import AVISAR, GRACIA, VENCER, evaluar_renovacion, vencer_suscripcion


class Command(BaseCommand):
    help = "Avisa de suscripciones por vencer y devuelve al Plan Básico las vencidas."

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        conteo = {AVISAR: 0, GRACIA: 0, VENCER: 0}
        activas = Suscripcion.objects.filter(estado=Suscripcion.Estado.ACTIVA, fecha_fin__isnull=False).select_related("usuario", "plan")
        for suscripcion in activas:
            fin = timezone.localtime(suscripcion.fecha_fin).date()
            accion = evaluar_renovacion(fin, hoy)
            if accion not in conteo:
                continue
            conteo[accion] += 1
            usuario = suscripcion.usuario
            if accion == AVISAR:
                mensaje = f"Tu {suscripcion.plan.nombre} vence el {fin:%d-%m-%Y}. Renuévalo para no perder sus funciones."
                codigo, severidad = f"SUSC-AVISO-{suscripcion.pk}", Alerta.Severidad.AVISO
            elif accion == GRACIA:
                mensaje = f"Tu {suscripcion.plan.nombre} venció el {fin:%d-%m-%Y}. Tienes unos días de gracia para renovarlo."
                codigo, severidad = f"SUSC-GRACIA-{suscripcion.pk}", Alerta.Severidad.URGENTE
            else:
                vencer_suscripcion(suscripcion)
                mensaje = f"Tu {suscripcion.plan.nombre} venció y volviste al Plan Básico. Tus datos se mantienen."
                codigo, severidad = f"SUSC-VENCIDA-{suscripcion.pk}", Alerta.Severidad.URGENTE
            _, creada = registrar_alerta(usuario, codigo, severidad, mensaje, enlace=reverse("subscriptions:mi_suscripcion"))
            if creada and usuario.email:
                send_mail("FinMicro: estado de tu suscripción", mensaje, settings.DEFAULT_FROM_EMAIL,
                          [usuario.email], fail_silently=True)
        self.stdout.write(self.style.SUCCESS(
            f"Avisos: {conteo[AVISAR]} · En gracia: {conteo[GRACIA]} · Vencidas: {conteo[VENCER]}"
        ))
