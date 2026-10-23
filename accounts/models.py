"""
Modelo de usuario personalizado para FinMicro.

Reemplaza al User por defecto de Django para poder registrar, desde el
primer momento, los datos propios de un microempresario (RUT, nombre del
negocio, rubro). Se define un modelo de usuario propio en vez de usar un
perfil aparte porque es la práctica recomendada por Django cuando se sabe
de antemano que se necesitarán campos adicionales (evita una migración de
datos dolorosa más adelante).

Referencia en el informe: Sección I (perfil objetivo = "microempresario
informal") y Sección III (FODA / PESTEL: plataforma "adaptada al
microempresario informal").
"""
import re
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

_RUT_FORMATO = re.compile(r"^(\d{7,8})-([\dK])$")


def calcular_dv_rut(numero: str) -> str:
    """Dígito verificador de un RUT chileno (algoritmo módulo 11)."""
    suma, factor = 0, 2
    for digito in reversed(numero):
        suma += int(digito) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    return {11: "0", 10: "K"}.get(resto, str(resto))


def normalizar_rut(valor: str) -> str:
    """'12.345.678-k' -> '12345678-K'. No valida, solo limpia."""
    return (valor or "").replace(".", "").replace(" ", "").upper()


def validar_rut(valor):
    """Formato 12345678-9 (sin puntos) y dígito verificador correcto (RN-01)."""
    coincidencia = _RUT_FORMATO.match(normalizar_rut(valor))
    if not coincidencia:
        raise ValidationError("El RUT debe tener el formato 12345678-9.")
    numero, dv = coincidencia.groups()
    if calcular_dv_rut(numero) != dv:
        raise ValidationError("El RUT no es válido: el dígito verificador no coincide.")


class Usuario(AbstractUser):
    """Usuario de la plataforma: un microempresario chileno."""

    class TipoNegocio(models.TextChoices):
        FERIA_LIBRE = "FL", "Feria libre / comercio ambulante"
        COMERCIO = "CO", "Comercio establecido (almacén, botillería, etc.)"
        GASTRONOMIA = "GA", "Gastronomía (food truck, catering, delivery)"
        SERVICIOS = "SE", "Servicios (oficios, reparaciones, belleza, etc.)"
        ARTESANIA = "AR", "Artesanía y manufactura propia"
        OTRO = "OT", "Otro"

    class RegimenTributario(models.TextChoices):
        SIN_INICIO = "SI", "Sin inicio de actividades (informal)"
        PRO_PYME = "PP", "Régimen Pro Pyme General (14 D N°3)"
        PRO_PYME_TRANSPARENTE = "PT", "Régimen Pro Pyme Transparente (14 D N°8)"
        RENTA_PRESUNTA = "RP", "Renta presunta"
        GENERAL = "RG", "Régimen general semi integrado"

    rut = models.CharField(
        "RUT",
        max_length=10,
        unique=True,
        validators=[validar_rut],
        help_text="Formato 12345678-9, sin puntos.",
    )
    nombre_negocio = models.CharField("Nombre del negocio", max_length=150)
    tipo_negocio = models.CharField(
        "Rubro", max_length=2, choices=TipoNegocio.choices, default=TipoNegocio.OTRO
    )
    telefono = models.CharField("Teléfono", max_length=20, blank=True)
    comuna = models.CharField("Comuna", max_length=100, blank=True)
    emite_boletas_honorarios = models.BooleanField(
        "Emite boletas de honorarios",
        default=False,
        help_text="Determina si se le ofrece la calculadora de honorarios además de la de IVA.",
    )
    # --- Configuración tributaria y de metas (Sprint 1, RF-05) ---
    regimen_tributario = models.CharField(
        "Régimen tributario",
        max_length=2,
        choices=RegimenTributario.choices,
        default=RegimenTributario.SIN_INICIO,
    )
    afecto_iva = models.BooleanField(
        "Mis ventas están afectas a IVA",
        default=False,
        help_text="Márcalo si emites boletas o facturas afectas. Activa el recordatorio del F29.",
    )
    meta_ventas_mensual = models.PositiveIntegerField(
        "Meta de ventas mensual (CLP)",
        null=True,
        blank=True,
        help_text="Opcional. Se muestra tu avance en el panel.",
    )
    fecha_registro = models.DateTimeField("Fecha de registro", auto_now_add=True)

    REQUIRED_FIELDS = ["email", "rut", "nombre_negocio"]

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.nombre_negocio} ({self.username})"

    @property
    def suscripcion_activa(self):
        """Devuelve la Suscripcion vigente del usuario, o None.

        Se resuelve aquí (import local para evitar dependencia circular
        entre apps) para que cualquier vista o template pueda preguntar
        `usuario.suscripcion_activa` sin importar directamente el modelo
        de `subscriptions`.
        """
        return self.suscripciones.filter(estado="activa").order_by("-fecha_inicio").first()

    @property
    def es_premium(self):
        sub = self.suscripcion_activa
        return bool(sub and sub.plan.codigo == "premium")


class Colaboracion(models.Model):
    """Acceso de otra persona al negocio de un usuario (RF-06).

    El dueño invita por correo; la invitación queda PENDIENTE hasta que
    alguien con una cuenta registrada con ese mismo correo la acepta.
    """

    class Rol(models.TextChoices):
        LECTOR = "lector", "Solo lectura"
        EDITOR = "editor", "Puede registrar y editar movimientos"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        ACEPTADA = "aceptada", "Aceptada"

    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="colaboraciones_otorgadas"
    )
    colaborador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="colaboraciones",
        null=True,
        blank=True,
    )
    email = models.EmailField("Correo del colaborador")
    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.LECTOR)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Colaboración"
        verbose_name_plural = "Colaboraciones"
        ordering = ["-creada_en"]
        constraints = [
            models.UniqueConstraint(fields=["propietario", "email"], name="colaboracion_unica_por_email")
        ]

    def __str__(self):
        return f"{self.email} en {self.propietario.nombre_negocio} ({self.get_rol_display()})"
