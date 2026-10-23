"""Formularios de cuenta: registro, perfil, configuración y colaboradores."""
from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import Colaboracion, Usuario, normalizar_rut


def _estilizar(form):
    for campo in form.fields.values():
        if isinstance(campo.widget, forms.CheckboxInput):
            continue
        campo.widget.attrs.setdefault("class", "campo-input")


class RegistroForm(UserCreationForm):
    """Alta de un nuevo microempresario.

    Extiende UserCreationForm (en vez de un ModelForm común) para heredar
    la validación de contraseña de Django: reglas de largo mínimo,
    similitud con otros datos del usuario y contraseñas comunes
    (AUTH_PASSWORD_VALIDATORS en settings.py), sin reescribirlas a mano.
    """

    email = forms.EmailField(required=True, label="Correo electrónico")
    # 12 caracteres para aceptar "12.345.678-5"; se guarda normalizado (10).
    rut = forms.CharField(label="RUT", max_length=12, help_text="Con o sin puntos, con guion.")

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)
        self.fields["rut"].widget.attrs["placeholder"] = "12345678-9"

    def clean_rut(self):
        # Acepta "12.345.678-k" y lo guarda como "12345678-K".
        return normalizar_rut(self.cleaned_data["rut"])

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return email


class PerfilForm(UserChangeForm):
    """Edición de datos del negocio ya registrado. No expone la contraseña."""

    password = None  # oculta el campo de hash que trae UserChangeForm por defecto

    class Meta:
        model = Usuario
        fields = ("nombre_negocio", "tipo_negocio", "email", "telefono", "comuna")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)


class ConfiguracionForm(forms.ModelForm):
    """Configuración tributaria y metas del negocio (RF-05)."""

    class Meta:
        model = Usuario
        fields = ("regimen_tributario", "afecto_iva", "emite_boletas_honorarios", "meta_ventas_mensual")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilizar(self)

    def clean(self):
        datos = super().clean()
        # RN-04: sin inicio de actividades no se emiten documentos afectos.
        if (
            datos.get("regimen_tributario") == Usuario.RegimenTributario.SIN_INICIO
            and datos.get("afecto_iva")
        ):
            self.add_error(
                "afecto_iva",
                "Sin inicio de actividades no puedes emitir documentos afectos a IVA. "
                "Cambia tu régimen o desmarca esta opción.",
            )
        return datos


class InvitacionForm(forms.ModelForm):
    class Meta:
        model = Colaboracion
        fields = ("email", "rol")

    def __init__(self, *args, propietario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.propietario = propietario
        _estilizar(self)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if self.propietario and email == (self.propietario.email or "").lower():
            raise forms.ValidationError("No puedes invitarte a ti mismo.")
        if Colaboracion.objects.filter(propietario=self.propietario, email__iexact=email).exists():
            raise forms.ValidationError("Ya invitaste a este correo.")
        return email


class EliminarCuentaForm(forms.Form):
    password = forms.CharField(label="Confirma tu contraseña", widget=forms.PasswordInput)

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        _estilizar(self)

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.usuario.check_password(password):
            raise forms.ValidationError("La contraseña no es correcta.")
        return password
