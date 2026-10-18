from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


# Create your models here.
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

 
# Validación simple de formato de RUT chileno: 7 u 8 dígitos, guion, y
# dígito verificador (número o "K"). No calcula el dígito verificador
# real (eso se puede añadir después con la librería `python-rut` o una
# función utilitaria propia); esto solo evita errores de formato groseros
# al tipear.
validador_rut = RegexValidator(
    regex=r"^\d{7,8}-[\dkK]$",
    message="El RUT debe tener el formato 12345678-9 (sin puntos).",
)
 
 
class Usuario(AbstractUser):
    """Usuario de la plataforma: un microempresario chileno."""
 
    class TipoNegocio(models.TextChoices):
        FERIA_LIBRE = "FL", "Feria libre / comercio ambulante"
        COMERCIO = "CO", "Comercio establecido (almacén, botillería, etc.)"
        GASTRONOMIA = "GA", "Gastronomía (food truck, catering, delivery)"
        SERVICIOS = "SE", "Servicios (oficios, reparaciones, belleza, etc.)"
        ARTESANIA = "AR", "Artesanía y manufactura propia"
        OTRO = "OT", "Otro"
 
    rut = models.CharField(
        "RUT",
        max_length=10,
        unique=True,
        validators=[validador_rut],
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
 