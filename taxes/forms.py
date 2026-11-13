from django import forms
from django.db import models

from django.utils import timezone

from .services import TABLA_RETENCION_HONORARIOS


class IVAForm(forms.Form):
    ventas_netas = forms.DecimalField(
        label="Ventas netas del período (CLP)", min_value=0, decimal_places=2, max_digits=12
    )
    compras_netas = forms.DecimalField(
        label="Compras / insumos netos del período (CLP)",
        min_value=0,
        decimal_places=2,
        max_digits=12,
        required=False,
        initial=0,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "campo-input")


class HonorariosForm(forms.Form):
    class Modo(models.TextChoices):
        DESDE_BRUTO = "bruto", "Sé el monto bruto de la boleta"
        DESDE_LIQUIDO = "liquido", "Sé cuánto quiero recibir líquido"

    modo = forms.ChoiceField(choices=Modo.choices, widget=forms.RadioSelect, initial=Modo.DESDE_BRUTO)
    monto = forms.DecimalField(label="Monto (CLP)", min_value=1, decimal_places=2, max_digits=12)
    anio = forms.ChoiceField(label="Año tributario")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # RF-25: los años salen de la tabla de tasas (y llegan al menos al año siguiente).
        from .models import TasaTributaria

        anios = set(
            TasaTributaria.objects.filter(codigo=TasaTributaria.Codigo.RETENCION_HONORARIOS)
            .values_list("vigente_desde__year", flat=True)
        ) or set(TABLA_RETENCION_HONORARIOS)
        anio_actual = timezone.localdate().year
        anios = range(min(anios), max(max(anios), anio_actual + 1) + 1)
        self.fields["anio"].choices = [(a, a) for a in anios]
        self.fields["anio"].initial = anio_actual
        for nombre, campo in self.fields.items():
            if nombre != "modo":
                campo.widget.attrs.setdefault("class", "campo-input")