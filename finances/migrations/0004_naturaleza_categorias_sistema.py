"""RF-19: clasifica las categorías de gasto del sistema en fijas o variables."""
from django.db import migrations

NATURALEZA_SISTEMA = {
    "Mercadería / insumos": "variable",
    "Transporte": "variable",
    "Impuestos y comisiones": "variable",
    "Arriendo": "fijo",
    "Servicios básicos": "fijo",
    "Marketing": "fijo",
}


def clasificar(apps, schema_editor):
    Categoria = apps.get_model("finances", "Categoria")
    for nombre, naturaleza in NATURALEZA_SISTEMA.items():
        Categoria.objects.filter(nombre=nombre, tipo="gasto", usuario=None).update(naturaleza=naturaleza)


class Migration(migrations.Migration):
    dependencies = [
        ("finances", "0003_producto_y_naturaleza"),
    ]

    operations = [
        migrations.RunPython(clasificar, migrations.RunPython.noop),
    ]
