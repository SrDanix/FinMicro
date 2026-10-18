from django.contrib import admin

# Register your models here.

from .models import Categoria, Movimiento


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "usuario", "es_gravable_iva")
    list_filter = ("tipo", "es_gravable_iva")
    search_fields = ("nombre",)


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "tipo", "categoria", "monto", "fecha")
    list_filter = ("tipo", "categoria")
    date_hierarchy = "fecha"
    search_fields = ("usuario__username", "descripcion")