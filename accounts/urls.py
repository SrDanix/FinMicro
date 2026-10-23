from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = "accounts"

urlpatterns = [
    path("registro/", views.registro, name="registro"),
    path("perfil/", views.perfil, name="perfil"),
    path("configuracion/", views.configuracion, name="configuracion"),
    path("colaboradores/", views.colaboradores, name="colaboradores"),
    path("colaboradores/<int:pk>/revocar/", views.revocar_colaborador, name="revocar_colaborador"),
    path("colaboradores/<int:pk>/abandonar/", views.abandonar_negocio, name="abandonar_negocio"),
    path("invitacion/<uuid:token>/", views.aceptar_invitacion, name="aceptar_invitacion"),
    path("negocio/cambiar/", views.cambiar_negocio, name="cambiar_negocio"),
    path("mis-datos/exportar/", views.exportar_datos, name="exportar_datos"),
    path("eliminar/", views.eliminar_cuenta, name="eliminar_cuenta"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "clave/cambiar/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            success_url=reverse_lazy("accounts:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "clave/cambiada/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html"
        ),
        name="password_change_done",
    ),
    # --- Recuperación de contraseña por correo (RF-03) ---
    path(
        "clave/recuperar/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.txt",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url=reverse_lazy("accounts:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "clave/recuperar/enviado/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "clave/recuperar/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "clave/recuperar/listo/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
