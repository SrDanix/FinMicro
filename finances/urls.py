from django.urls import path

from . import views

app_name = "finances"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("movimientos/", views.listar_movimientos, name="listar_movimientos"),
    path("movimientos/nuevo/", views.crear_movimiento, name="crear_movimiento"),
    path("movimientos/<int:pk>/editar/", views.editar_movimiento, name="editar_movimiento"),
    path("movimientos/<int:pk>/eliminar/", views.eliminar_movimiento, name="eliminar_movimiento"),
    path("categorias/nueva/", views.crear_categoria, name="crear_categoria"),
]