"""
Parámetros tributarios editables desde el administrador de Django.

- `TasaTributaria` (RF-25): las tasas dejan de estar fijas en el código.
  Cada tasa tiene una vigencia; para un cambio legal se agrega una fila
  nueva con su fecha de inicio, sin desplegar código.
- `Feriado` (RF-23): días no hábiles que corren los vencimientos al día
  hábil siguiente.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class TasaTributaria(models.Model):
    class Codigo(models.TextChoices):
        IVA = "IVA", "IVA"
        RETENCION_HONORARIOS = "RET_HON", "Retención boletas de honorarios"

    codigo = models.CharField(max_length=10, choices=Codigo.choices)
    valor = models.DecimalField(
        "Tasa (fracción)",
        max_digits=6,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
        help_text="0,19 = 19 %.",
    )
    vigente_desde = models.DateField()
    vigente_hasta = models.DateField(null=True, blank=True, help_text="Vacío = sin término definido.")
    fuente = models.CharField(max_length=200, help_text="Ley o circular que respalda la tasa.")
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tasa tributaria"
        verbose_name_plural = "Tasas tributarias"
        ordering = ["codigo", "-vigente_desde"]
        constraints = [
            models.UniqueConstraint(fields=["codigo", "vigente_desde"], name="tasa_unica_por_inicio")
        ]

    def __str__(self):
        return f"{self.get_codigo_display()} {self.porcentaje}% desde {self.vigente_desde:%d-%m-%Y}"

    @property
    def porcentaje(self):
        return (self.valor * 100).normalize()

    def clean(self):
        if self.vigente_hasta and self.vigente_hasta < self.vigente_desde:
            raise ValidationError({"vigente_hasta": "El término no puede ser anterior al inicio."})


class Feriado(models.Model):
    fecha = models.DateField(unique=True)
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Feriado"
        verbose_name_plural = "Feriados"
        ordering = ["fecha"]

    def __str__(self):
        return f"{self.fecha:%d-%m-%Y} {self.nombre}"
