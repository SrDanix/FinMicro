# Especificación de requerimientos no funcionales

**Actividad 2.7** · Responsable: Luciano · Aprueba: Danilo · Semana 4

Cada requerimiento tiene un umbral verificable y la forma de medirlo. Los umbrales están
pensados para la arquitectura MVP sobre una sola instancia EC2 (ver
[07_arquitectura.md](07_arquitectura.md)).

| ID | Categoría | Requerimiento | Umbral | Cómo se verifica | Estado |
|---|---|---|---|---|---|
| RNF-01 | Seguridad | Las contraseñas se almacenan con hash adaptativo, nunca en texto plano. | PBKDF2 (por defecto en Django) | Revisión de `settings.py` | Cumple |
| RNF-02 | Seguridad | Toda la comunicación en producción va cifrada. | HTTPS obligatorio, HSTS ≥ 7 días | `check --deploy` en CI | Cumple (config.) |
| RNF-03 | Seguridad | Cada negocio solo ve sus datos o los de negocios a los que fue invitado. | 0 fugas en las pruebas de aislamiento | `accounts/tests.py` (colaboradores) | Cumple |
| RNF-04 | Seguridad | Protección contra CSRF, XSS y clickjacking. | Middlewares activos | `check --deploy` | Cumple |
| RNF-05 | Seguridad | Las dependencias no tienen vulnerabilidades conocidas altas o críticas. | 0 altas/críticas | `pip-audit` (actividad 5.3) | Por verificar (sem. 21) |
| RNF-06 | Privacidad | El usuario puede acceder a sus datos y eliminarlos (Ley N°19.628). | Exportación y borrado en ≤ 1 clic + confirmación | RF-07 | Cumple |
| RNF-07 | Rendimiento | Las páginas principales responden rápido. | p95 < 800 ms con 50 usuarios concurrentes | Prueba de carga (actividad 5.4) | Por verificar (sem. 21) |
| RNF-08 | Disponibilidad | El servicio está disponible durante el piloto. | ≥ 99 % mensual | Monitoreo (actividad 6.2) | Por verificar |
| RNF-09 | Recuperación | Los datos se respaldan y se pueden restaurar. | RPO 24 h, RTO 4 h | Respaldo diario + restauración probada (6.2) | Por verificar |
| RNF-10 | Usabilidad | Un microempresario sin experiencia registra un movimiento sin ayuda. | ≥ 80 % de éxito, < 60 s | Prueba de usabilidad (actividad 5.5) | Por verificar (sem. 13) |
| RNF-11 | Usabilidad | La interfaz funciona en celular. | Usable a 375 px de ancho, sin scroll horizontal | Revisión en navegador | Cumple |
| RNF-12 | Accesibilidad | Contraste y etiquetas de formulario adecuados. | WCAG 2.1 AA en las pantallas principales | Lighthouse ≥ 90 en accesibilidad | Por verificar |
| RNF-13 | Mantenibilidad | El código tiene pruebas automatizadas que corren en cada cambio. | CI en verde para integrar; servicios con pruebas unitarias | GitHub Actions | Cumple |
| RNF-14 | Portabilidad | El sistema se despliega igual en cualquier máquina. | Imagen Docker reproducible | `docker build` en CI | Cumple |
| RNF-15 | Localización | Montos en pesos chilenos con separador de miles con punto; fechas dd/mm/aaaa; interfaz en español de Chile. | 100 % de las pantallas | Pruebas de contenido | Cumple |
| RNF-16 | Costo | La infraestructura no supera el presupuesto mensual. | ≤ USD 15/mes, alertas al 50 %, 80 % y 100 % proyectado | AWS Budgets (actividad 6.0) | Configuración lista |
| RNF-17 | Exactitud | Los cálculos tributarios coinciden con los ejemplos oficiales del SII. | Diferencia ≤ $1 por redondeo | `taxes/tests.py` + validación contable (5.6) | Cumple en pruebas |
