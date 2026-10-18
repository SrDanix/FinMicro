from django import forms
from django.db.models import Q

from .models import Categoria, Movimiento


class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = ["tipo", "categoria", "monto", "fecha", "descripcion"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "descripcion": forms.TextInput(attrs={"placeholder": "Opcional"}),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        for nombre, campo in self.fields.items():
            campo.widget.attrs.setdefault("class", "campo-input")

        if usuario is not None:
            # Categorías del sistema (usuario=None) + las propias del usuario.
            self.fields["categoria"].queryset = Categoria.objects.filter(
                Q(usuario__isnull=True) | Q(usuario=usuario)
            ).order_by("tipo", "nombre")
            # data-tipo permite al pequeño script del template filtrar las
            # opciones visibles según el tipo (ingreso/gasto) elegido.
            self.fields["categoria"].widget.attrs["data-filtrable"] = "true"

    def clean(self):
        datos = super().clean()
        categoria = datos.get("categoria")
        tipo = datos.get("tipo")
        if categoria and tipo and categoria.tipo != tipo:
            self.add_error("categoria", "Esta categoría no corresponde al tipo elegido.")
        return datos


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "tipo", "es_gravable_iva"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            campo.widget.attrs.setdefault("class", "campo-input")


class FiltroMovimientosForm(forms.Form):
    """Filtro simple para la lista de movimientos (mes/año + tipo)."""

    MESES = [("", "Todos")] + [
        (i, nombre)
        for i, nombre in enumerate(
            ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
             "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
            start=1,
        )
    ]

    mes = forms.ChoiceField(choices=MESES, required=False, label="Mes")
    anio = forms.IntegerField(required=False, min_value=2020, max_value=2100, label="Año")
    tipo = forms.ChoiceField(
        choices=[("", "Todos")] + list(Categoria.Tipo.choices), required=False, label="Tipo"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "campo-input")