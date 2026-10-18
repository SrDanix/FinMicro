"""Crea las categorías del sistema al migrar (mismas que `seed_categorias`)."""
from django.db import migrations

CATEGORIAS_SISTEMA = [
    ("Ventas", "ingreso", True),
    ("Servicios prestados", "ingreso", True),
    ("Otros ingresos", "ingreso", False),
    ("Mercadería / insumos", "gasto", True),
    ("Arriendo", "gasto", False),
    ("Transporte", "gasto", True),
    ("Servicios básicos", "gasto", True),
    ("Marketing", "gasto", True),
    ("Impuestos y comisiones", "gasto", False),
    ("Otros gastos", "gasto", False),
]


def crear_categorias(apps, schema_editor):
    Categoria = apps.get_model("finances", "Categoria")
    for nombre, tipo, gravable in CATEGORIAS_SISTEMA:
        Categoria.objects.get_or_create(
            nombre=nombre, tipo=tipo, usuario=None, defaults={"es_gravable_iva": gravable}
        )


class Migration(migrations.Migration):
    dependencies = [
        ("finances", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(crear_categorias, migrations.RunPython.noop),
    ]
