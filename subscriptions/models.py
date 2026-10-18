"""
Modelo freemium de FinMicro: Plan Básico (gratis, con publicidad) y Plan
Premium ($9.990 CLP/mes) — Sección 5.1 del informe ("Fuentes de Ingresos").
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Plan(models.Model):
    class Codigo(models.TextChoices):
        BASICO = "basico", "Plan Básico"
        PREMIUM = "premium", "Plan Premium"

    codigo = models.CharField(max_length=20, choices=Codigo.choices, unique=True)
    nombre = models.CharField(max_length=100)
    precio_mensual_clp = models.PositiveIntegerField(
        help_text="0 para el plan gratuito. Tabla 5 del informe: Premium = $9.990 CLP/mes."
    )
    con_publicidad = models.BooleanField(default=False)
    limite_movimientos_mensuales = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Tope de movimientos financieros por mes. Vacío = ilimitado (Premium).",
    )
    incluye_proyecciones = models.BooleanField(
        default=True, help_text="Acceso al módulo de proyección de ingresos."
    )
    incluye_evaluador_viabilidad = models.BooleanField(
        default=False,
        help_text="Acceso a la calculadora VAN/TIR/Payback para el propio negocio del usuario.",
    )
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Planes"
        ordering = ["precio_mensual_clp"]

    def __str__(self):
        return self.nombre


class Suscripcion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pago pendiente"
        ACTIVA = "activa", "Activa"
        CANCELADA = "cancelada", "Cancelada"
        VENCIDA = "vencida", "Vencida"

    class MetodoPago(models.TextChoices):
        NINGUNO = "ninguno", "Sin costo (Plan Básico)"
        KHIPU = "khipu", "Khipu"
        FLOW = "flow", "Flow.cl"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="suscripciones"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="suscripciones")
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    metodo_pago = models.CharField(
        max_length=20, choices=MetodoPago.choices, default=MetodoPago.NINGUNO
    )
    referencia_pago = models.CharField(
        "ID de transacción en la pasarela",
        max_length=100,
        blank=True,
        help_text="payment_id (Khipu) o token/flowOrder (Flow.cl).",
    )
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Suscripción"
        verbose_name_plural = "Suscripciones"
        ordering = ["-creada_en"]

    def __str__(self):
        return f"{self.usuario} — {self.plan} ({self.get_estado_display()})"

    def activar(self):
        self.estado = self.Estado.ACTIVA
        if not self.fecha_inicio:
            self.fecha_inicio = timezone.now()
        self.save(update_fields=["estado", "fecha_inicio"])