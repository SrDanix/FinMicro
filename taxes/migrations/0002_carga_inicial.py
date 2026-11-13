"""Carga inicial de tasas (RF-25) y feriados (RF-23).

Las tasas son las mismas que estaban fijas en taxes/services.py. Los
feriados son los legales de Chile 2026–2027 que pueden mover un
vencimiento; se mantienen en el administrador. VALIDAR con la asesoría
contable (actividad X-12) antes de producción.
"""
from datetime import date
from decimal import Decimal

from django.db import migrations

TASAS = [
    ("IVA", "0.19", date(2003, 10, 1), None, "DL 825, art. 14 (Ley 19.888)"),
    ("RET_HON", "0.145", date(2025, 1, 1), date(2025, 12, 31), "Ley 21.133"),
    ("RET_HON", "0.1525", date(2026, 1, 1), date(2026, 12, 31), "Ley 21.133"),
    ("RET_HON", "0.16", date(2027, 1, 1), date(2027, 12, 31), "Ley 21.133"),
    ("RET_HON", "0.17", date(2028, 1, 1), None, "Ley 21.133 (tasa final)"),
]

FERIADOS = [
    (date(2026, 1, 1), "Año Nuevo"),
    (date(2026, 4, 3), "Viernes Santo"),
    (date(2026, 4, 4), "Sábado Santo"),
    (date(2026, 5, 1), "Día del Trabajo"),
    (date(2026, 5, 21), "Día de las Glorias Navales"),
    (date(2026, 6, 21), "Día Nacional de los Pueblos Indígenas"),
    (date(2026, 6, 29), "San Pedro y San Pablo"),
    (date(2026, 7, 16), "Virgen del Carmen"),
    (date(2026, 8, 15), "Asunción de la Virgen"),
    (date(2026, 9, 18), "Independencia Nacional"),
    (date(2026, 9, 19), "Glorias del Ejército"),
    (date(2026, 10, 12), "Encuentro de Dos Mundos"),
    (date(2026, 10, 31), "Día de las Iglesias Evangélicas y Protestantes"),
    (date(2026, 11, 1), "Día de Todos los Santos"),
    (date(2026, 12, 8), "Inmaculada Concepción"),
    (date(2026, 12, 25), "Navidad"),
    (date(2027, 1, 1), "Año Nuevo"),
    (date(2027, 3, 26), "Viernes Santo"),
    (date(2027, 3, 27), "Sábado Santo"),
    (date(2027, 5, 1), "Día del Trabajo"),
    (date(2027, 5, 21), "Día de las Glorias Navales"),
    (date(2027, 6, 21), "Día Nacional de los Pueblos Indígenas"),
    (date(2027, 6, 28), "San Pedro y San Pablo"),
    (date(2027, 7, 16), "Virgen del Carmen"),
    (date(2027, 8, 15), "Asunción de la Virgen"),
    (date(2027, 9, 18), "Independencia Nacional"),
    (date(2027, 9, 19), "Glorias del Ejército"),
    (date(2027, 10, 11), "Encuentro de Dos Mundos"),
    (date(2027, 10, 31), "Día de las Iglesias Evangélicas y Protestantes"),
    (date(2027, 11, 1), "Día de Todos los Santos"),
    (date(2027, 12, 8), "Inmaculada Concepción"),
    (date(2027, 12, 25), "Navidad"),
]


def cargar(apps, schema_editor):
    Tasa = apps.get_model("taxes", "TasaTributaria")
    Feriado = apps.get_model("taxes", "Feriado")
    for codigo, valor, desde, hasta, fuente in TASAS:
        Tasa.objects.get_or_create(
            codigo=codigo, vigente_desde=desde,
            defaults={"valor": Decimal(valor), "vigente_hasta": hasta, "fuente": fuente},
        )
    for fecha, nombre in FERIADOS:
        Feriado.objects.get_or_create(fecha=fecha, defaults={"nombre": nombre})


class Migration(migrations.Migration):
    dependencies = [
        ("taxes", "0001_tasas_y_feriados"),
    ]

    operations = [
        migrations.RunPython(cargar, migrations.RunPython.noop),
    ]
