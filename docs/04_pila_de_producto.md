# Pila de producto priorizada

**Actividad 2.9** · Responsable: Carlos · Aprueba: Danilo · Semana 5

Una historia de usuario (HU) por requerimiento funcional (misma numeración: HU-06 ↔ RF-06).
Prioridad MoSCoW: **M** debe, **S** debería, **C** podría. Velocidad supuesta: 40 puntos por
sprint de dos semanas; ningún sprint la supera.

## Criterio de priorización

1. **Dependencias técnicas primero.** Sin cuenta (S1) no hay operaciones (S2); sin operaciones no hay indicadores (S3) ni impuestos automáticos (S4).
2. **Riesgo antes que comodidad.** El motor tributario (S4) va antes que los reportes (S5) porque requiere validación externa (actividad 5.6, semanas 17–18).
3. **Valor para el microempresario informal.** Registrar ventas y gastos en menos de un minuto es el núcleo; la asistencia inteligente (S6) es diferenciadora pero no imprescindible para el piloto.

## Sprint 1 (24 pts) — cerrado en semana 10

| HU | Como… quiero… para… | Pts | Prio. | Criterios de aceptación |
|---|---|---|---|---|
| HU-01 | Como microempresario quiero registrarme con mi RUT para tener mi cuenta. | 3 | M | RUT con o sin puntos; DV inválido se rechaza con mensaje; correo repetido se rechaza; queda en Plan Básico. |
| HU-02 | Como usuario quiero iniciar y cerrar sesión. | 1 | M | Login con usuario y clave; logout por POST. |
| HU-03 | Como usuario que olvidó su clave quiero recuperarla por correo. | 3 | M | Enlace de un solo uso; no revela si el correo existe; la nueva clave cumple las reglas de Django. |
| HU-04 | Como usuario quiero editar los datos de mi negocio y mi contraseña. | 1 | M | El RUT no es editable; los cambios se confirman con mensaje. |
| HU-05 | Como usuario quiero configurar mi régimen tributario y una meta de ventas. | 5 | M | Cinco regímenes; RN-04; la meta muestra barra de avance en el panel. |
| HU-06 | Como dueño quiero invitar a mi contador o socio para que vea o registre en mi negocio. | 8 | S | Invitación por correo con rol; aceptación solo con el mismo correo; selector de negocio; lector no edita; revocación inmediata. |
| HU-07 | Como usuario quiero descargar o borrar mis datos. | 3 | M | JSON con perfil, movimientos, categorías, suscripciones y colaboradores; borrado con clave. |

## Sprint 2 (29 pts) — semanas 11–12

| HU | Historia | Pts | Prio. | Criterios de aceptación |
|---|---|---|---|---|
| HU-08 | Registrar, editar y eliminar ventas y gastos. | 5 | M | Hecho en el prototipo; se revisa contra RN-07 y RN-08. |
| HU-09 | Crear categorías propias. | 3 | M | Hecho en el prototipo. |
| HU-10 | Buscar movimientos por texto además de filtrar por mes y tipo. | 3 | S | Búsqueda en descripción y categoría, sin distinguir mayúsculas ni tildes. |
| HU-11 | Tener un catálogo de productos y servicios con precio. | 8 | S | CRUD de productos; al registrar una venta se elige producto y cantidad y el monto se calcula. |
| HU-12 | Importar mis ventas desde un Excel o CSV. | 8 | S | Plantilla descargable; vista previa; errores por fila sin importar nada parcial; respeta el límite del plan. |
| HU-13 | Saber cuándo me acerco al límite de mi plan. | 2 | M | Hecho en el prototipo. |

## Sprint 3 (33 pts) — semanas 13–14

| HU | Historia | Pts | Prio. |
|---|---|---|---|
| HU-14 | Ver el balance del mes. | 3 | M |
| HU-15 | Ver el gráfico de seis meses. | 3 | M |
| HU-16 | Ver mi flujo de caja mensual real versus proyectado. | 8 | M |
| HU-17 | Conocer mi margen, punto de equilibrio y ticket promedio. | 8 | S |
| HU-18 | Ver la UF, la UTM y el dólar del día. | 3 | C |
| HU-19 | Distinguir gastos fijos de variables. | 8 | S |

## Sprint 4 (29 pts) — semanas 15–16

| HU | Historia | Pts | Prio. |
|---|---|---|---|
| HU-20 | Calcular el IVA de un período. | 3 | M |
| HU-21 | Calcular la retención de una boleta de honorarios. | 3 | M |
| HU-22 | Que el IVA del mes se calcule solo con mis movimientos. | 8 | M |
| HU-23 | Ver un calendario con mis vencimientos tributarios. | 5 | M |
| HU-24 | Recibir alertas de vencimientos, límite de plan y gastos inusuales. | 8 | S |
| HU-25 | Que las tasas se actualicen sin desplegar código. | 2 | S |

## Sprint 5 (36 pts) — semanas 17–18

| HU | Historia | Pts | Prio. |
|---|---|---|---|
| HU-26 | Elegir entre Plan Básico y Premium. | 3 | M |
| HU-27 | Pagar Premium con Khipu o Flow.cl. | 8 | M |
| HU-28 | Que mi suscripción se renueve o venza correctamente. | 5 | M |
| HU-29 | Aceptar términos y política de privacidad de forma registrada. | 5 | M |
| HU-30 | Descargar un reporte mensual en PDF. | 8 | S |
| HU-31 | Exportar mis movimientos a Excel. | 5 | S |
| HU-32 | Que quede registro de las acciones sensibles. | 2 | S |

## Sprint 6 (39 pts) — semanas 19–20

| HU | Historia | Pts | Prio. |
|---|---|---|---|
| HU-33 | Ver un panel con lo más importante del mes. | 5 | M |
| HU-34 | Proyectar mis ingresos de los próximos meses. | 5 | M |
| HU-35 | Evaluar si una inversión conviene (VAN/TIR). | 5 | S |
| HU-36 | Comparar escenarios optimista, base y pesimista. | 8 | C |
| HU-37 | Preguntar en lenguaje natural sobre mis finanzas. | 13 | C |
| HU-38 | Recibir recomendaciones automáticas. | 3 | C |
