
# Create your views here.
"""Vistas de autenticación y perfil del microempresario."""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from subscriptions.services import asegurar_plan_basico
from .forms import PerfilForm, RegistroForm


def registro(request):
    """Alta de un nuevo microempresario.

    Al registrarse, se le asigna automáticamente el Plan Básico (gratuito)
    definido en la Sección 5.1 del informe, para que el usuario entre
    directamente al dashboard sin pasos intermedios obligatorios.
    """
    if request.user.is_authenticated:
        return redirect("finances:dashboard")

    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            asegurar_plan_basico(usuario)
            login(request, usuario)
            messages.success(
                request,
                f"¡Bienvenido a FinMicro, {usuario.nombre_negocio}! Tu cuenta quedó activa en el Plan Básico.",
            )
            return redirect("finances:dashboard")
    else:
        form = RegistroForm()

    return render(request, "accounts/registro.html", {"form": form})


@login_required
def perfil(request):
    if request.method == "POST":
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Tus datos se actualizaron correctamente.")
            return redirect("accounts:perfil")
    else:
        form = PerfilForm(instance=request.user)

    return render(request, "accounts/perfil.html", {"form": form})