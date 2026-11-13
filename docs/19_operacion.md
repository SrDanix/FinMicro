# Operación: base de datos, respaldos, tareas programadas, monitoreo y pruebas de calidad

**Actividades X-04, X-05, X-08, X-09, X-10 y X-11 de la carta Gantt** · Complementa
[11_infraestructura.md](11_infraestructura.md), [17_base_de_datos_aws.md](17_base_de_datos_aws.md)
y [18_despliegue_aws_academy.md](18_despliegue_aws_academy.md).

Cada sección indica qué quedó en el repositorio, qué se verificó y qué falta hacer en AWS.

---

## X-04 · PostgreSQL

| Dónde | Archivo | Estado |
|---|---|---|
| Desarrollo | `docker-compose.yml` (PostgreSQL 17 + app) | Listo |
| CI | `.github/workflows/ci.yml`: las pruebas corren en SQLite **y** PostgreSQL 17 | Listo |
| EC2 (opción B, sin costo extra) | `docker-compose.postgres.yml`, se suma a `docker-compose.prod.yml` | Listo, por activar en el servidor |
| Amazon RDS (opción A) | [17_base_de_datos_aws.md](17_base_de_datos_aws.md) | Guía lista; decisión de costo pendiente |

Para usar PostgreSQL en la misma EC2, en el `.env` del servidor:

```ini
DB_ENGINE=postgresql
DB_HOST=db
DB_NAME=finmicro
DB_USER=finmicro
DB_PASSWORD=una-clave-larga-generada-con-secrets.token_urlsafe
```

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.postgres.yml up -d --build
```

Primero hay que migrar los datos (siguiente sección).

## X-05 · Migración de SQLite a PostgreSQL

Script: [`deploy/migrar_sqlite_a_postgres.sh`](../deploy/migrar_sqlite_a_postgres.sh). Exporta la base
SQLite, crea el esquema en PostgreSQL, carga los datos, **compara los conteos de cada tabla** y corre
`manage.py check` sobre PostgreSQL. Si los conteos no coinciden, se detiene sin tocar la configuración.

En el servidor (con la app detenida y PostgreSQL ya levantado):

```bash
cd ~/FinMicro
docker compose -f docker-compose.prod.yml stop web
docker compose -f docker-compose.prod.yml -f docker-compose.postgres.yml up -d db
docker compose -f docker-compose.prod.yml -f docker-compose.postgres.yml run --rm \
  -e SQLITE_PATH=/app/data/db.sqlite3 -e SALIDA=/app/data/migracion web \
  bash deploy/migrar_sqlite_a_postgres.sh
# Si termina en "OK", poner DB_ENGINE=postgresql en .env y levantar todo:
docker compose -f docker-compose.prod.yml -f docker-compose.postgres.yml up -d --build
```

**Evidencia (13-11-2026, base de desarrollo → PostgreSQL 16 local):** 116 objetos copiados, conteos
idénticos en las 15 tablas (4 usuarios, 58 movimientos, 10 categorías, 3 suscripciones, 5 tasas,
32 feriados, 2 documentos legales…) y `check` sin observaciones. Después de la carga se creó un
movimiento nuevo sin choque de identificadores (las secuencias quedan ajustadas).

## X-08 · Respaldos y prueba de restauración (RNF-09: RPO 24 h, RTO 4 h)

| Script | Qué hace |
|---|---|
| [`deploy/respaldar.sh`](../deploy/respaldar.sh) | SQLite: copia en caliente con la API de respaldo de SQLite + `integrity_check` + gzip. PostgreSQL: `pg_dump` formato custom + verificación con `pg_restore --list`. Sube a S3 si `S3_BUCKET` está definido y conserva 14 días locales. |
| [`deploy/probar_restauracion.sh`](../deploy/probar_restauracion.sh) | Restaura el último respaldo en una copia temporal (nunca sobre la base en uso), verifica integridad, cuenta registros y mide el tiempo. |

**Evidencia (13-11-2026):**

| Motor | Respaldo | Restauración |
|---|---|---|
| SQLite | 20 KB comprimido, `integrity_check: ok` | 4 usuarios, 58 movimientos, 10 categorías, 3 suscripciones · 0 s |
| PostgreSQL | 80 KB (`.dump`), legible con `pg_restore --list` | mismos conteos · 0 s |

Con una base de este tamaño el RTO real lo domina el tiempo de levantar la instancia, no la restauración.

**Pendiente en AWS:** crear el bucket (bloqueo de acceso público, cifrado y regla de ciclo de vida de 30 días)
y dar permiso de escritura a la instancia. En el Learner Lab se usa el perfil de instancia
**LabInstanceProfile** (EC2 → Actions → Security → Modify IAM role) y se instala la CLI con
`sudo snap install aws-cli --classic`. Sin bucket, los respaldos quedan solo en `/var/backups/finmicro`
de la misma EC2: sirven ante un error humano, no ante la pérdida de la instancia. Complementar con un
snapshot del volumen EBS (guía 18, "Uso diario").

```bash
aws s3api create-bucket --bucket finmicro-respaldos-CAMBIAR --region us-east-1
aws s3api put-public-access-block --bucket finmicro-respaldos-CAMBIAR \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-lifecycle-configuration --bucket finmicro-respaldos-CAMBIAR \
  --lifecycle-configuration '{"Rules":[{"ID":"retener-30-dias","Status":"Enabled","Filter":{"Prefix":"diario/"},"Expiration":{"Days":30}}]}'
echo "S3_BUCKET=finmicro-respaldos-CAMBIAR" >> .env
```

## Tareas programadas (cron)

[`deploy/crontab.txt`](../deploy/crontab.txt): respaldo diario, prueba de restauración mensual,
alertas de vencimientos (RF-24) y renovación de suscripciones (RF-28). Instalar con
`sudo crontab deploy/crontab.txt` después de revisar la ruta del proyecto. En el Learner Lab la
instancia se apaga al terminar la sesión: las tareas corren solo mientras el laboratorio está
encendido (el panel también actualiza las alertas de vencimiento al abrirse).

## X-09 · Presupuesto, monitoreo y correo

| Servicio | Cuenta AWS normal | Learner Lab |
|---|---|---|
| **AWS Budgets** | USD 15/mes con avisos al 50 %, 80 % y 100 % proyectado: `deploy/aws/presupuesto.json` y `alertas.json` (doc 11) | No disponible: el laboratorio controla su propio crédito (panel del lab) |
| **CloudWatch** | Alarmas de CPU > 80 % (3 × 5 min) y `StatusCheckFailed` con aviso por SNS (comandos abajo) | Mismo procedimiento si el lab lo permite; si no, revisar las métricas en la pestaña Monitoring de la instancia |
| **SES** | Verificar dominio (DKIM), crear credenciales SMTP, pedir salida del sandbox | Queda en sandbox: solo envía a correos verificados. Para el curso, verificar los correos del equipo |

```bash
aws sns create-topic --name finmicro-alertas
aws sns subscribe --topic-arn ARN_DEL_TEMA --protocol email --notification-endpoint equipo@CAMBIAR.cl
aws cloudwatch put-metric-alarm --alarm-name finmicro-cpu-alta --namespace AWS/EC2 \
  --metric-name CPUUtilization --statistic Average --dimensions Name=InstanceId,Value=i-CAMBIAR \
  --period 300 --evaluation-periods 3 --threshold 80 --comparison-operator GreaterThanThreshold \
  --alarm-actions ARN_DEL_TEMA
aws cloudwatch put-metric-alarm --alarm-name finmicro-instancia-caida --namespace AWS/EC2 \
  --metric-name StatusCheckFailed --statistic Maximum --dimensions Name=InstanceId,Value=i-CAMBIAR \
  --period 60 --evaluation-periods 2 --threshold 1 --comparison-operator GreaterThanOrEqualToThreshold \
  --alarm-actions ARN_DEL_TEMA
```

Correo con SES en `.env`: `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`,
`EMAIL_HOST=email-smtp.us-east-1.amazonaws.com` y las credenciales SMTP. Probar con
`docker compose -f docker-compose.prod.yml exec web python manage.py sendtestemail correo@verificado.cl`.

## X-10 · Calidad en la CI

Job **Calidad** de `.github/workflows/ci.yml` (bloquea la integración si falla):

| Verificación | Herramienta | Resultado al 13-11-2026 |
|---|---|---|
| Análisis estático | `ruff check .` (`ruff.toml`) | Sin hallazgos |
| Riesgos de seguridad en el código | `bandit -ll` (severidad media o alta) | 0 medios, 0 altos |
| Dependencias vulnerables (RNF-05) | `pip-audit` | Django 6.0.7 tenía 3 avisos (PYSEC-2026-3717, PYSEC-2026-4035) → se subió a **6.0.8**; hoy 0 |
| Cobertura total (umbral 85 %) | `coverage` (`.coveragerc`) | **90 %** (140 pruebas) |
| Cobertura de módulos de cálculo (umbral 90 %) | servicios de finanzas, impuestos, calendario, proyecciones, alertas y recomendaciones | **97 %** |

## X-11 · Pruebas de carga, seguridad y accesibilidad

### Carga (RNF-07: p95 < 800 ms con 50 usuarios)

Escenario: [`deploy/carga/locustfile.py`](../deploy/carga/locustfile.py). 50 usuarios que inician sesión
y recorren panel, movimientos, búsqueda, indicadores, impuestos y proyección, registrando gastos.
Gunicorn con 3 workers, `DEBUG=False`, SQLite, 90 segundos.

| Ruta | Solicitudes | p50 | p95 |
|---|---|---|---|
| `/finanzas/` (panel) | 728 | 20 ms | 250 ms |
| `/finanzas/indicadores/` | 259 | 43 ms | 72 ms |
| `/finanzas/movimientos/` | 433 | 26 ms | 42 ms |
| búsqueda por texto | 298 | 15 ms | 22 ms |
| `/impuestos/` | 155 | 14 ms | 27 ms |
| registrar movimiento (POST) | 126 | 32 ms | 48 ms |
| inicio de sesión (POST) | 50 | 1.300 ms | 2.600 ms |
| **Total** | **2.384, 0 errores** | **22 ms** | **670 ms** ✅ |

El inicio de sesión es lento a propósito: las contraseñas usan PBKDF2 (RNF-01), y la prueba hace entrar
a los 50 usuarios en los primeros 5 segundos. Las pantallas de uso diario quedan muy por debajo del umbral.

⚠️ Se midió en el contenedor de desarrollo (4 vCPU). **Hay que repetirla contra la EC2** (`t3.small`,
2 vCPU) para dar el RNF por cumplido en producción:

```bash
python manage.py crear_usuarios_prueba --password "ClaveDeCarga.2026"   # en el servidor
pip install locust                                                       # en tu PC
locust -f deploy/carga/locustfile.py --host https://TU_DOMINIO --headless -u 50 -r 10 -t 2m --csv resultados
```

### Accesibilidad (RNF-12: WCAG 2.1 AA)

Revisión automática con **axe-core 4.10** sobre 21 pantallas (4 públicas y 17 con sesión), en escritorio
y a 375 px:

- Hallazgos iniciales: enlaces dentro de párrafos que se distinguían solo por el color (6 pantallas) y una
  tabla desplazable sin acceso por teclado. Corregidos en `static/css/styles.css` y `templates/base.html`.
- Resultado final: **0 violaciones WCAG 2.1 A/AA**. Ninguna pantalla se desborda a 375 px (RNF-11).

La revisión automática no reemplaza una revisión manual con lector de pantalla ni Lighthouse en el
navegador; queda como parte de la prueba de usabilidad (X-03).

### Seguridad

Además de `bandit` y `pip-audit` en la CI y `check --deploy`, en esta etapa se corrigió:

- **Webhook de pagos (RF-27):** antes, un aviso a `/suscripcion/webhook/flow/` con `{"status": 2}` activaba
  Premium sin verificar nada. Ahora el estado se consulta a la pasarela con las credenciales del comercio y
  se validan orden y monto.
- **Redirecciones abiertas:** los parámetros `siguiente` y `next` solo aceptan rutas del propio sitio.
- **Aislamiento entre negocios (RNF-03):** pruebas automatizadas para productos, alertas, importación,
  exportación y el asistente.

Pendiente fuera del repositorio: un escaneo dinámico (por ejemplo OWASP ZAP baseline) contra la EC2 cuando
tenga HTTPS.
