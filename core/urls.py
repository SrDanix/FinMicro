
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("alertas/", views.alertas, name="alertas"),
    path("asistente/", views.asistente_financiero, name="asistente"),
    path("alertas/<int:pk>/leida/", views.marcar_alerta_leida, name="marcar_alerta_leida"),
]