from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.
"""Vistas de la calculadora de impuestos (IVA + boletas de honorarios)."""


from .forms import HonorariosForm, IVAForm
from .services import (
    calcular_honorarios_desde_bruto,
    calcular_honorarios_desde_liquido,
    calcular_iva,
)


@login_required
def calculadora(request):
    iva_form = IVAForm(prefix="iva")
    honorarios_form = HonorariosForm(prefix="hon")
    resultado_iva = None
    resultado_honorarios = None
    pestana_activa = "iva"

    if request.method == "POST" and request.POST.get("formulario") == "iva":
        iva_form = IVAForm(request.POST, prefix="iva")
        if iva_form.is_valid():
            resultado_iva = calcular_iva(
                iva_form.cleaned_data["ventas_netas"],
                iva_form.cleaned_data["compras_netas"] or 0,
            )

    elif request.method == "POST" and request.POST.get("formulario") == "honorarios":
        pestana_activa = "honorarios"
        honorarios_form = HonorariosForm(request.POST, prefix="hon")
        if honorarios_form.is_valid():
            datos = honorarios_form.cleaned_data
            anio = int(datos["anio"])
            if datos["modo"] == HonorariosForm.Modo.DESDE_BRUTO:
                resultado_honorarios = calcular_honorarios_desde_bruto(datos["monto"], anio)
            else:
                resultado_honorarios = calcular_honorarios_desde_liquido(datos["monto"], anio)

    return render(
        request,
        "taxes/calculadora.html",
        {
            "iva_form": iva_form,
            "honorarios_form": honorarios_form,
            "resultado_iva": resultado_iva,
            "resultado_honorarios": resultado_honorarios,
            "pestana_activa": pestana_activa,
            "mostrar_honorarios": request.user.emite_boletas_honorarios,
        },
    )