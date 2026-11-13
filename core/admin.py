from django.contrib import admin

from .models import Alerta, RegistroAuditoria


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ("negocio", "severidad", "mensaje", "creada_en", "leida")
    list_filter = ("severidad", "leida")
    search_fields = ("negocio__username", "mensaje", "codigo")


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    """RF-32: de solo lectura. Nadie, ni un superusuario, lo edita o borra desde el administrador."""

    list_display = ("creado_en", "nombre_usuario", "accion", "detalle", "ip")
    list_filter = ("accion",)
    search_fields = ("nombre_usuario", "detalle", "ip")
    date_hierarchy = "creado_en"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
