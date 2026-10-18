"""Crea los planes Básico y Premium al migrar (mismos valores que services.py)."""
from django.db import migrations

PLANES = [
    {
        "codigo": "basico",
        "nombre": "Plan Básico",
        "precio_mensual_clp": 0,
        "con_publicidad": True,
        "limite_movimientos_mensuales": 60,
        "incluye_proyecciones": True,
        "incluye_evaluador_viabilidad": False,
        "descripcion": "Gratis, financiado con publicidad. Gestión financiera e "
        "impuestos incluidos, con tope de 60 movimientos al mes.",
    },
    {
        "codigo": "premium",
        "nombre": "Plan Premium",
        "precio_mensual_clp": 9990,
        "con_publicidad": False,
        "limite_movimientos_mensuales": None,
        "incluye_proyecciones": True,
        "incluye_evaluador_viabilidad": True,
        "descripcion": "Sin publicidad, movimientos ilimitados y evaluador de "
        "viabilidad (VAN/TIR/Payback) para tu propio negocio.",
    },
]


def crear_planes(apps, schema_editor):
    Plan = apps.get_model("subscriptions", "Plan")
    for datos in PLANES:
        datos = dict(datos)
        codigo = datos.pop("codigo")
        Plan.objects.get_or_create(codigo=codigo, defaults=datos)


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(crear_planes, migrations.RunPython.noop),
    ]
