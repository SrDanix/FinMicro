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
