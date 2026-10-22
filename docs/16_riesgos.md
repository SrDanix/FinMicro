# Registro de riesgos del proyecto

**Actividad 1.3** (transversal, semanas 2–26) · Responsable: Danilo · Aprueba: Carlos

Escala: probabilidad (P) e impacto (I) de 1 a 3. Exposición = P × I. Revisar cada dos semanas, al cierre de sprint.

| ID | Riesgo | P | I | Exp. | Respuesta | Dueño | Estado (sem. 10) |
|---|---|---|---|---|---|---|---|
| R01 | La cesión de derechos (7.3) no se firma a tiempo y los desarrolladores no socios no pueden escribir código | 2 | 3 | 6 | Prioridad de la asesoría legal; mientras tanto, solo los socios integran código en `main` | Danilo | **Verificar**: hito H2 era en la semana 4 |
| R02 | Las entrevistas (2.5) no alcanzan la muestra por disponibilidad de terceros | 3 | 2 | 6 | Encuesta en línea como complemento; reclutar en ferias con incentivo | Marcelo | **Verificar** con Marcelo |
| R03 | Fin del plan gratuito de AWS o gasto inesperado | 2 | 2 | 4 | Presupuesto con alertas (6.0); revisión mensual | Danilo | Configuración lista, falta aplicarla |
| R04 | La asesoría contable objeta el motor tributario (5.6) | 2 | 3 | 6 | Validación adelantada a semanas 17–18; cálculos aislados y con pruebas | Danilo | Abierto |
| R05 | Cambio de tasas o normas tributarias durante el proyecto | 2 | 2 | 4 | Tasas parametrizables (RF-25); revisión de sii.cl por sprint | Marcelo | Abierto |
| R06 | Entrada en vigencia de la Ley 21.719 durante el piloto | 3 | 2 | 6 | Diseñar privacidad bajo la nueva ley (7.2, 7.4, 7.5); ya existen exportación y borrado | Carlos | Mitigado en parte (RF-07) |
| R07 | Fuga de datos entre negocios | 1 | 3 | 3 | `request.negocio` obligatorio; pruebas de aislamiento; revisión cruzada | Luciano | Mitigado (pruebas en CI) |
| R08 | Punto único de falla (una sola instancia) | 2 | 2 | 4 | Respaldos diarios y reconstrucción en < 1 h (plan de escalamiento) | Danilo | Abierto (6.2, sem. 21) |
| R09 | Sobrecarga de Marcelo (18 actividades como responsable) | 2 | 2 | 4 | Revisar reparto en cada planificación de sprint | Carlos | Abierto |
| R10 | Baja adopción en el piloto | 2 | 3 | 6 | Onboarding acompañado (7.7); prueba de usabilidad en semana 13 | Carlos | Abierto |
| R11 | mindicador.cl no disponible | 2 | 1 | 2 | Caché de 6 h; la portada no se rompe si falla (probado) | Danilo | Mitigado |
