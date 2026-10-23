# Estado del proyecto frente a la carta Gantt — semana 10

Cubre las 32 actividades que comienzan entre las semanas 1 y 10.

**Leyenda:** ✅ entregable en el repositorio · 📋 instrumento o procedimiento listo, **falta ejecutarlo** (requiere personas, terceros o cuentas externas) · 🔄 transversal en curso · ⛔ fuera del alcance del repositorio

## Fase 1 — Inicio y análisis

| Cód. | Actividad | Sem. | Estado | Entregable |
|---|---|---|---|---|
| 6.0 | Verificación de la cuenta AWS y presupuesto de alertas | 1 | 📋 | [11_infraestructura.md §6.0](11_infraestructura.md), [deploy/aws/](../deploy/aws/) — falta que alguien con acceso a la cuenta lo aplique |
| 1.1 | Planificación y línea base | 1 | ✅ | Carta Gantt + [pila de producto](04_pila_de_producto.md) (190 pts) |
| 1.6 | Incorporación al informe de los ajustes acordados | 1–2 | ⛔ | El informe no está en el repositorio |
| 2.1 | Levantamiento documental y de fuentes oficiales | 1–2 | ✅ | Fuentes citadas en [13_marco_normativo.md](13_marco_normativo.md) |
| 2.2 | Revisión normativa y tributaria | 1–3 | ✅ | [13_marco_normativo.md](13_marco_normativo.md) — con checklist de verificación pendiente |
| 7.1 | Constitución de la sociedad y trámites | 2–4 | ⛔ | Trámite legal (Ley 20.659) |
| 7.3 | Acuerdos de cesión de derechos sobre el código | 2–3 | ⛔ | Requiere asesoría legal y firmas — **hito H2**, ver riesgo R01 |
| 2.3 | Análisis comparativo de la oferta | 2 | ✅ | [14_analisis_competencia.md](14_analisis_competencia.md) — verificar precios |
| 2.4 | Diseño de instrumentos primarios | 2 | ✅ | [12_instrumentos_levantamiento.md](12_instrumentos_levantamiento.md) (guion de 14 preguntas + encuesta) |
| 2.5 | Aplicación de entrevistas y encuesta | 3–5 | 📋 | Instrumentos listos; requiere trabajo de campo |
| 2.6 | Requerimientos funcionales | 3–4 | ✅ | [01_requerimientos_funcionales.md](01_requerimientos_funcionales.md) (38 RF) |
| 2.7 | Requerimientos no funcionales | 4 | ✅ | [02_requerimientos_no_funcionales.md](02_requerimientos_no_funcionales.md) (17 RNF) |
| 2.8 | Reglas de negocio | 4 | ✅ | [03_reglas_de_negocio.md](03_reglas_de_negocio.md) (18 RN) |
| 2.9 | Priorización de la pila de producto | 5 | ✅ | [04_pila_de_producto.md](04_pila_de_producto.md) |
| 2.10 | Matriz de trazabilidad | 5 | ✅ | [05_matriz_trazabilidad.md](05_matriz_trazabilidad.md) |

## Fase 2 — Diseño

| Cód. | Actividad | Sem. | Estado | Entregable |
|---|---|---|---|---|
| 3.1 | Proceso actual (AS-IS) | 5 | ✅ | [06_procesos_as_is_to_be.md](06_procesos_as_is_to_be.md) — contrastar con 2.5 |
| 3.5 | Stack tecnológico | 6 | ✅ | [07_arquitectura.md](07_arquitectura.md#stack-tecnológico-actividad-35) |
| 3.3 | Arquitectura (C4) | 6–7 | ✅ | [07_arquitectura.md](07_arquitectura.md) (contexto, contenedores, componentes) |
| 3.2 | Proceso propuesto (TO-BE) | 6 | ✅ | [06_procesos_as_is_to_be.md](06_procesos_as_is_to_be.md) |
| 3.4 | Modelo de datos | 7 | ✅ | [09_modelo_de_datos.md](09_modelo_de_datos.md) |
| 3.6 | Interfaz y prototipo navegable | 7–8 | ✅ | La aplicación misma (`templates/`, `static/`) — falta la validación con usuarios del hito H4 |
| 3.7 | Plan de escalamiento | 8 | ✅ | [08_plan_escalamiento.md](08_plan_escalamiento.md) |
| 6.1 | Ambientes e integración continua | 7–8 | ✅ | [CI](../.github/workflows/ci.yml), [Dockerfile](../Dockerfile), [docker-compose.prod.yml](../docker-compose.prod.yml) — falta crear la instancia EC2 |
| 6.4 | Endurecimiento del servidor y firewall | 8 | ✅ | [deploy/endurecer_servidor.sh](../deploy/endurecer_servidor.sh), [Nginx](../deploy/nginx/finmicro.conf), Security Group en [11_infraestructura.md](11_infraestructura.md) — se ejecuta al crear la instancia |
| 5.1 | Definition of Done | 8 | ✅ | [10_definition_of_done.md](10_definition_of_done.md) |

## Fase 3 — Construcción

| Cód. | Actividad | Sem. | Estado | Entregable |
|---|---|---|---|---|
| 4.1 | Sprint 1: cuenta, configuración y colaboradores (24 pts) | 9–10 | ✅ | [15_sprint_1.md](15_sprint_1.md) — 24/24 pts; falta la revisión con el aprobador y la retrospectiva |

## Transversales

| Cód. | Actividad | Estado | Entregable |
|---|---|---|---|
| 1.2 | Seguimiento del avance y control de cambios | 🔄 | Este documento |
| 1.3 | Gestión de riesgos | 🔄 | [16_riesgos.md](16_riesgos.md) |
| 1.4 | Coordinación con el académico guía | ⛔ | Reuniones del equipo |
| 4.7 | Revisión cruzada de código | 🔄 | [CONTRIBUTING.md](../CONTRIBUTING.md), [plantilla de PR](../.github/pull_request_template.md) |
| 4.8 | Gestión del repositorio y control de versiones | 🔄 | [CONTRIBUTING.md](../CONTRIBUTING.md) (ramas, commits, protección de `main`) |
| 5.2 | Pruebas automatizadas | 🔄 | 45 pruebas; corren en la CI |

## Hitos vencidos a la semana 10

| Hito | Sem. | Condición | Estado |
|---|---|---|---|
| H1 | 2 | Cuenta AWS verificada, presupuesto configurado e informe actualizado | 📋 Falta aplicar 6.0 y actualizar el informe (1.6) |
| H2 | 4 | Cesión de derechos firmada | ⛔ Confirmar con la asesoría legal (riesgo R01) |
| H3 | 5 | Requerimientos y pila de producto aprobados | ✅ Documentos listos — falta la aprobación de Carlos |
| H4 | 8 | Arquitectura, modelo de datos y ambientes operativos; prototipo validado | ✅ Documentos y CI listos — falta crear la instancia y validar el prototipo con usuarios |

## Adelanto respecto de la Gantt

El prototipo ya incluye funciones de sprints posteriores (67 de los 190 pts en estado
*Hecho*, ver [resumen de requerimientos](01_requerimientos_funcionales.md#resumen)). Se
mantienen en su sprint original y se verifican en su revisión.
