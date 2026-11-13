from django.contrib import admin

from .models import Alerta


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ("negocio", "severidad", "mensaje", "creada_en", "leida")
    list_filter = ("severidad", "leida")
    search_fields = ("negocio__username", "mensaje", "codigo")
