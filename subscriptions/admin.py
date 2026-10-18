from django.contrib import admin

# Register your models here.

from .models import Plan, Suscripcion


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "precio_mensual_clp", "con_publicidad", "activo")
    list_filter = ("activo", "con_publicidad")


@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ("usuario", "plan", "estado", "metodo_pago", "fecha_inicio", "fecha_fin")
    list_filter = ("estado", "metodo_pago", "plan")
    search_fields = ("usuario__username", "usuario__nombre_negocio", "referencia_pago")
    autocomplete_fields = ("usuario",)