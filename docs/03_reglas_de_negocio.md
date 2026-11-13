# Reglas de negocio

**Actividad 2.8** · Responsable: Marcelo · Aprueba: Carlos · Semana 4 · Predecesoras: 2.2, 2.6

| ID | Regla | Dónde se aplica |
|---|---|---|
| RN-01 | El RUT tiene el formato `12345678-9` y un dígito verificador válido (módulo 11). Se acepta con puntos y se guarda sin ellos, con `K` mayúscula. | `accounts.models.validar_rut` |
| RN-02 | Un correo electrónico pertenece a una sola cuenta. | `RegistroForm.clean_email` |
| RN-03 | Todo usuario nuevo queda suscrito al Plan Básico. Ningún usuario queda sin plan. | `subscriptions.services.asegurar_plan_basico` |
| RN-04 | Un contribuyente *sin inicio de actividades* no puede marcarse como afecto a IVA. | `ConfiguracionForm.clean` |
| RN-05 | El Plan Básico admite 60 movimientos por mes calendario; el Premium no tiene límite. Al llegar al 80 % se avisa. | `finances.views._limite_alcanzado`, panel |
| RN-06 | El límite de movimientos se cuenta sobre el plan del **dueño** del negocio, aunque registre un colaborador. | `finances.views.crear_movimiento` |
| RN-07 | Un movimiento debe tener el mismo tipo (ingreso/gasto) que su categoría. | `Movimiento.clean`, `MovimientoForm.clean` |
| RN-08 | El monto de un movimiento es de al menos $1. Los montos en CLP se redondean a peso entero (medio peso hacia arriba). | `Movimiento.monto`, `taxes.services._redondear_clp` |
| RN-09 | Las categorías del sistema son visibles para todos; las categorías propias solo para su negocio. | `MovimientoForm.__init__` |
| RN-10 | IVA = 19 % del neto. Si el crédito supera al débito, el saldo es remanente a favor, no un pago. | `taxes.services.calcular_iva` |
| RN-11 | Retención de honorarios según año (Ley 21.133): 14,5 % (2025), 15,25 % (2026), 16 % (2027), 17 % (2028 en adelante). | `taxes.services.TABLA_RETENCION_HONORARIOS` |
| RN-12 | La proyección de ingresos usa solo meses completos y requiere al menos dos meses con ingresos. Los meses previos al primer ingreso no se cuentan. Nunca proyecta valores negativos. | `projections.views`, `projections.services` |
| RN-13 | El evaluador de viabilidad es exclusivo del Plan Premium. | `projections.views.evaluador_viabilidad` |
| RN-14 | Un colaborador *solo lectura* ve todo el negocio pero no puede crear, editar ni eliminar movimientos ni categorías. Un *editor* sí puede. Ninguno puede cambiar el plan, la configuración ni invitar a otros. | `accounts.negocio.requiere_edicion` |
| RN-15 | Una invitación solo la puede aceptar una cuenta con el mismo correo al que se envió. El dueño puede revocar un acceso en cualquier momento y el colaborador vuelve a su propio negocio. | `accounts.views.aceptar_invitacion`, `NegocioActivoMiddleware` |
| RN-16 | Eliminar la cuenta borra de forma permanente perfil, movimientos, categorías propias, suscripciones y colaboraciones, previa confirmación con contraseña. | `accounts.views.eliminar_cuenta` |
| RN-17 | Un cambio de plan solo ocurre por POST y tras una pantalla de confirmación. | `subscriptions.views.suscribirse` |
| RN-18 | Mientras no existan credenciales de pasarela, los pagos se simulan y así se indica en pantalla. | `subscriptions.services`, `PAGOS_MODO_SIMULADO` |
| RN-19 | Una venta puede registrarse desde el catálogo: el monto es precio × cantidad si no se ingresa otro. Solo los ingresos llevan producto. | `MovimientoForm.clean`, `Movimiento.clean` |
| RN-20 | La importación es todo o nada: si una fila tiene error o se supera el límite del plan (RN-05) no se importa ninguna. Las filas ya registradas se omiten. Montos en pesos enteros, sin fechas futuras, máximo 1.000 filas y 2 MB. | `finances.importacion`, `finances.views.confirmar_importacion` |
| RN-21 | Costo de ventas = gastos variables del mes. Margen bruto = ventas − costo de ventas. Punto de equilibrio = costos fijos ÷ (1 − gastos variables ÷ ventas); no existe si no hay ventas o si los variables las igualan. | `finances.services` |
| RN-22 | Saldo inicial de caja de un mes = caja declarada al empezar + todo lo registrado en los meses anteriores. | `finances.services.flujo_de_caja` |
| RN-23 | IVA automático: los montos registrados incluyen IVA; generan débito o crédito solo las categorías y productos afectos; se redondea una vez por período; el remanente se arrastra hasta 12 meses sin reajuste. *A validar con la asesoría contable (X-12).* | `taxes.services.iva_del_mes` |
| RN-24 | La tasa aplicable a una fecha es la de inicio más reciente que la cubre; si la tabla no tiene una, se usa la tasa legal del código. | `taxes.services.tasa_vigente` |
| RN-25 | F29 vence el día 12 del mes siguiente (el 20 si está afecto a IVA y emite documentos electrónicos); F22 el 30 de abril. Un vencimiento en fin de semana o feriado se corre al día hábil siguiente. Sin inicio de actividades no hay vencimientos. | `taxes.calendario` |
| RN-26 | Alertas: vencimiento a 7 días o menos; plan al 80 % y al 100 %; gasto mayor al doble de la mediana de la categoría (con al menos 3 gastos previos). Una misma situación genera una sola alerta. | `core.alertas` |
| RN-27 | Un plan pagado se activa solo si la pasarela confirma el pago al consultarla y la orden y el monto coinciden. Un aviso repetido no cambia nada. | `subscriptions.services.procesar_notificacion` |
| RN-28 | Premium dura un mes; renovar suma el mes al final del período vigente. Se avisa 3 días antes; al vencer hay 3 días de gracia y luego vuelve al Plan Básico, sin perder datos. | `subscriptions.services`, `renovar_suscripciones` |
| RN-29 | Para usar la app hay que aceptar la versión vigente de los términos y de la política de privacidad; un documento publicado no se modifica. | `accounts.legal`, `DocumentoLegalAdmin` |
| RN-30 | El registro de auditoría solo se agrega: nadie lo edita ni lo borra desde la app o el administrador. | `core.auditoria`, `RegistroAuditoriaAdmin` |
| RN-31 | El asistente es exclusivo del Plan Premium, solo recibe datos del negocio activo y tiene un tope diario de preguntas. | `core.asistente` |
