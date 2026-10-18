
from django.urls import path

from . import views

app_name = "projections"

urlpatterns = [
    path("ingresos/", views.proyeccion_ingresos, name="proyeccion_ingresos"),
    path("viabilidad/", views.evaluador_viabilidad, name="evaluador_viabilidad"),
]