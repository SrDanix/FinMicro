# Modelo de datos

**Actividad 3.4** · Responsable: Marcelo · Aprueba: Danilo · Semana 7

Refleja los modelos implementados en el repositorio al cierre del Sprint 1. Las
entidades de sprints futuros aparecen al final como propuesta.

```mermaid
erDiagram
    USUARIO ||--o{ MOVIMIENTO : "registra (negocio)"
    USUARIO ||--o{ CATEGORIA : "crea (propias)"
    USUARIO ||--o{ SUSCRIPCION : "tiene"
    USUARIO ||--o{ COLABORACION : "otorga (propietario)"
    USUARIO |o--o{ COLABORACION : "recibe (colaborador)"
    PLAN ||--o{ SUSCRIPCION : "define"
    CATEGORIA ||--o{ MOVIMIENTO : "clasifica"

    USUARIO {
        bigint id PK
        varchar username UK
        varchar email
        varchar rut UK "12345678-9, DV validado"
        varchar nombre_negocio
        char tipo_negocio "FL CO GA SE AR OT"
        varchar telefono
        varchar comuna
        char regimen_tributario "SI PP PT RP RG"
        bool afecto_iva
        bool emite_boletas_honorarios
        int meta_ventas_mensual "nullable"
        datetime fecha_registro
    }
    COLABORACION {
        bigint id PK
        bigint propietario_id FK
        bigint colaborador_id FK "null hasta aceptar"
        varchar email "UK con propietario"
        varchar rol "lector | editor"
        varchar estado "pendiente | aceptada"
        uuid token UK
        datetime creada_en
    }
    PLAN {
        bigint id PK
        varchar codigo UK "basico | premium"
        varchar nombre
        int precio_mensual_clp
        bool con_publicidad
        int limite_movimientos_mensuales "null = ilimitado"
        bool incluye_proyecciones
        bool incluye_evaluador_viabilidad
        text descripcion
        bool activo
    }
    SUSCRIPCION {
        bigint id PK
        bigint usuario_id FK
        bigint plan_id FK "PROTECT"
        varchar estado "pendiente activa cancelada vencida"
        varchar metodo_pago "ninguno khipu flow"
        varchar referencia_pago
        datetime fecha_inicio
        datetime fecha_fin
        datetime creada_en
    }
    CATEGORIA {
        bigint id PK
        varchar nombre
        varchar tipo "ingreso | gasto"
        bigint usuario_id FK "null = del sistema"
        bool es_gravable_iva
    }
    MOVIMIENTO {
        bigint id PK
        bigint usuario_id FK "dueño del negocio"
        bigint categoria_id FK "PROTECT"
        varchar tipo "= categoria.tipo"
        decimal monto "12,2 · mínimo 1"
        date fecha
        varchar descripcion
        datetime creado_en
    }
```

## Restricciones e índices

| Tabla | Restricción | Motivo |
|---|---|---|
| Usuario | `rut` único, `username` único | Un RUT = un negocio (RN-01) |
| Colaboracion | único (`propietario`, `email`) | No duplicar invitaciones |
| Colaboracion | `token` único (UUID4) | Enlace de invitación no adivinable |
| Categoria | único (`nombre`, `tipo`, `usuario`) | Sin categorías repetidas por negocio |
| Movimiento | índice (`usuario`, `fecha`) | Consultas por mes del panel y los filtros |
| Movimiento → Categoria | `PROTECT` | No se borra una categoría con movimientos |
| Suscripcion → Plan | `PROTECT` | No se borra un plan con historial |

## Decisiones

- **El negocio es el usuario dueño.** No existe una tabla `Negocio` separada: en el MVP un usuario tiene un solo negocio. Los colaboradores acceden mediante `Colaboracion` y sus registros quedan a nombre del dueño. Si se requiere que una persona tenga varios negocios propios, se introduce `Negocio` y se migra `usuario_id` → `negocio_id` (cambio acotado gracias a `request.negocio`).
- **`Movimiento.tipo` se duplica desde la categoría** para filtrar sin JOIN; la consistencia se garantiza en `clean()` (RN-07).
- **Montos en `DECIMAL`**, nunca en coma flotante.

## Entidades propuestas para sprints futuros

| Sprint | Entidad | Campos principales |
|---|---|---|
| 2 | `Producto` | negocio, nombre, precio, afecto_iva, activo |
| 2 | `Movimiento` + | producto (FK opcional), cantidad |
| 3 | `Categoria` + | naturaleza (fijo / variable) |
| 4 | `TasaTributaria` | impuesto, año, tasa, vigente_desde |
| 4 | `Alerta` | negocio, tipo, mensaje, fecha, leída |
| 5 | `Consentimiento` | usuario, documento, versión, fecha, IP |
| 5 | `RegistroAuditoria` | usuario, acción, objeto, fecha, IP |
