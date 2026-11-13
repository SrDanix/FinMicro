"""
Gestión financiera del microempresario: categorías, ingresos y gastos.
Es el módulo base sobre el que se apoyan `taxes` (calcula impuestos a
partir de ventas/compras) y `projections` (proyecta ingresos futuros a
partir del historial de Movimiento).

Referencia: Objetivo específico 1 del informe — "Identificar y proyectar
las fuentes de ingresos y los costos fijos y variables del proyecto".
Aquí se implementa el lado operativo de esa idea, pero para el negocio
del propio usuario de la plataforma (no para FinMicro como empresa).
"""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Categoria(models.Model):
    class Tipo(models.TextChoices):
        INGRESO = "ingreso", "Ingreso"
        GASTO = "gasto", "Gasto"

    class Naturaleza(models.TextChoices):
        FIJO = "fijo", "Fijo"
        VARIABLE = "variable", "Variable"

    nombre = models.CharField(max_length=80)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    # NULL = categoría "del sistema" (visible para todos). Si el usuario
    # crea su propia categoría, queda asociada solo a él.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categorias",
        null=True,
        blank=True,
    )
    es_gravable_iva = models.BooleanField(
        "Afecta a IVA",
        default=True,
        help_text="Si el movimiento en esta categoría debe considerarse en la calculadora de IVA.",
    )
    # RF-19: solo aplica a gastos. Vacío = sin clasificar (se informa aparte).
    naturaleza = models.CharField(
        "Tipo de gasto",
        max_length=10,
        choices=Naturaleza.choices,
        blank=True,
        help_text="Fijo: se paga igual aunque vendas poco (arriendo). Variable: sube con las ventas (mercadería).",
    )

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["tipo", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["nombre", "tipo", "usuario"], name="categoria_unica_por_usuario"
            )
        ]

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    def clean(self):
        if self.tipo == self.Tipo.INGRESO:
            self.naturaleza = ""


class Producto(models.Model):
    """RF-11: producto o servicio que el negocio vende, con su precio."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="productos"
    )
    nombre = models.CharField(max_length=120)
    precio = models.DecimalField(
        "Precio unitario (CLP)", max_digits=12, decimal_places=0,
        validators=[MinValueValidator(Decimal("1"))],
    )
    afecto_iva = models.BooleanField("Afecto a IVA", default=True)
    activo = models.BooleanField(
        default=True, help_text="Los productos inactivos no aparecen al registrar ventas."
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Producto o servicio"
        verbose_name_plural = "Productos y servicios"
        ordering = ["-activo", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["usuario", "nombre"], name="producto_unico_por_negocio")
        ]

    def __str__(self):
        return self.nombre


class Movimiento(models.Model):
    """Un ingreso o un gasto registrado por el microempresario."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="movimientos"
    )
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name="movimientos"
    )
    tipo = models.CharField(max_length=10, choices=Categoria.Tipo.choices)
    # RF-11: venta registrada desde el catálogo (opcional).
    producto = models.ForeignKey(
        Producto, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimientos"
    )
    cantidad = models.PositiveIntegerField(null=True, blank=True)
    monto = models.DecimalField(
        "Monto (CLP)", max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("1"))]
    )
    fecha = models.DateField()
    descripcion = models.CharField(max_length=255, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ["-fecha", "-creado_en"]
        indexes = [models.Index(fields=["usuario", "fecha"])]

    def __str__(self):
        signo = "+" if self.tipo == Categoria.Tipo.INGRESO else "-"
        return f"{signo}${self.monto} — {self.categoria} ({self.fecha})"

    def save(self, *args, **kwargs):
        if self.categoria_id and not self.tipo:
            self.tipo = self.categoria.tipo
        super().save(*args, **kwargs)

    def clean(self):
        # El tipo del movimiento debe ser consistente con el tipo de su
        # categoría; evita que un "Arriendo" (gasto) quede cargado como
        # ingreso por error de formulario.
        if self.categoria_id and self.tipo != self.categoria.tipo:
            raise ValidationError(
                {"categoria": "La categoría elegida no coincide con el tipo de movimiento."}
            )
        if self.producto_id and self.tipo != Categoria.Tipo.INGRESO:
            raise ValidationError({"producto": "Solo las ventas (ingresos) llevan producto."})