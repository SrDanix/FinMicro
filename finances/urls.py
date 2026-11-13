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
    path("productos/", views.listar_productos, name="listar_productos"),
    path("productos/nuevo/", views.crear_producto, name="crear_producto"),
    path("productos/<int:pk>/editar/", views.editar_producto, name="editar_producto"),
    path("productos/<int:pk>/eliminar/", views.eliminar_producto, name="eliminar_producto"),
    path("indicadores/", views.indicadores, name="indicadores"),
]