# Especificación de requerimientos funcionales

**Actividad 2.6** · Responsable: Marcelo · Aprueba: Carlos · Semanas 3–4

Cada requerimiento indica el sprint en que se construye (carta Gantt 4.1–4.6), su
estimación en puntos de historia y su estado en el repositorio. El total comprometido
es de **190 puntos**: 24 + 29 + 33 + 29 + 36 + 39.

Estados: **Hecho** (en `main`, con pruebas) · **Parcial** (existe una versión básica) · **Pendiente**.

## Sprint 1 — Gestión de cuenta, configuración y colaboradores (24 pts, semanas 9–10)

| ID | Requerimiento | Pts | Estado |
|---|---|---|---|
| RF-01 | El sistema permite registrarse con usuario, correo, RUT, nombre y rubro del negocio, validando el dígito verificador del RUT y que el correo no esté en uso. | 3 | Hecho |
| RF-02 | El sistema permite iniciar y cerrar sesión. | 1 | Hecho |
| RF-03 | El sistema permite recuperar la contraseña mediante un enlace de un solo uso enviado al correo. | 3 | Hecho |
| RF-04 | El usuario puede editar los datos de su negocio y cambiar su contraseña. | 1 | Hecho |
| RF-05 | El usuario configura su régimen tributario, si está afecto a IVA, si emite boletas de honorarios y una meta de ventas mensual, cuyo avance se ve en el panel. | 5 | Hecho |
| RF-06 | El dueño invita colaboradores por correo con rol *solo lectura* o *editor*; el colaborador acepta, cambia entre negocios y el dueño puede revocar el acceso. | 8 | Hecho |
| RF-07 | El usuario descarga todos sus datos y puede eliminar su cuenta con todos sus registros (Ley N°19.628). | 3 | Hecho |

## Sprint 2 — Registro de operaciones, catálogo e importación (29 pts, semanas 11–12)

| ID | Requerimiento | Pts | Estado |
|---|---|---|---|
| RF-08 | Registrar, editar y eliminar ingresos y gastos con fecha, monto, categoría y descripción. | 5 | Hecho |
| RF-09 | Crear categorías propias además de las categorías del sistema. | 3 | Hecho |
| RF-10 | Filtrar movimientos por mes, año y tipo, y buscar por texto. | 3 | Parcial (falta búsqueda por texto) |
| RF-11 | Mantener un catálogo de productos y servicios con precio, para registrar ventas a partir de él. | 8 | Pendiente |
| RF-12 | Importar movimientos desde un archivo CSV o Excel con vista previa y detección de errores por fila. | 8 | Pendiente |
| RF-13 | Limitar los movimientos mensuales según el plan y avisar al acercarse al límite. | 2 | Hecho |

## Sprint 3 — Indicadores financieros y flujo de caja (33 pts, semanas 13–14)

| ID | Requerimiento | Pts | Estado |
|---|---|---|---|
| RF-14 | Mostrar balance, ingresos y gastos del mes en curso. | 3 | Hecho |
| RF-15 | Graficar ingresos y gastos de los últimos seis meses. | 3 | Hecho |
| RF-16 | Mostrar el flujo de caja mensual (saldo inicial, entradas, salidas, saldo final) y compararlo con lo proyectado. | 8 | Pendiente |
| RF-17 | Calcular margen bruto, punto de equilibrio y ticket promedio. | 8 | Pendiente |
| RF-18 | Mostrar UF, UTM, dólar e IPC del día desde una fuente oficial. | 3 | Hecho |
| RF-19 | Clasificar gastos en fijos y variables y mostrar su proporción. | 8 | Pendiente |

## Sprint 4 — Motor de reglas tributarias y alertas (29 pts, semanas 15–16)

| ID | Requerimiento | Pts | Estado |
|---|---|---|---|
| RF-20 | Calcular IVA débito, crédito y saldo a pagar o remanente. | 3 | Hecho |
| RF-21 | Calcular retención y líquido de una boleta de honorarios, en ambos sentidos, según el año. | 3 | Hecho |
| RF-22 | Calcular el IVA del mes automáticamente a partir de los movimientos en categorías afectas. | 8 | Pendiente |
| RF-23 | Mostrar un calendario tributario con los vencimientos que aplican al régimen del usuario (F29 mensual, Operación Renta). | 5 | Pendiente |
| RF-24 | Generar alertas: vencimientos próximos, límite de plan y gastos inusuales respecto del promedio. | 8 | Pendiente |
| RF-25 | Mantener las tasas tributarias en una tabla parametrizable por año, editable desde el administrador. | 2 | Parcial (tabla en código) |

## Sprint 5 — Suscripción, cumplimiento y reportes (36 pts, semanas 17–18)

| ID | Requerimiento | Pts | Estado |
|---|---|---|---|
| RF-26 | Ofrecer Plan Básico gratuito y Plan Premium, y cambiar entre ellos. | 3 | Hecho |
| RF-27 | Cobrar la suscripción Premium mediante Khipu o Flow.cl. | 8 | Parcial (modo simulado) |
| RF-28 | Controlar renovación y vencimiento de la suscripción y degradar a Básico si no se paga. | 5 | Pendiente |
| RF-29 | Registrar el consentimiento a los términos y a la política de privacidad, con fecha y versión. | 5 | Pendiente |
| RF-30 | Generar un reporte mensual en PDF con el resumen financiero y tributario. | 8 | Pendiente |
| RF-31 | Exportar movimientos a Excel. | 5 | Pendiente |
| RF-32 | Mantener un registro de auditoría de acciones sensibles (inicio de sesión, cambios de plan, eliminación de datos). | 2 | Pendiente |

## Sprint 6 — Panel, proyección y asistencia inteligente (39 pts, semanas 19–20)

| ID | Requerimiento | Pts | Estado |
|---|---|---|---|
| RF-33 | Panel principal con resumen, gráfico, últimos movimientos y avance de la meta. | 5 | Hecho |
| RF-34 | Proyectar los ingresos de los próximos tres meses a partir de los meses completos registrados. | 5 | Hecho |
| RF-35 | Evaluar la viabilidad de una inversión con VAN, TIR, payback y relación beneficio/costo (Premium). | 5 | Hecho |
| RF-36 | Mostrar escenarios de proyección optimista, base y pesimista. | 8 | Pendiente |
| RF-37 | Responder preguntas en lenguaje natural sobre las finanzas del propio negocio (asistente inteligente). | 13 | Pendiente |
| RF-38 | Entregar recomendaciones automáticas a partir de los indicadores (p. ej. gasto creciente en una categoría). | 3 | Pendiente |

## Resumen

| Sprint | Puntos | Hechos | Parciales | Pendientes |
|---|---|---|---|---|
| 1 | 24 | 24 | 0 | 0 |
| 2 | 29 | 10 | 3 | 16 |
| 3 | 33 | 9 | 0 | 24 |
| 4 | 29 | 6 | 2 | 21 |
| 5 | 36 | 3 | 8 | 25 |
| 6 | 39 | 15 | 0 | 24 |
| **Total** | **190** | **67** | **13** | **110** |

Los parciales se cuentan por los puntos completos del requerimiento. Varios
requerimientos de sprints posteriores ya estaban hechos en el prototipo (actividad 3.6);
se mantienen en su sprint original para no alterar la línea base, y en la revisión de cada
sprint se verifica que cumplan los criterios de aceptación.
