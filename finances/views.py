"""
Vistas de gestión financiera: dashboard y CRUD de movimientos.

Objetivo específico 1 del informe: "Identificar y proyectar las fuentes
de ingresos y los costos fijos y variables del proyecto" — aplicado aquí
al negocio del propio usuario.
"""
import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.negocio import requiere_edicion
from core.alertas import revisar_movimiento, revisar_vencimientos
from core.models import Alerta
from .forms import CategoriaForm, FiltroMovimientosForm, MovimientoForm, ProductoForm
from .models import Categoria, Movimiento, Producto
from .services import buscar_por_texto, flujo_de_caja_ultimos_meses, indicadores_del_mes

# calendar.month_abbr depende del locale del sistema (en Windows suele
# quedar en inglés); se fijan las abreviaturas en español.
MESES_ABREV = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def _resumen_mes(usuario, anio, mes):
    qs = Movimiento.objects.filter(usuario=usuario, fecha__year=anio, fecha__month=mes)
    ingresos = qs.filter(tipo=Categoria.Tipo.INGRESO).aggregate(t=Sum("monto"))["t"] or 0
    gastos = qs.filter(tipo=Categoria.Tipo.GASTO).aggregate(t=Sum("monto"))["t"] or 0
    return {"ingresos": ingresos, "gastos": gastos, "balance": ingresos - gastos}


@login_required
def dashboard(request):
    hoy = timezone.localdate()
    resumen_actual = _resumen_mes(request.negocio, hoy.year, hoy.month)

    # Serie de los últimos 6 meses para el gráfico (Chart.js, ver
    # dashboard.html). Se arma con TruncMonth + Sum en una sola consulta
    # por tipo, en vez de 6 consultas sueltas por mes.
    hace_6_meses = (hoy.replace(day=1) - timedelta(days=150)).replace(day=1)
    serie = (
        Movimiento.objects.filter(usuario=request.negocio, fecha__gte=hace_6_meses)
        .annotate(mes=TruncMonth("fecha"))
        .values("mes", "tipo")
        .annotate(total=Sum("monto"))
        .order_by("mes")
    )
    serie = list(serie)
    meses_ordenados = sorted({row["mes"] for row in serie})
    etiquetas = [MESES_ABREV[m.month - 1] for m in meses_ordenados]
    ingresos_serie = []
    gastos_serie = []
    for mes in meses_ordenados:
        ingresos_serie.append(
            float(next((r["total"] for r in serie if r["mes"] == mes and r["tipo"] == "ingreso"), 0))
        )
        gastos_serie.append(
            float(next((r["total"] for r in serie if r["mes"] == mes and r["tipo"] == "gasto"), 0))
        )

    ultimos_movimientos = Movimiento.objects.filter(usuario=request.negocio).select_related(
        "categoria"
    )[:8]

    plan = request.negocio.suscripcion_activa.plan if request.negocio.suscripcion_activa else None
    movimientos_del_mes = Movimiento.objects.filter(
        usuario=request.negocio, fecha__year=hoy.year, fecha__month=hoy.month
    ).count()

    revisar_vencimientos(request.negocio, hoy)
    meta = request.negocio.meta_ventas_mensual
    contexto = {
        "alertas": Alerta.objects.filter(negocio=request.negocio, leida=False)[:5],
        "meta_ventas": meta,
        "avance_meta": min(100, round(resumen_actual["ingresos"] * 100 / meta)) if meta else None,
        "resumen": resumen_actual,
        "ultimos_movimientos": ultimos_movimientos,
        "grafico_datos": json.dumps(
            {"etiquetas": etiquetas, "ingresos": ingresos_serie, "gastos": gastos_serie}
        ),
        "plan": plan,
        "movimientos_del_mes": movimientos_del_mes,
        "cerca_del_limite": bool(
            plan and plan.limite_movimientos_mensuales
            and movimientos_del_mes >= plan.limite_movimientos_mensuales * 0.8
        ),
    }
    return render(request, "finances/dashboard.html", contexto)


@login_required
def listar_movimientos(request):
    form = FiltroMovimientosForm(request.GET or None)
    movimientos = Movimiento.objects.filter(usuario=request.negocio).select_related("categoria")

    if form.is_valid():
        if form.cleaned_data.get("mes"):
            movimientos = movimientos.filter(fecha__month=form.cleaned_data["mes"])
        if form.cleaned_data.get("anio"):
            movimientos = movimientos.filter(fecha__year=form.cleaned_data["anio"])
        if form.cleaned_data.get("tipo"):
            movimientos = movimientos.filter(tipo=form.cleaned_data["tipo"])
        if form.cleaned_data.get("q"):
            movimientos = buscar_por_texto(movimientos, form.cleaned_data["q"])

    return render(
        request,
        "finances/movimiento_list.html",
        {"movimientos": movimientos, "form": form, "filtros": request.GET.urlencode()},
    )


def _contexto_formulario(form, modo):
    precios = {str(p.pk): int(p.precio) for p in form.fields["producto"].queryset}
    return {"form": form, "modo": modo, "precios_productos": json.dumps(precios)}


def _limite_alcanzado(usuario) -> bool:
    plan = usuario.suscripcion_activa.plan if usuario.suscripcion_activa else None
    if not plan or not plan.limite_movimientos_mensuales:
        return False
    hoy = timezone.localdate()
    total_mes = Movimiento.objects.filter(
        usuario=usuario, fecha__year=hoy.year, fecha__month=hoy.month
    ).count()
    return total_mes >= plan.limite_movimientos_mensuales


@login_required
@requiere_edicion
def crear_movimiento(request):
    if _limite_alcanzado(request.negocio):
        messages.warning(
            request,
            "Alcanzaste el límite de movimientos del Plan Básico este mes. "
            "Sube a Premium para registrar movimientos ilimitados.",
        )
        return redirect("subscriptions:planes")

    if request.method == "POST":
        form = MovimientoForm(request.POST, usuario=request.negocio)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.usuario = request.negocio
            movimiento.save()
            revisar_movimiento(movimiento, timezone.localdate())
            messages.success(request, "Movimiento registrado.")
            return redirect("finances:dashboard")
    else:
        form = MovimientoForm(usuario=request.negocio, initial={"fecha": timezone.localdate()})

    return render(request, "finances/movimiento_form.html", _contexto_formulario(form, "crear"))


@login_required
@requiere_edicion
def editar_movimiento(request, pk):
    movimiento = get_object_or_404(Movimiento, pk=pk, usuario=request.negocio)
    if request.method == "POST":
        form = MovimientoForm(request.POST, instance=movimiento, usuario=request.negocio)
        if form.is_valid():
            form.save()
            messages.success(request, "Movimiento actualizado.")
            return redirect("finances:listar_movimientos")
    else:
        form = MovimientoForm(instance=movimiento, usuario=request.negocio)

    return render(request, "finances/movimiento_form.html", _contexto_formulario(form, "editar"))


@login_required
@requiere_edicion
def eliminar_movimiento(request, pk):
    movimiento = get_object_or_404(Movimiento, pk=pk, usuario=request.negocio)
    if request.method == "POST":
        movimiento.delete()
        messages.success(request, "Movimiento eliminado.")
        return redirect("finances:listar_movimientos")
    return render(request, "finances/movimiento_confirmar_eliminar.html", {"movimiento": movimiento})


@login_required
@requiere_edicion
def crear_categoria(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.usuario = request.negocio
            categoria.save()
            messages.success(request, f'Categoría "{categoria.nombre}" creada.')
            return redirect("finances:crear_movimiento")
    else:
        form = CategoriaForm()
    return render(request, "finances/categoria_form.html", {"form": form})

# ---------- RF-11: catálogo de productos y servicios ----------

@login_required
def listar_productos(request):
    productos = Producto.objects.filter(usuario=request.negocio)
    return render(request, "finances/producto_list.html", {"productos": productos})


@login_required
@requiere_edicion
def crear_producto(request):
    form = ProductoForm(request.POST or None, usuario=request.negocio)
    if request.method == "POST" and form.is_valid():
        producto = form.save(commit=False)
        producto.usuario = request.negocio
        producto.save()
        messages.success(request, f'Producto "{producto.nombre}" agregado al catálogo.')
        return redirect("finances:listar_productos")
    return render(request, "finances/producto_form.html", {"form": form, "modo": "crear"})


@login_required
@requiere_edicion
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk, usuario=request.negocio)
    form = ProductoForm(request.POST or None, instance=producto, usuario=request.negocio)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Producto actualizado.")
        return redirect("finances:listar_productos")
    return render(request, "finances/producto_form.html", {"form": form, "modo": "editar"})


@login_required
@requiere_edicion
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk, usuario=request.negocio)
    if request.method == "POST":
        # Las ventas ya registradas conservan su monto; solo pierden el vínculo.
        producto.delete()
        messages.success(request, "Producto eliminado del catálogo.")
        return redirect("finances:listar_productos")
    return render(
        request,
        "finances/producto_confirmar_eliminar.html",
        {"producto": producto, "ventas": producto.movimientos.count()},
    )


# ---------- RF-16, RF-17, RF-19: indicadores y flujo de caja ----------

def _mes_elegido(request):
    """Mes pedido en ?mes=AAAA-MM; por defecto, el mes en curso."""
    hoy = timezone.localdate().replace(day=1)
    try:
        anio, mes = (int(x) for x in request.GET.get("mes", "").split("-"))
        elegido = hoy.replace(year=anio, month=mes)
    except (ValueError, TypeError):
        return hoy
    return min(elegido, hoy)


@login_required
def indicadores(request):
    mes = _mes_elegido(request)
    flujos = flujo_de_caja_ultimos_meses(request.negocio, mes, meses=6)
    contexto = {
        "mes": mes,
        "mes_valor": mes.strftime("%Y-%m"),
        "indicadores": indicadores_del_mes(request.negocio, mes),
        "flujo": flujos[-1],
        "flujos": flujos,
        "grafico_flujo": json.dumps(
            {
                "etiquetas": [f"{MESES_ABREV[f.mes.month - 1]} {f.mes.year}" for f in flujos],
                "saldo_final": [float(f.saldo_final) for f in flujos],
                "entradas": [float(f.entradas) for f in flujos],
                "proyectado": [float(f.proyectado) if f.proyectado is not None else None for f in flujos],
            }
        ),
    }
    return render(request, "finances/indicadores.html", contexto)
