# Matriz de trazabilidad

**Actividad 2.10** · Responsable: Luciano · Aprueba: Carlos · Semana 5

Verifica que ningún requerimiento quede sin origen ni sin componente. Origen:
**INF** = informe del proyecto · **NOR** = marco normativo ([13_marco_normativo.md](13_marco_normativo.md)) ·
**ENT** = entrevistas y encuesta (actividad 2.5, pendiente de ejecución) · **EQ** = decisión del equipo.

Los requerimientos con origen ENT deben confirmarse cuando se apliquen las entrevistas;
si el trabajo de campo no los respalda, se repriorizan en la pila.

| RF | Origen | HU | Componente | Prueba automatizada | RN / RNF |
|---|---|---|---|---|---|
| RF-01 | INF §I, NOR (RUT) | HU-01 | `accounts` · `RegistroForm`, `validar_rut` | `accounts/tests.py` RutTests, RegistroTests | RN-01, RN-02, RN-03 |
| RF-02 | EQ | HU-02 | Django auth · `accounts/urls.py` | `core/tests.py` (sesión en todas las pruebas) | RNF-01 |
| RF-03 | EQ | HU-03 | Django auth · plantillas `password_reset_*` | `RecuperarClaveTests` | RNF-01 |
| RF-04 | EQ | HU-04 | `accounts.views.perfil` | `core/tests.py` páginas autenticadas | — |
| RF-05 | NOR (Ley 21.210), ENT | HU-05 | `accounts.views.configuracion`, panel | `ConfiguracionTests` | RN-04 |
| RF-06 | ENT (contador externo), EQ | HU-06 | `accounts.models.Colaboracion`, `accounts.negocio` | `ColaboradoresTests` (7 pruebas) | RN-06, RN-14, RN-15, RNF-03 |
| RF-07 | NOR (Ley 19.628 / 21.719) | HU-07 | `accounts.views.exportar_datos`, `eliminar_cuenta` | `DatosPersonalesTests` | RN-16, RNF-06 |
| RF-08 | INF obj. 1 | HU-08 | `finances` · `Movimiento`, vistas CRUD | `core/tests.py` test_crud_movimiento | RN-07, RN-08 |
| RF-09 | INF obj. 1 | HU-09 | `finances.Categoria`, `crear_categoria` | `core/tests.py` páginas | RN-09 |
| RF-10 | ENT | HU-10 | `FiltroMovimientosForm` | test_crud_movimiento (filtro) | — |
| RF-11 | ENT | HU-11 | `finances` (nuevo modelo Producto) | Pendiente | — |
| RF-12 | ENT | HU-12 | `finances` (importador) | Pendiente | RN-05 |
| RF-13 | INF §5.1 | HU-13 | `finances.views._limite_alcanzado` | Pendiente de prueba dedicada | RN-05 |
| RF-14 | INF obj. 1 | HU-14 | `finances.views.dashboard` | test_crud_movimiento | RNF-15 |
| RF-15 | INF obj. 1 | HU-15 | `dashboard.html` (Chart.js) | — (visual) | — |
| RF-16 | INF obj. 2 | HU-16 | `finances` / `projections` | Pendiente | — |
| RF-17 | INF obj. 1 | HU-17 | `finances` (servicio de indicadores) | Pendiente | — |
| RF-18 | INF §III (PESTEL tecnológico) | HU-18 | `core.services.BancoCentralService` | test_home_publica (caída de la API) | — |
| RF-19 | INF obj. 1 | HU-19 | `finances.Categoria` (atributo fijo/variable) | Pendiente | — |
| RF-20 | INF §III, NOR (DL 825) | HU-20 | `taxes.services.calcular_iva` | `taxes/tests.py` CalculadoraIVATests | RN-10, RNF-17 |
| RF-21 | INF §III, NOR (Ley 21.133) | HU-21 | `taxes.services.calcular_honorarios_*` | `CalculadoraHonorariosTests` | RN-11, RNF-17 |
| RF-22 | NOR (DL 825) | HU-22 | `taxes` + `finances` | Pendiente | RN-10 |
| RF-23 | NOR (F29, Operación Renta) | HU-23 | `taxes` (calendario) | Pendiente | — |
| RF-24 | ENT | HU-24 | `taxes` / `core` (alertas) | Pendiente | — |
| RF-25 | NOR | HU-25 | `taxes` (modelo de tasas) | Pendiente | RN-11 |
| RF-26 | INF §5.1 | HU-26 | `subscriptions` | test_flujo_premium_y_evaluador | RN-03, RN-17 |
| RF-27 | INF §III (Khipu, Flow) | HU-27 | `subscriptions.services` pasarelas | test_flujo_premium (simulado) | RN-18 |
| RF-28 | INF §5.1, NOR (Ley 19.496) | HU-28 | `subscriptions` | Pendiente | — |
| RF-29 | NOR (Ley 19.628 / 21.719) | HU-29 | `accounts` | Pendiente | RNF-06 |
| RF-30 | ENT | HU-30 | `finances` / reportes | Pendiente | — |
| RF-31 | ENT | HU-31 | `finances` / exportación | Pendiente | — |
| RF-32 | NOR, EQ | HU-32 | `core` (auditoría) | Pendiente | — |
| RF-33 | INF obj. 1 | HU-33 | `finances.views.dashboard` | `core/tests.py` | — |
| RF-34 | INF obj. 2 | HU-34 | `projections.services.proyectar_ingresos` | `projections/tests.py` | RN-12 |
| RF-35 | INF obj. 6, §X | HU-35 | `projections.services.evaluar_viabilidad` | `projections/tests.py` | RN-13 |
| RF-36 | INF obj. 2 | HU-36 | `projections` | Pendiente | — |
| RF-37 | INF (diferenciación), EQ | HU-37 | Nuevo módulo de asistencia | Pendiente | RNF-03 |
| RF-38 | EQ | HU-38 | `finances` / `projections` | Pendiente | — |

## Verificación

- 38 de 38 requerimientos tienen origen y componente asignado.
- 19 tienen prueba automatizada. De los 19 restantes, 17 aún no se construyen y su prueba es parte de su Definition of Done.
- Dos están construidos sin prueba dedicada: RF-13 (límite del plan) queda como deuda para el Sprint 2; RF-15 (gráfico) se verifica a mano en la revisión del sprint.
