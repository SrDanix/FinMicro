# Sprint 1 — Gestión de cuenta, configuración y colaboradores

**Actividad 4.1** · Responsable: Marcelo · Aprueba: Danilo · Semanas 9–10 · Comprometido: 24 pts

## Objetivo del sprint

Que un microempresario pueda crear y administrar su cuenta, configurar su situación
tributaria y dar acceso a su contador o socio, con control total sobre sus datos.

## Pila del sprint

| HU | Pts | Estado | Entregado |
|---|---|---|---|
| HU-01 Registro con RUT validado | 3 | ✅ Terminada | Validación módulo 11, RUT con o sin puntos, correo único |
| HU-02 Inicio y cierre de sesión | 1 | ✅ Terminada | (existente) |
| HU-03 Recuperar contraseña | 3 | ✅ Terminada | Enlace de un solo uso por correo; 4 pantallas nuevas |
| HU-04 Editar perfil y clave | 1 | ✅ Terminada | (existente) |
| HU-05 Configuración tributaria y meta | 5 | ✅ Terminada | Régimen, IVA, honorarios, meta con barra de avance |
| HU-06 Colaboradores con roles | 8 | ✅ Terminada | Invitación, aceptación, selector de negocio, lector/editor, revocación |
| HU-07 Exportar y eliminar datos | 3 | ✅ Terminada | Descarga JSON; eliminación con contraseña |
| **Total** | **24** | **24 / 24** | |

## Cambios técnicos

- `accounts/models.py`: `validar_rut`, campos de configuración, modelo `Colaboracion`.
- `accounts/negocio.py`: `NegocioActivoMiddleware` (`request.negocio`, `request.rol_negocio`) y decorador `requiere_edicion`.
- `finances`, `taxes`, `projections`: todas las consultas pasan de `request.user` a `request.negocio`.
- Migración `accounts/0002_configuracion_y_colaboradores`.
- Correo configurable (`EMAIL_*`); en desarrollo se imprime en la consola.
- 21 pruebas nuevas en `accounts/tests.py` (45 en total).

## Revisión del sprint

> Completar en la reunión de revisión con el aprobador.

- Fecha: ____ · Asistentes: ____
- Demostración: registro con RUT inválido → configuración → invitar contador → aceptar en otra cuenta → modo lectura → revocar → exportar → eliminar.
- [ ] Aprobado por Danilo

## Retrospectiva

> Completar con el equipo.

| Qué funcionó | Qué mejorar | Acción para el Sprint 2 |
|---|---|---|
| | | |

## Deuda técnica detectada

- RF-13 (límite de plan) sin prueba dedicada.
- El envío real de correos requiere configurar SES (actividad 6.1, en producción).
- Si una persona necesita varios negocios propios, habrá que introducir la entidad `Negocio` (ver [modelo de datos](09_modelo_de_datos.md)).
