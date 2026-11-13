"""Vistas de impuestos: calculadora (RF-20, RF-21), IVA automático (RF-22) y calendario (RF-23)."""
from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from .calendario import obligaciones_del_negocio
from .forms import HonorariosForm, IVAForm
from .models import TasaTributaria
from .services import (
    calcular_honorarios_desde_bruto,
    calcular_honorarios_desde_liquido,
    calcular_iva,
    iva_del_mes,
    tasa_vigente,
)


def _mes_elegido(request):
    hoy = timezone.localdate().replace(day=1)
    try:
        anio, mes = (int(x) for x in request.GET.get("mes", "").split("-"))
        return min(date(anio, mes, 1), hoy)
    except (ValueError, TypeError):
        return hoy


@login_required
def calculadora(request):
    hoy = timezone.localdate()
    tasa_iva = tasa_vigente(TasaTributaria.Codigo.IVA, hoy)
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
                tasa=tasa_iva,
            )

    elif request.method == "POST" and request.POST.get("formulario") == "honorarios":
        pestana_activa = "honorarios"
        honorarios_form = HonorariosForm(request.POST, prefix="hon")
        if honorarios_form.is_valid():
            datos = honorarios_form.cleaned_data
            anio = int(datos["anio"])
            tasa = tasa_vigente(TasaTributaria.Codigo.RETENCION_HONORARIOS, date(anio, 1, 1))
            if datos["modo"] == HonorariosForm.Modo.DESDE_BRUTO:
                resultado_honorarios = calcular_honorarios_desde_bruto(datos["monto"], anio, tasa)
            else:
                resultado_honorarios = calcular_honorarios_desde_liquido(datos["monto"], anio, tasa)

    mes = _mes_elegido(request)
    return render(
        request,
        "taxes/calculadora.html",
        {
            "iva_form": iva_form,
            "honorarios_form": honorarios_form,
            "resultado_iva": resultado_iva,
            "resultado_honorarios": resultado_honorarios,
            "pestana_activa": pestana_activa,
            "mostrar_honorarios": request.negocio.emite_boletas_honorarios,
            "afecto_iva": request.negocio.afecto_iva,
            "tasa_iva_porcentaje": (tasa_iva * 100).normalize(),
            "iva_automatico": iva_del_mes(request.negocio, mes) if request.negocio.afecto_iva else None,
            "mes_valor": mes.strftime("%Y-%m"),
            "tasas": TasaTributaria.objects.all(),
        },
    )


@login_required
def calendario(request):
    hoy = timezone.localdate()
    obligaciones = obligaciones_del_negocio(request.negocio, hoy, hoy + relativedelta(months=12))
    return render(
        request,
        "taxes/calendario.html",
        {
            "obligaciones": [(o, o.dias_restantes(hoy)) for o in obligaciones],
            "sin_inicio": request.negocio.regimen_tributario == "SI",
        },
    )
