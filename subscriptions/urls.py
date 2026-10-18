from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    path("planes/", views.planes, name="planes"),
    path("planes/<str:codigo_plan>/suscribirse/", views.suscribirse, name="suscribirse"),
    path("pago-simulado/<int:suscripcion_id>/", views.pago_simulado, name="pago_simulado"),
    path("webhook/khipu/", views.webhook_khipu, name="webhook_khipu"),
    path("webhook/flow/", views.webhook_flow, name="webhook_flow"),
    path("mi-suscripcion/", views.mi_suscripcion, name="mi_suscripcion"),
]