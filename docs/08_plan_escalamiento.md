# Plan de escalamiento de la arquitectura

**Actividad 3.7** · Responsable: Danilo · Aprueba: Carlos · Semana 8

La arquitectura MVP (una instancia EC2, SQLite, Docker) es suficiente para el piloto.
Este plan define **cuándo** y **cómo** crecer, con disparadores medibles, para no
sobredimensionar antes de tiempo ni reaccionar tarde.

## Etapas

| Etapa | Usuarios activos | Arquitectura | Costo aprox. mensual |
|---|---|---|---|
| **E0 — MVP / piloto** | hasta ~200 | 1 EC2 (t3.micro/small) + Docker + SQLite en volumen + respaldo diario a S3 | ≤ USD 15 |
| **E1 — Base de datos gestionada** | ~200 a ~2.000 | 1 EC2 + **Amazon RDS PostgreSQL** (db.t4g.micro) + caché Redis en la misma instancia | USD 30–50 |
| **E2 — Alta disponibilidad** | ~2.000 a ~20.000 | **Application Load Balancer** + 2 o más EC2 en un Auto Scaling Group en dos zonas + RDS Multi-AZ + ElastiCache Redis + estáticos en S3/CloudFront | USD 150–300 |
| **E3 — Servicios separados** | > 20.000 o equipo > 10 devs | Contenedores en ECS Fargate; tareas pesadas (reportes PDF, importaciones, asistente IA) en colas (SQS + workers); multi-tenant estricto por esquema si un cliente lo exige | según uso |

Las cifras de costo son referenciales y deben revisarse con la calculadora de AWS al
momento de cada cambio.

## Disparadores (cualquiera de ellos inicia el paso a la etapa siguiente)

| De → a | Disparador |
|---|---|
| E0 → E1 | Más de 5 errores `database is locked` por semana · tiempo p95 > 800 ms sostenido (RNF-07) · base de datos > 1 GB · necesidad de más de 1 contenedor web |
| E1 → E2 | CPU de la EC2 > 70 % sostenido en horario punta · el negocio comprometa disponibilidad > 99,5 % · primer cliente con contrato |
| E2 → E3 | Tareas largas que bloquean peticiones web · equipo que despliega más de una vez al día en módulos distintos |

## Qué ya está preparado en el código

- **Base de datos intercambiable:** `settings.py` usa PostgreSQL con solo definir `DB_ENGINE=postgresql` y los `DB_*` en el `.env`, con SSL y reutilización de conexiones. La CI prueba en SQLite y en PostgreSQL 17. Guía paso a paso de RDS y de la migración de datos: [17_base_de_datos_aws.md](17_base_de_datos_aws.md).
- **Aplicación sin estado local:** las sesiones están en la base de datos y los estáticos se generan en la imagen; se pueden levantar varias copias detrás de un balanceador (E2) sin cambios de código.
- **Caché centralizable:** `CACHES` usa memoria local; en E1 se cambia a Redis (`django-redis`) para compartirla entre workers.
- **Cálculos aislados en `services.py`:** se pueden mover a workers asíncronos (E3) sin reescribirlos.
- **Aislación por negocio (`request.negocio`):** el multi-tenant lógico actual escala hasta E2; un esquema por cliente (django-tenants) solo si un cliente corporativo lo exige.

## Riesgos de quedarse en E0 demasiado tiempo

| Riesgo | Mitigación en E0 |
|---|---|
| Pérdida de datos si falla el disco de la instancia | Respaldo diario a S3 con restauración probada (actividad 6.2) |
| Caída total si se cae la instancia (punto único de falla) | Imagen Docker + script de endurecimiento: reconstruir una instancia toma menos de 1 hora (RTO 4 h, RNF-09) |
| Fin del plan gratuito de AWS | Presupuesto con alertas (actividad 6.0) y revisión mensual de costos |
