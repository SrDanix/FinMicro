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


class RegistroAuditoria(models.Model):
    """RF-32: registro de acciones sensibles. Solo se agrega; nunca se edita ni se borra desde la app.

    Guarda el nombre de usuario como texto para que el registro sobreviva
    aunque la cuenta se elimine (RF-07).
    """

    class Accion(models.TextChoices):
        INICIO_SESION = "login", "Inicio de sesión"
        INICIO_FALLIDO = "login_fallido", "Inicio de sesión fallido"
        CIERRE_SESION = "logout", "Cierre de sesión"
        CAMBIO_PLAN = "cambio_plan", "Cambio de plan"
        PAGO = "pago", "Pago de suscripción"
        VENCIMIENTO_PLAN = "vencimiento_plan", "Vencimiento de plan"
        ELIMINAR_MOVIMIENTO = "eliminar_movimiento", "Eliminación de movimiento"
        IMPORTAR = "importar", "Importación de movimientos"
        EXPORTAR_DATOS = "exportar_datos", "Exportación de datos personales"
        ELIMINAR_CUENTA = "eliminar_cuenta", "Eliminación de cuenta"
        COLABORADOR = "colaborador", "Cambio de colaboradores"
        CONSENTIMIENTO = "consentimiento", "Aceptación de términos"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    nombre_usuario = models.CharField(max_length=150, blank=True)
    accion = models.CharField(max_length=30, choices=Accion.choices)
    detalle = models.CharField(max_length=300, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Registros de auditoría"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.creado_en:%d-%m-%Y %H:%M} {self.nombre_usuario} {self.get_accion_display()}"


class ConsultaAsistente(models.Model):
    """RF-37: preguntas al asistente y sus respuestas, para el historial y el tope diario."""

    negocio = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consultas_asistente")
    pregunta = models.CharField(max_length=500)
    respuesta = models.TextField()
    creada_en = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Consulta al asistente"
        verbose_name_plural = "Consultas al asistente"
        ordering = ["-creada_en"]

    def __str__(self):
        return self.pregunta[:60]
