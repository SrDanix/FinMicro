from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Colaboracion, Usuario


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
    list_filter = ("tipo_negocio", "regimen_tributario", "emite_boletas_honorarios", "is_active")
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
                    "regimen_tributario",
                    "afecto_iva",
                    "emite_boletas_honorarios",
                    "meta_ventas_mensual",
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


@admin.register(Colaboracion)
class ColaboracionAdmin(admin.ModelAdmin):
    list_display = ("email", "propietario", "colaborador", "rol", "estado", "creada_en")
    list_filter = ("rol", "estado")
    search_fields = ("email", "propietario__nombre_negocio")
