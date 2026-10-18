from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Panel de administración del usuario, extendiendo el UserAdmin de
    Django para no perder las secciones de permisos/grupos ya probadas."""

    list_display = (
        "username",
        "nombre_negocio",
        "rut",
        "tipo_negocio",
        "email",
        "is_active",
        "fecha_registro",
    )
    list_filter = ("tipo_negocio", "emite_boletas_honorarios", "is_active")
    search_fields = ("username", "nombre_negocio", "rut", "email")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Datos del negocio (FinMicro)",
            {
                "fields": (
                    "rut",
                    "nombre_negocio",
                    "tipo_negocio",
                    "telefono",
                    "comuna",
                    "emite_boletas_honorarios",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Datos del negocio (FinMicro)",
            {
                "fields": (
                    "email",
                    "rut",
                    "nombre_negocio",
                    "tipo_negocio",
                )
            },
        ),
    )