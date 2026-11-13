from django.contrib import admin

from .models import Feriado, TasaTributaria


@admin.register(TasaTributaria)
class TasaTributariaAdmin(admin.ModelAdmin):
    """RF-25: para un cambio legal se agrega una tasa nueva con su fecha de inicio."""

    list_display = ("codigo", "porcentaje", "vigente_desde", "vigente_hasta", "fuente", "actualizada_en")
    list_filter = ("codigo",)
    ordering = ("codigo", "-vigente_desde")


@admin.register(Feriado)
class FeriadoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "nombre")
    date_hierarchy = "fecha"
