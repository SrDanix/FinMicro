"""Enrutador principal: delega en el urls.py de cada app."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("cuenta/", include("accounts.urls")),
    path("suscripcion/", include("subscriptions.urls")),
    path("finanzas/", include("finances.urls")),
    path("impuestos/", include("taxes.urls")),
    path("proyecciones/", include("projections.urls")),
]
# En DEBUG, django.contrib.staticfiles ya sirve /static/ desde STATICFILES_DIRS.