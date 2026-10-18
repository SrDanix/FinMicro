"""Vistas de proyección de ingresos y evaluación de viabilidad de negocio."""
import json

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from finances.models import Categoria, Movimiento
from finances.views import MESES_ABREV
from .forms import EvaluadorViabilidadForm
from .services import evaluar_viabilidad, proyectar_ingresos


def _etiqueta_mes(fecha):
    return f"{MESES_ABREV[fecha.month - 1]} {fecha.year}"


def _historial_ingresos_mensuales(usuario, meses=6):
    """Últimos `meses` totales de ingresos, en orden cronológico ascendente.

    Se recorre mes a mes (en vez de agrupar con TruncMonth) para poder
    incluir explícitamente los meses sin ningún ingreso registrado como
    $0 — la regresión lineal necesita una serie continua, no solo los
    meses que tuvieron movimientos.
    """
    hoy = timezone.localdate().replace(day=1)
    etiquetas, valores = [], []
    for i in range(meses - 1, -1, -1):
        mes_ref = hoy - relativedelta(months=i)
        total = Movimiento.objects.filter(
            usuario=usuario,
            tipo=Categoria.Tipo.INGRESO,
            fecha__year=mes_ref.year,
            fecha__month=mes_ref.month,
        ).aggregate(t=Sum("monto"))["t"] or 0
        etiquetas.append(_etiqueta_mes(mes_ref))
        valores.append(total)
    return etiquetas, valores


@login_required
def proyeccion_ingresos(request):
    etiquetas, historial = _historial_ingresos_mensuales(request.user, meses=6)
    meses_con_datos = sum(1 for v in historial if v > 0)

    proyeccion = None
    etiquetas_proyeccion = []
    if meses_con_datos >= 2:
        proyeccion = proyectar_ingresos(historial, meses_futuros=3)
        ultimo_mes = timezone.localdate().replace(day=1)
        etiquetas_proyeccion = [
            _etiqueta_mes(ultimo_mes + relativedelta(months=i + 1))
            for i in range(3)
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
    plan = request.user.suscripcion_activa.plan if request.user.suscripcion_activa else None
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