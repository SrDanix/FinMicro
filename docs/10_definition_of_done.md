# Definition of Done

**Actividad 5.1** · Responsable (custodio): Danilo · Aprueba: Carlos · Semana 8

Una historia de usuario está **terminada** solo si cumple **todos** los puntos. Si falta
uno, no cuenta para la velocidad del sprint y vuelve a la pila.

## Código

1. Cumple todos los criterios de aceptación de la historia ([04_pila_de_producto.md](04_pila_de_producto.md)).
2. Todas las consultas a datos de negocio filtran por `request.negocio` (RNF-03).
3. Las vistas que modifican datos exigen sesión y, si corresponde, `@requiere_edicion`.
4. Sin migraciones pendientes: `python manage.py makemigrations --check` no detecta cambios.
5. Sin secretos en el código ni en el historial (claves solo en `.env`).

## Pruebas

6. Hay pruebas automatizadas del caso feliz y de al menos un caso de error.
7. Los cálculos (`services.py`) tienen pruebas unitarias con valores verificados a mano o con ejemplos oficiales.
8. `python manage.py test` pasa completo en local.
9. La CI de GitHub Actions está en verde (pruebas, `check --deploy`, construcción de la imagen Docker).

## Revisión

10. El pull request fue revisado y aprobado por un integrante **distinto del autor** (actividad 4.7; ver [CONTRIBUTING.md](../CONTRIBUTING.md)).
11. Se probó en el navegador, en escritorio y a 375 px de ancho (RNF-11).

## Documentación

12. Si cambia una regla, se actualiza [03_reglas_de_negocio.md](03_reglas_de_negocio.md).
13. Si se agrega un modelo o campo, se actualiza [09_modelo_de_datos.md](09_modelo_de_datos.md).
14. Se marca el estado del requerimiento en [01_requerimientos_funcionales.md](01_requerimientos_funcionales.md) y la prueba en la [matriz de trazabilidad](05_matriz_trazabilidad.md).

## Para cerrar un sprint (además de lo anterior)

- Revisión del sprint con demostración al aprobador.
- Retrospectiva registrada en el documento del sprint.
- Desplegado en el ambiente de pruebas (a partir del Sprint 2, cuando exista la instancia EC2).
