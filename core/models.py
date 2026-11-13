"""
Modelos transversales a todas las apps.

- `Alerta` (RF-24): avisos para el negocio (vencimientos tributarios,
  límite del plan y gastos inusuales). El código identifica la alerta y
  evita duplicarla: la misma situación nunca genera dos avisos.
"""
from django.conf import settings
from django.db import models


class Alerta(models.Model):
    class Severidad(models.TextChoices):
        INFO = "info", "Información"
        AVISO = "aviso", "Aviso"
        URGENTE = "urgente", "Urgente"

    negocio = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alertas"
    )
    codigo = models.CharField(max_length=60, help_text="Identifica la situación, p. ej. VENC-F29-2026-10.")
    severidad = models.CharField(max_length=10, choices=Severidad.choices, default=Severidad.INFO)
    mensaje = models.CharField(max_length=300)
    enlace = models.CharField(max_length=200, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        ordering = ["leida", "-creada_en"]
        constraints = [
            models.UniqueConstraint(fields=["negocio", "codigo"], name="alerta_unica_por_negocio")
        ]

    def __str__(self):
        return f"[{self.get_severidad_display()}] {self.mensaje}"
