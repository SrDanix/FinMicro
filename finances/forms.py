from django import forms
from django.db.models import Q

from .models import Categoria, Movimiento, Producto


class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = ["tipo", "categoria", "producto", "cantidad", "monto", "fecha", "descripcion"]
        labels = {"producto": "Producto o servicio (opcional)", "cantidad": "Cantidad"}
        help_texts = {
            "producto": "Si eliges un producto de tu catálogo, el monto se calcula con su precio.",
        }
        widgets = {
            # <input type="date"> solo acepta AAAA-MM-DD, no el formato local.
            "fecha": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "descripcion": forms.TextInput(attrs={"placeholder": "Opcional"}),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "campo-input")

        if usuario is not None:
            # Categorías del sistema (usuario=None) + las propias del usuario.
            self.fields["categoria"].queryset = Categoria.objects.filter(
                Q(usuario__isnull=True) | Q(usuario=usuario)
            ).order_by("tipo", "nombre")
            # data-tipo permite al pequeño script del template filtrar las
            # opciones visibles según el tipo (ingreso/gasto) elegido.
            self.fields["categoria"].widget.attrs["data-filtrable"] = "true"
            # RF-11: productos activos del negocio (y el ya elegido, aunque esté inactivo).
            productos = Producto.objects.filter(usuario=usuario, activo=True)
            if self.instance.producto_id:
                productos = productos | Producto.objects.filter(pk=self.instance.producto_id)
            self.fields["producto"].queryset = productos.order_by("nombre")
        else:
            self.fields["producto"].queryset = Producto.objects.none()
        self.fields["producto"].label_from_instance = lambda p: f"{p.nombre} (${p.precio:,.0f})".replace(",", ".")
        self.fields["monto"].required = False
        self.fields["monto"].help_text = "Con producto puedes dejarlo vacío: se calcula como precio × cantidad."
        self.fields["cantidad"].widget.attrs.setdefault("min", "1")

    def clean(self):
        datos = super().clean()
        categoria = datos.get("categoria")
        tipo = datos.get("tipo")
        if categoria and tipo and categoria.tipo != tipo:
            self.add_error("categoria", "Esta categoría no corresponde al tipo elegido.")

        producto = datos.get("producto")
        if producto:
            if tipo and tipo != Categoria.Tipo.INGRESO:
                self.add_error("producto", "Solo las ventas (ingresos) llevan producto.")
            cantidad = datos.get("cantidad") or 1
            datos["cantidad"] = cantidad
            if not datos.get("monto"):
                datos["monto"] = producto.precio * cantidad
            if not datos.get("descripcion"):
                datos["descripcion"] = f"{cantidad} × {producto.nombre}"
        else:
            datos["cantidad"] = None
        if not datos.get("monto") and "monto" not in self.errors:
            self.add_error("monto", "Ingresa el monto o elige un producto.")
        return datos


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "precio", "afecto_iva", "activo"]

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        for campo in self.fields.values():
            if not isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs.setdefault("class", "campo-input")

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        repetido = Producto.objects.filter(usuario=self.usuario, nombre__iexact=nombre)
        if self.instance.pk:
            repetido = repetido.exclude(pk=self.instance.pk)
        if repetido.exists():
            raise forms.ValidationError("Ya tienes un producto con ese nombre.")
        return nombre


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "tipo", "naturaleza", "es_gravable_iva"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "campo-input")
        self.fields["naturaleza"].help_text += " Solo para gastos."

    def clean(self):
        datos = super().clean()
        if datos.get("tipo") == Categoria.Tipo.INGRESO:
            datos["naturaleza"] = ""
        return datos


class FiltroMovimientosForm(forms.Form):
    """Filtro de la lista de movimientos: mes, año, tipo y texto (RF-10)."""

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
    q = forms.CharField(
        required=False,
        max_length=100,
        label="Buscar",
        widget=forms.TextInput(attrs={"placeholder": "Descripción o categoría", "type": "search"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "campo-input")

class ImportarMovimientosForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo Excel (.xlsx) o CSV",
        help_text="Columnas: fecha, tipo (ingreso o gasto), monto, categoria y descripcion (opcional). Máximo 1.000 filas.",
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx,.csv", "class": "campo-input"}),
    )
