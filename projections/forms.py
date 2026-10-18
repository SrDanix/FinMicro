
from decimal import Decimal, InvalidOperation

from django import forms


class EvaluadorViabilidadForm(forms.Form):
    inversion_inicial = forms.DecimalField(
        label="Inversión inicial (CLP)", min_value=1, decimal_places=2, max_digits=14
    )
    tasa_descuento_pct = forms.DecimalField(
        label="Tasa de descuento anual (%)",
        min_value=Decimal("0.1"),
        max_value=100,
        decimal_places=2,
        max_digits=5,
        initial=Decimal("12"),
        help_text="Sección VII del informe: 12% fue la tasa base calculada para FinMicro con CAPM adaptado. "
        "Ajusta este valor según el riesgo propio de tu negocio.",
    )
    flujos_texto = forms.CharField(
        label="Flujo neto esperado por período (uno por línea)",
        widget=forms.Textarea(attrs={"rows": 6, "placeholder": "1200000\n1500000\n1800000"}),
        help_text="Un monto por línea, en el orden en que ocurrirán (período 1, período 2, ...).",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            if nombre != "flujos_texto":
                campo.widget.attrs.setdefault("class", "campo-input")
            else:
                campo.widget.attrs.setdefault("class", "campo-input campo-textarea")

    def clean_flujos_texto(self):
        bruto = self.cleaned_data["flujos_texto"]
        flujos = []
        for numero_linea, linea in enumerate(bruto.splitlines(), start=1):
            linea = linea.strip().replace(".", "").replace(",", ".")
            if not linea:
                continue
            try:
                flujos.append(Decimal(linea))
            except InvalidOperation:
                raise forms.ValidationError(f"La línea {numero_linea} ('{linea}') no es un monto válido.")
        if len(flujos) < 1:
            raise forms.ValidationError("Ingresa al menos un período de flujo esperado.")
        return flujos

    def clean_tasa_descuento_pct(self):
        return self.cleaned_data["tasa_descuento_pct"] / Decimal("100")