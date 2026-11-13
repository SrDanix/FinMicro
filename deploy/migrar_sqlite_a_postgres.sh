#!/usr/bin/env bash
# =====================================================================
# X-05 · Migración de datos de SQLite a PostgreSQL con verificación.
#
# Lee la base SQLite indicada en SQLITE_PATH y la copia a la base
# PostgreSQL indicada por DB_NAME, DB_USER, DB_PASSWORD, DB_HOST y
# DB_PORT (la misma configuración del .env, pero sin DB_ENGINE activo).
# Ejecutar con la aplicación detenida, para que nadie escriba durante
# la copia. En el servidor, ver docs/19_operacion.md.
#
#   SQLITE_PATH=db.sqlite3 DB_NAME=finmicro DB_USER=finmicro \
#   DB_PASSWORD=... DB_HOST=localhost bash deploy/migrar_sqlite_a_postgres.sh
# =====================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

: "${SQLITE_PATH:?Indica SQLITE_PATH (la base SQLite de origen)}"
: "${DB_NAME:?Indica DB_NAME (la base PostgreSQL de destino)}"
SALIDA="${SALIDA:-respaldos}"
mkdir -p "$SALIDA"
SELLO="$(date +%Y%m%d_%H%M%S)"
DATOS="$SALIDA/migracion_${SELLO}.json"

origen() { env DB_ENGINE= python manage.py "$@"; }
destino() { env DB_ENGINE=postgresql python manage.py "$@"; }

CONTAR='
from django.apps import apps
for m in sorted(apps.get_models(), key=lambda m: m._meta.label):
    if m._meta.label not in ("contenttypes.ContentType", "auth.Permission", "sessions.Session", "admin.LogEntry"):
        print(m._meta.label, m.objects.count())'

echo "1/5 Exportando $SQLITE_PATH -> $DATOS"
# Tipos de contenido, permisos y sesiones los recrea PostgreSQL al migrar.
origen dumpdata --natural-foreign --exclude contenttypes --exclude auth.permission \
  --exclude sessions --exclude admin.logentry --indent 1 --output "$DATOS"
origen shell --no-imports -c "$CONTAR" > "$SALIDA/conteo_sqlite_${SELLO}.txt"

echo "2/5 Creando el esquema en PostgreSQL ($DB_NAME)"
destino migrate --noinput -v 0

echo "3/5 Cargando los datos"
destino loaddata "$DATOS"

echo "4/5 Comparando conteos"
destino shell --no-imports -c "$CONTAR" > "$SALIDA/conteo_postgres_${SELLO}.txt"
if ! diff "$SALIDA/conteo_sqlite_${SELLO}.txt" "$SALIDA/conteo_postgres_${SELLO}.txt"; then
  echo "ERROR: los conteos no coinciden. No cambies DB_ENGINE todavía." >&2
  exit 1
fi
cat "$SALIDA/conteo_postgres_${SELLO}.txt"

echo "5/5 Verificación de Django sobre PostgreSQL"
destino check -v 0
echo "OK: migración verificada. Guarda $SALIDA/ como evidencia y luego define DB_ENGINE=postgresql en .env."
