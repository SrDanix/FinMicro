"""Formularios de registro y edición de perfil para microempresarios."""
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import Usuario


class RegistroForm(UserCreationForm):
    """Alta de un nuevo microempresario.

    Extiende UserCreationForm (en vez de un ModelForm común) para heredar
    la validación de contraseña de Django: reglas de largo mínimo,
    similitud con otros datos del usuario y contraseñas comunes
    (AUTH_PASSWORD_VALIDATORS en settings.py), sin reescribirlas a mano.
    """

    email = forms.EmailField(required=True, label="Correo electrónico")

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = (
            "username",
            "email",
            "rut",
            "nombre_negocio",
            "tipo_negocio",
            "telefono",
            "comuna",
            "emite_boletas_honorarios",
        )
        widgets = {
            "tipo_negocio": forms.Select(attrs={"class": "campo-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            campo.widget.attrs.setdefault("class", "campo-input")
        self.fields["rut"].widget.attrs["placeholder"] = "12345678-9"


class PerfilForm(UserChangeForm):
    """Edición de datos del negocio ya registrado. No expone la contraseña."""

    password = None  # oculta el campo de hash que trae UserChangeForm por defecto

    class Meta:
        model = Usuario
        fields = (
            "nombre_negocio",
            "tipo_negocio",
            "email",
            "telefono",
            "comuna",
            "emite_boletas_honorarios",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            campo.widget.attrs.setdefault("class", "campo-input")