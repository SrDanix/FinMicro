# Prueba de usabilidad y de aceptación abreviada

**Actividades X-03 y X-13 de la carta Gantt** · Responsables: Luciano y Carlos · Semanas 15–16

El piloto original (15 participantes durante 4 semanas) no cabe antes de la defensa. Este protocolo lo
reemplaza por una prueba de usabilidad (X-03) y una prueba de aceptación abreviada (X-13) que se pueden
hacer en una semana con 5 a 8 microempresarios. Requiere personas reales: el repositorio solo deja listo
el material.

## Preparación (una vez)

1. Ambiente: la instancia EC2 con HTTPS (guía 18, etapa 2), con la versión que se va a defender.
2. Una cuenta por participante, creada por el mismo participante en `/cuenta/registro/` (así se prueba
   el registro y queda su consentimiento, RF-29). Para Premium, el equipo cambia la suscripción en
   `/admin/` → Suscripciones.
3. Consentimiento informado para la prueba (uso de la información solo para el proyecto, sin
   grabar pantallas con datos reales sin permiso).
4. Un integrante modera y otro anota; cronómetro en el celular.

## Parte 1 · Usabilidad (X-03, RNF-10)

Sin ayuda del moderador, salvo que el participante quede bloqueado más de 2 minutos (se anota como
"con ayuda"). Se le lee cada tarea y se mide el tiempo desde que toca la pantalla hasta que termina.

| N.º | Tarea | Éxito si… | Meta |
|---|---|---|---|
| T1 | Crea tu cuenta con tu RUT | llega al panel | sin ayuda |
| T2 | Registra la venta de hoy por $15.000 | aparece en el panel | **< 60 s** (RNF-10) |
| T3 | Registra un gasto de bencina por $8.000 | aparece en Movimientos | < 60 s |
| T4 | Busca cuánto gastaste en "bencina" | usa la búsqueda o el filtro | < 90 s |
| T5 | ¿Cuánto IVA pagarías este mes? (si está afecto) | encuentra Impuestos → IVA del mes | < 90 s |
| T6 | ¿Cuándo vence tu próximo F29? | abre el calendario | < 60 s |
| T7 | Agrega un producto a tu catálogo y véndelo | la venta queda con el monto calculado | < 2 min |

**Criterio de aceptación de RNF-10:** al menos 80 % de los participantes completa T2 sin ayuda en
menos de 60 segundos.

Al final, la escala SUS (10 preguntas, 1 a 5) y dos preguntas abiertas: *¿Qué fue lo más difícil?* y
*¿Lo usarías en tu negocio? ¿Por qué?*

## Parte 2 · Aceptación abreviada (X-13)

Durante 5 días hábiles cada participante registra sus ventas y gastos reales (o de una semana típica).
Al cierre, en una conversación de 20 minutos:

| Criterio | Cómo se verifica | Aceptado si… |
|---|---|---|
| Registro diario | Movimientos en el admin, por día | registró al menos 4 de 5 días |
| Comprensión de indicadores | Explica su margen y su punto de equilibrio con sus palabras | lo explica sin ayuda |
| Utilidad del IVA estimado y del calendario | Lo compara con lo que declara o le dice su contador | lo considera útil |
| Confianza en los datos | Pregunta directa | no reporta errores de cálculo |
| Disposición a pagar Premium ($9.990) | Pregunta directa | registrar sí / no / a qué precio |

## Registro de resultados

| Participante | Rubro | T1 | T2 (s) | T3 (s) | T4 | T5 | T6 | T7 | SUS | Días con registro | ¿Acepta? | Observaciones |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | | | | | | | | | | | | |
| P2 | | | | | | | | | | | | |
| P3 | | | | | | | | | | | | |
| P4 | | | | | | | | | | | | |
| P5 | | | | | | | | | | | | |

Los defectos encontrados se registran como issues en GitHub con la etiqueta `piloto`; los de prioridad
alta se corrigen antes de congelar la versión (X-15).
