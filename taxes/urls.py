
from django.urls import path

from . import views

app_name = "taxes"

urlpatterns = [
    path("", views.calculadora, name="calculadora"),
]