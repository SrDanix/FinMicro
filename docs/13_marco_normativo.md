# Marco normativo y tributario aplicable

**Actividad 2.2** · Responsable: Marcelo · Aprueba: Danilo · Semanas 1–3

> Resumen de trabajo para el equipo, no asesoría legal ni tributaria. Antes de cerrar la
> actividad, cada punto debe contrastarse con la fuente oficial vigente (bcn.cl, sii.cl)
> y el motor tributario debe validarse con la asesoría contable (actividad 5.6).

## Tributario

| Norma | Qué establece | Impacto en FinMicro |
|---|---|---|
| **DL 825 (Ley sobre Impuesto a las Ventas y Servicios)** | IVA de 19 % sobre ventas y servicios afectos. Débito fiscal (ventas) menos crédito fiscal (compras con respaldo). | RF-20, RF-22; RN-10. Categorías marcadas como afectas. |
| **Formulario 29** | Declaración y pago mensual de IVA y retenciones. Plazo general: día 12 del mes siguiente; día 20 para quienes declaran por internet y emiten documentos electrónicos. | RF-23 calendario; RF-24 alertas. Confirmar plazos vigentes en sii.cl. |
| **Ley 21.133** | Aumento gradual de la retención de boletas de honorarios: 14,5 % (2025), 15,25 % (2026), 16 % (2027), 17 % (2028). | RF-21; RN-11; tabla en `taxes/services.py`. |
| **Ley 21.210 (Modernización Tributaria, 2020)** | Régimen Pro Pyme (art. 14 D N°3 y N°8 transparente); obligatoriedad de la boleta electrónica. | RF-05: régimen tributario en la configuración. |
| **Ley sobre Impuesto a la Renta, art. 34** | Renta presunta para actividades específicas (agrícola, transporte, minería). | Opción de régimen en RF-05. |
| **Operación Renta (Formulario 22)** | Declaración anual de renta, en abril. | RF-23 calendario. |
| **Inicio de actividades (SII)** | Trámite para formalizarse y emitir documentos tributarios. | RN-04: sin inicio no se emiten documentos afectos. |

## Protección de datos y consumidor

| Norma | Qué establece | Impacto en FinMicro |
|---|---|---|
| **Ley 19.628 (protección de la vida privada)** | Tratamiento de datos personales con finalidad informada; derechos de acceso, rectificación, cancelación y oposición. | RF-07 exportar y eliminar datos; RF-29 consentimiento. |
| **Ley 21.719 (nueva ley de protección de datos personales)** | Publicada en diciembre de 2024. Moderniza la Ley 19.628: crea la Agencia de Protección de Datos Personales, exige base de licitud, deber de seguridad, notificación de brechas y registro de actividades de tratamiento; establece multas. Entra en vigencia en diciembre de 2026, **durante el piloto de FinMicro**. | Actividades 7.2 (política de privacidad), 7.4 (registro de actividades de tratamiento) y 7.5 (respuesta a incidentes). Diseñar ya bajo sus exigencias. |
| **Ley 19.496 (protección de los derechos de los consumidores)** | Información clara de precio y condiciones; reglas para contratos de adhesión y suscripciones. | RF-26, RF-28: precio visible, condiciones de renovación y cancelación. |

## Societario y propiedad intelectual

| Norma | Qué establece | Impacto en el proyecto |
|---|---|---|
| **Ley 20.659 (Empresa en un Día)** | Constitución simplificada de sociedades en registroempresas.cl. | Actividad 7.1. |
| **Ley 17.336 (propiedad intelectual)** | El software es obra protegida; su titularidad debe quedar clara cuando lo desarrollan personas que no son socias. | Actividad 7.3: cesión de derechos antes de que los desarrolladores no socios escriban código (hito H2). |

## Pendiente para cerrar 2.2

- [ ] Confirmar plazos del F29 y calendario de Operación Renta del año en sii.cl
- [ ] Confirmar fecha exacta de entrada en vigencia de la Ley 21.719 en bcn.cl
- [ ] Revisión por la asesoría legal (Ley 21.719 y Ley 19.496)
