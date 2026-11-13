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
| RF-10 | ENT | HU-10 | `finances.services.buscar_por_texto` | `finances/tests.py` BusquedaTests | — |
| RF-11 | ENT | HU-11 | `finances.Producto`, vistas de catálogo | `CatalogoTests` | RN-19, RNF-03 |
| RF-12 | ENT | HU-12 | `finances.importacion`, `importar_movimientos` | `ImportacionTests`, `LecturaImportacionTests` | RN-05, RN-20 |
| RF-13 | INF §5.1 | HU-13 | `finances.views._limite_alcanzado`, `core.alertas` | `ImportacionTests` (límite), `ReglasDeAlertaTests` | RN-05 |
| RF-14 | INF obj. 1 | HU-14 | `finances.views.dashboard` | test_crud_movimiento | RNF-15 |
| RF-15 | INF obj. 1 | HU-15 | `dashboard.html` (Chart.js) | — (visual) | — |
| RF-16 | INF obj. 2 | HU-16 | `finances.services.flujo_de_caja`, `projections.historial` | `IndicadoresConsultaTests` | RN-22 |
| RF-17 | INF obj. 1 | HU-17 | `finances.services.indicadores_del_mes` | `CalculosTests`, `IndicadoresConsultaTests` | RN-21 |
| RF-18 | INF §III (PESTEL tecnológico) | HU-18 | `core.services.BancoCentralService` | test_home_publica (caída de la API) | — |
| RF-19 | INF obj. 1 | HU-19 | `Categoria.naturaleza`, `clasificar_costos` | `CalculosTests`, `CategoriaNaturalezaTests` | RN-21 |
| RF-20 | INF §III, NOR (DL 825) | HU-20 | `taxes.services.calcular_iva` | `taxes/tests.py` CalculadoraIVATests | RN-10, RNF-17 |
| RF-21 | INF §III, NOR (Ley 21.133) | HU-21 | `taxes.services.calcular_honorarios_*` | `CalculadoraHonorariosTests` | RN-11, RNF-17 |
| RF-22 | NOR (DL 825) | HU-22 | `taxes.services.iva_del_mes` | `IVAAutomaticoTests` | RN-10, RN-23 |
| RF-23 | NOR (F29, Operación Renta) | HU-23 | `taxes.calendario`, `Feriado` | `CalendarioTributarioTests` | RN-25 |
| RF-24 | ENT | HU-24 | `core.alertas`, `Alerta`, `generar_alertas` | `ReglasDeAlertaTests`, `AlertasIntegracionTests` | RN-26 |
| RF-25 | NOR | HU-25 | `taxes.TasaTributaria`, `tasa_vigente` | `TasasEditablesTests` | RN-11, RN-24 |
| RF-26 | INF §5.1 | HU-26 | `subscriptions` | test_flujo_premium_y_evaluador | RN-03, RN-17 |
| RF-27 | INF §III (Khipu, Flow) | HU-27 | `subscriptions.services.procesar_notificacion` | `subscriptions/tests.py` PagosTests | RN-18, RN-27 |
| RF-28 | INF §5.1, NOR (Ley 19.496) | HU-28 | `evaluar_renovacion`, `renovar_suscripciones` | `ReglasTests`, `RenovacionTests` | RN-28 |
| RF-29 | NOR (Ley 19.628 / 21.719) | HU-29 | `accounts.DocumentoLegal`, `Consentimiento`, `accounts.legal` | `ConsentimientoTests` | RN-29, RNF-06 |
| RF-30 | ENT | HU-30 | `finances.reporte` | `RecomendacionesYReporteTests` | — |
| RF-31 | ENT | HU-31 | `finances.exportacion` | `ExportacionTests` | RNF-03 |
| RF-32 | NOR, EQ | HU-32 | `core.RegistroAuditoria`, `core.auditoria` | `AuditoriaTests` | RN-30 |
| RF-33 | INF obj. 1 | HU-33 | `finances.views.dashboard` | `core/tests.py` | — |
| RF-34 | INF obj. 2 | HU-34 | `projections.services.proyectar_ingresos` | `projections/tests.py` | RN-12 |
| RF-35 | INF obj. 6, §X | HU-35 | `projections.services.evaluar_viabilidad` | `projections/tests.py` | RN-13 |
| RF-36 | INF obj. 2 | HU-36 | `projections.services.proyectar_escenarios` | `EscenariosTests` | — |
| RF-37 | INF (diferenciación), EQ | HU-37 | `core.asistente`, `ConsultaAsistente` | `AsistenteTests` | RN-31, RNF-03 |
| RF-38 | EQ | HU-38 | `finances.recomendaciones` | `RecomendacionesTests` | — |

## Verificación

- 38 de 38 requerimientos tienen origen, componente y prueba automatizada (al 13-11-2026),
  salvo RF-15 (gráfico), que se verifica a mano en la revisión del sprint.
- Los requerimientos con origen ENT siguen pendientes de confirmar con el trabajo de campo (2.5).
