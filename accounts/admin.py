from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Colaboracion, Consentimiento, DocumentoLegal, Usuario


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
                    "saldo_caja_inicial",
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


@admin.register(DocumentoLegal)
class DocumentoLegalAdmin(admin.ModelAdmin):
    """RF-29: un documento publicado no se modifica; para cambiarlo se agrega una versión nueva."""

    list_display = ("tipo", "version", "vigente_desde", "huella")
    list_filter = ("tipo",)
    readonly_fields = ("huella",)

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return ("tipo", "version", "contenido", "vigente_desde", "huella")
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Consentimiento)
class ConsentimientoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "documento", "aceptado_en", "ip")
    list_filter = ("documento",)
    search_fields = ("usuario__username", "usuario__rut")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
