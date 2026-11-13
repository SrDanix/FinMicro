"""Vistas de proyección de ingresos y evaluación de viabilidad de negocio."""
import json

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from finances.views import MESES_ABREV
from .forms import EvaluadorViabilidadForm
from .historial import historial_ingresos_mensuales, recortar_inicio
from .services import evaluar_viabilidad, proyectar_ingresos


def _etiqueta_mes(fecha):
    return f"{MESES_ABREV[fecha.month - 1]} {fecha.year}"


@login_required
def proyeccion_ingresos(request):
    meses, historial = historial_ingresos_mensuales(request.negocio, meses=6)
    etiquetas = [_etiqueta_mes(m) for m in meses]
    serie = recortar_inicio(historial)
    meses_con_datos = sum(1 for v in historial if v > 0)

    proyeccion = None
    etiquetas_proyeccion = []
    if serie is not None:
        proyeccion = proyectar_ingresos(serie, meses_futuros=3)
        # La proyección empieza en el mes en curso (aún incompleto).
        mes_actual = timezone.localdate().replace(day=1)
        etiquetas_proyeccion = [
            _etiqueta_mes(mes_actual + relativedelta(months=i)) for i in range(3)
        ]

    grafico = {
        "etiquetas": etiquetas + etiquetas_proyeccion,
        "historial": [float(v) for v in historial] + [None] * len(etiquetas_proyeccion),
        "proyeccion": [None] * len(historial) + ([float(v) for v in proyeccion] if proyeccion else []),
    }

    return render(
        request,
        "projections/proyeccion.html",
        {
            "suficientes_datos": meses_con_datos >= 2,
            "proyeccion": proyeccion,
            "grafico_datos": json.dumps(grafico),
        },
    )


@login_required
def evaluador_viabilidad(request):
    plan = request.negocio.suscripcion_activa.plan if request.negocio.suscripcion_activa else None
    if not plan or not plan.incluye_evaluador_viabilidad:
        messages.info(
            request,
            "El evaluador de viabilidad (VAN, TIR, Payback) es una funcionalidad del Plan Premium.",
        )
        return redirect("subscriptions:planes")

    resultado = None
    if request.method == "POST":
        form = EvaluadorViabilidadForm(request.POST)
        if form.is_valid():
            resultado = evaluar_viabilidad(
                form.cleaned_data["inversion_inicial"],
                form.cleaned_data["flujos_texto"],
                form.cleaned_data["tasa_descuento_pct"],
            )
    else:
        form = EvaluadorViabilidadForm()

    return render(
        request, "projections/evaluador_viabilidad.html", {"form": form, "resultado": resultado}
    )