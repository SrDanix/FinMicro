# Base de datos en AWS (PostgreSQL)

Complementa las actividades **3.4** (modelo de datos), **6.1** (ambientes) y **6.2**
(respaldos), y adelanta la etapa **E1** del [plan de escalamiento](08_plan_escalamiento.md).

## ¿Por qué cambiar SQLite por PostgreSQL?

| | SQLite (hoy) | PostgreSQL |
|---|---|---|
| Qué es | Un archivo en el disco del servidor | Un servidor de base de datos |
| Escrituras simultáneas | Una a la vez (error `database is locked` con carga) | Muchas a la vez |
| Si se pierde la instancia EC2 | Se pierde la base, salvo el último respaldo | Con RDS, la base vive aparte y sobrevive |
| Respaldos | Hay que programarlos (copiar el archivo) | RDS los hace solo, con restauración a un punto en el tiempo |
| Ideal para | Desarrollo y piloto pequeño | Producción con usuarios reales |

**El código ya funciona con ambas.** Se elige con variables de entorno, sin tocar Python:

```env
# SQLite (por defecto): no definir DB_ENGINE
# PostgreSQL:
DB_ENGINE=postgresql
DB_HOST=finmicro-db.abc123xyz.sa-east-1.rds.amazonaws.com
DB_NAME=finmicro
DB_USER=finmicro_app
DB_PASSWORD=una-clave-larga-y-aleatoria
DB_SSLMODE=require
```

La CI corre todas las pruebas en SQLite **y** en PostgreSQL 17 para garantizar que el
código funcione en ambas.

## Dos formas de tener PostgreSQL en AWS

| | **Opción A — Amazon RDS** (recomendada) | **Opción B — PostgreSQL en la misma EC2** |
|---|---|---|
| Quién lo administra | AWS: parches, respaldos, monitoreo | El equipo |
| Respaldos | Automáticos, 7 días, restauración a cualquier minuto | Script propio (`pg_dump` → S3) |
| Si se cae la EC2 | La base sigue intacta | Se cae todo |
| Costo | Instancia aparte (`db.t4g.micro`). Cubierta por la capa/plan gratuito mientras dure; **después suma un costo mensual** que probablemente supera el presupuesto de USD 15 (RNF-16) | Sin costo adicional |
| Cuándo | Antes del piloto (actividad 6.3) o al cumplir un disparador E0→E1 | Si el presupuesto no alcanza para RDS |

> **Decisión del equipo (Danilo, aprueba Carlos):** RDS cambia el costo comprometido en
> el informe. Antes de crearla, verifiquen en la [calculadora de AWS](https://calculator.aws/)
> el precio de `db.t4g.micro` en `sa-east-1` y qué cubre el plan de su cuenta (actividad 6.0).

## Opción A paso a paso: crear la base en Amazon RDS

> Requiere acceso a la consola de AWS. Haz todo en la **misma región** que la instancia
> EC2 (recomendado: `sa-east-1`, São Paulo).

### 1. Crear la base de datos

En la consola: **RDS → Databases → Create database**.

| Opción | Valor | Por qué |
|---|---|---|
| Creation method | Standard create | Para ver todas las opciones |
| Engine | **PostgreSQL**, versión 17 | La misma que usa la CI |
| Templates | **Free tier** (si aparece) o *Dev/Test* | Limita las opciones a las de bajo costo |
| DB instance identifier | `finmicro-db` | Nombre del servidor |
| Master username | `finmicro_admin` | Usuario administrador (no lo usa la app) |
| Credentials management | Self managed → **Auto generate password** | Guárdala en un gestor de contraseñas; se muestra **una sola vez** |
| Instance class | `db.t4g.micro` | La más pequeña |
| Storage | gp3, 20 GB, **desactivar** *storage autoscaling* | Evita crecer (y cobrar) sin aviso |
| Availability | Single-AZ | Multi-AZ duplica el costo; es de la etapa E2 |
| Compute resource | **Connect to an EC2 compute resource** → elegir la instancia de FinMicro | AWS crea solo los *security groups* para que **solo** la EC2 llegue a la base |
| Public access | **No** | La base no queda expuesta a internet |
| Database authentication | Password authentication | |
| Monitoring | Desactivar *Enhanced monitoring* | Tiene costo; CloudWatch básico basta |
| Initial database name *(en Additional configuration)* | `finmicro` | Si se deja vacío, no se crea la base |
| Backup retention | 7 días | Cumple el RPO de 24 h (RNF-09) |
| Encryption | Activado | Datos cifrados en disco |
| Deletion protection | **Activado** | Impide borrarla por error |

Clic en **Create database**. Tarda unos 10 minutos. Al terminar, copia el **Endpoint**
(pestaña *Connectivity & security*), algo como
`finmicro-db.abc123xyz.sa-east-1.rds.amazonaws.com`.

### 2. Crear un usuario solo para la aplicación

Buena práctica: la app no usa el usuario administrador. Desde la instancia EC2:

```bash
sudo apt-get install -y postgresql-client
psql "host=ENDPOINT_DE_RDS port=5432 dbname=finmicro user=finmicro_admin sslmode=require"
```

Dentro de `psql` (cambia la clave por una larga y aleatoria):

```sql
CREATE USER finmicro_app WITH PASSWORD 'CAMBIA-ESTA-CLAVE';
ALTER DATABASE finmicro OWNER TO finmicro_app;
\q
```

### 3. Configurar la aplicación

En el archivo `.env` de la instancia EC2 (nunca en el repositorio):

```env
DB_ENGINE=postgresql
DB_HOST=finmicro-db.abc123xyz.sa-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=finmicro
DB_USER=finmicro_app
DB_PASSWORD=CAMBIA-ESTA-CLAVE
DB_SSLMODE=require
```

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Al arrancar, el contenedor ejecuta `migrate`: crea las tablas, los planes y las
categorías del sistema.

### 4. Verificar

```bash
# Tablas creadas y conexión cifrada
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations
docker compose -f docker-compose.prod.yml exec web python manage.py dbshell
```

Dentro de `dbshell`:

```sql
SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid();   -- debe decir t (true)
SELECT codigo, precio_mensual_clp FROM subscriptions_plan;   -- basico y premium
\q
```

### 5. (Si ya había datos en SQLite) migrarlos a PostgreSQL

```bash
# a) Con la app todavía en SQLite: exportar
docker compose -f docker-compose.prod.yml exec web python manage.py dumpdata \
  --natural-foreign --natural-primary \
  --exclude contenttypes --exclude auth.permission --exclude sessions \
  --indent 2 -o /app/data/respaldo.json
docker compose -f docker-compose.prod.yml cp web:/app/data/respaldo.json ./respaldo.json

# b) Cambiar el .env a PostgreSQL (paso 3) y reiniciar; migrate crea las tablas.

# c) Vaciar los datos iniciales y cargar el respaldo
docker compose -f docker-compose.prod.yml cp ./respaldo.json web:/app/data/respaldo.json
docker compose -f docker-compose.prod.yml exec web python manage.py flush --no-input
docker compose -f docker-compose.prod.yml exec web python manage.py loaddata /app/data/respaldo.json
```

Probar primero en una copia. `respaldo.json` contiene datos personales: bórralo del
servidor cuando termines.

## Seguridad: resumen de lo que protege cada paso

| Medida | Qué evita |
|---|---|
| *Public access: No* + security group solo desde la EC2 | Que alguien en internet intente conectarse a la base |
| `DB_SSLMODE=require` | Que los datos viajen sin cifrar entre la EC2 y RDS |
| Usuario `finmicro_app` distinto del administrador | Que una falla en la app dé control total del servidor de base de datos |
| Contraseñas solo en `.env` (ignorado por Git) | Que una clave termine publicada en GitHub |
| Cifrado en disco + respaldos de 7 días | Pérdida o robo de datos (Ley 19.628 / 21.719) |
| *Deletion protection* | Borrar la base de producción por error |

## Desarrollo local con PostgreSQL

`docker compose up --build` ahora levanta dos contenedores: `db` (PostgreSQL 17) y `web`.
Así se desarrolla con el mismo motor que en producción. Sin Docker, todo sigue
funcionando con SQLite (`python manage.py runserver`).
