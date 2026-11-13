from django.core.management.base import BaseCommand



from finances.models import Categoria



CATEGORIAS_SISTEMA = [

    ("Ventas", Categoria.Tipo.INGRESO, True),

    ("Servicios prestados", Categoria.Tipo.INGRESO, True),

    ("Otros ingresos", Categoria.Tipo.INGRESO, False),

    ("Mercadería / insumos", Categoria.Tipo.GASTO, True),

    ("Arriendo", Categoria.Tipo.GASTO, False),

    ("Transporte", Categoria.Tipo.GASTO, True),

    ("Servicios básicos", Categoria.Tipo.GASTO, True),

    ("Marketing", Categoria.Tipo.GASTO, True),

    ("Impuestos y comisiones", Categoria.Tipo.GASTO, False),

    ("Otros gastos", Categoria.Tipo.GASTO, False),

]





# RF-19 (ver migración 0004): lo que no aparece aquí queda sin clasificar.
NATURALEZA_SISTEMA = {
    "Mercadería / insumos": Categoria.Naturaleza.VARIABLE,
    "Transporte": Categoria.Naturaleza.VARIABLE,
    "Impuestos y comisiones": Categoria.Naturaleza.VARIABLE,
    "Arriendo": Categoria.Naturaleza.FIJO,
    "Servicios básicos": Categoria.Naturaleza.FIJO,
    "Marketing": Categoria.Naturaleza.FIJO,
}


class Command(BaseCommand):

    help = "Crea las categorías de ingreso/gasto por defecto (visibles para todos los usuarios)."



    def handle(self, *args, **options):

        creadas = 0

        for nombre, tipo, gravable in CATEGORIAS_SISTEMA:

            _, creada = Categoria.objects.get_or_create(

                nombre=nombre,
                tipo=tipo,
                usuario=None,
                defaults={
                    "es_gravable_iva": gravable,
                    "naturaleza": NATURALEZA_SISTEMA.get(nombre, ""),
                },

            )

            creadas += int(creada)

        self.stdout.write(self.style.SUCCESS(f"Categorías del sistema listas ({creadas} nuevas)."))
