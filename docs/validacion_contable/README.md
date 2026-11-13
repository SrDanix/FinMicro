# Validación contable (actividad X-12)

`FinMicro_Casos_validacion_contable.xlsx` reúne 30 casos de IVA automático, honorarios, calendario
tributario, tasas e indicadores con el resultado que entrega hoy la aplicación. La asesoría contable
completa las columnas amarillas (resultado esperado, conformidad y observaciones).

Para regenerarla después de corregir un cálculo:

```bash
python manage.py generar_casos_validacion docs/validacion_contable/FinMicro_Casos_validacion_contable.xlsx
```

Por cada caso no conforme: corregir el cálculo, agregar una prueba en `taxes/tests.py` o
`finances/tests.py` con el valor del contador y volver a generar la planilla. La conformidad firmada
es la evidencia de RNF-17 y de la actividad X-12.
